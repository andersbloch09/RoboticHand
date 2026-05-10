"""PyQt5 GUI for creating and composing robotic hand motions with live preview."""

import sys
import os

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QSlider, QLabel, QPushButton, QSpinBox, QDoubleSpinBox,
        QComboBox, QListWidget, QListWidgetItem, QDialog, QLineEdit,
        QCheckBox, QMessageBox, QGroupBox, QFormLayout, QScrollArea
    )
    from PyQt5.QtCore import Qt, QTimer
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    print("[ERROR] PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)

from motion_editor_lib import MotionLibrary, CalibrationLoader, MotionMetadata
from motion import Motion


class KeyframeEditor(QWidget):
    """Tab for creating individual keyframes."""
    
    def __init__(self, hand, calibration):
        super().__init__()
        self.hand = hand
        self.calibration = calibration or {}
        self.current_keyframe_index = 0
        self.keyframes = [(0.0, {})]
        self.digit_sliders = {}
        self.digit_position_labels = {}
        self.torque_limits = {}  # {digit_name: torque_nm}
        self.torque_spinboxes = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Keyframe timeline
        timeline_group = QGroupBox("Keyframe Timeline")
        timeline_layout = QHBoxLayout()
        
        self.keyframe_list = QListWidget()
        self.keyframe_list.itemSelectionChanged.connect(self.on_keyframe_selected)
        timeline_layout.addWidget(QLabel("Keyframes:"))
        timeline_layout.addWidget(self.keyframe_list, 1)
        
        timeline_btn_layout = QVBoxLayout()
        add_kf_btn = QPushButton("Add")
        add_kf_btn.clicked.connect(self.add_keyframe)
        delete_kf_btn = QPushButton("Delete")
        delete_kf_btn.clicked.connect(self.delete_keyframe)
        timeline_btn_layout.addWidget(add_kf_btn)
        timeline_btn_layout.addWidget(delete_kf_btn)
        timeline_layout.addLayout(timeline_btn_layout)
        
        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)
        
        # Position sliders
        sliders_group = QGroupBox("Joint Positions (0=Open, 1=Closed)")
        sliders_layout = QVBoxLayout()
        
        digit_names = ["finger_0", "finger_1", "finger_2", "finger_3",
                       "thumb_flexion", "thumb_abduction", "index_abduction"]
        
        for digit_name in digit_names:
            h_layout = QHBoxLayout()
            
            label = QLabel(digit_name)
            label.setMinimumWidth(120)
            h_layout.addWidget(label)
            
            # Position slider
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(0)
            slider.setTickInterval(10)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.valueChanged.connect(
                lambda val, dn=digit_name: self.on_slider_changed(dn, val)
            )
            self.digit_sliders[digit_name] = slider
            h_layout.addWidget(slider, 1)
            
            pos_label = QLabel("0.00")
            pos_label.setMinimumWidth(50)
            self.digit_position_labels[digit_name] = pos_label
            h_layout.addWidget(pos_label)
            
            # Torque limit spinbox
            h_layout.addWidget(QLabel("T:"))
            torque_spinbox = QDoubleSpinBox()
            torque_spinbox.setMinimum(0.0)
            torque_spinbox.setMaximum(0.5)
            torque_spinbox.setSingleStep(0.05)
            torque_spinbox.setValue(0.25)
            torque_spinbox.setMinimumWidth(60)
            torque_spinbox.setSuffix(" Nm")
            torque_spinbox.valueChanged.connect(
                lambda val, dn=digit_name: self.on_torque_changed(dn, val)
            )
            self.torque_limits[digit_name] = 0.25
            self.torque_spinboxes[digit_name] = torque_spinbox
            h_layout.addWidget(torque_spinbox)
            
            sliders_layout.addLayout(h_layout)
        
        sliders_group.setLayout(sliders_layout)
        layout.addWidget(sliders_group)
        
        # Keyframe time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Keyframe Time (s):"))
        self.time_spinbox = QDoubleSpinBox()
        self.time_spinbox.setMinimum(0.0)
        self.time_spinbox.setMaximum(60.0)
        self.time_spinbox.setSingleStep(0.1)
        self.time_spinbox.valueChanged.connect(self.on_time_changed)
        time_layout.addWidget(self.time_spinbox)
        layout.addLayout(time_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        update_btn = QPushButton("Update Keyframe Position")
        update_btn.clicked.connect(self.update_keyframe_position)
        button_layout.addWidget(update_btn)
        
        preview_btn = QPushButton("Preview on Gripper")
        preview_btn.clicked.connect(self.preview_on_gripper)
        button_layout.addWidget(preview_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.refresh_keyframe_list()
    
    def on_slider_changed(self, digit_name, value):
        """Update label when slider moves."""
        normalized = value / 100.0
        self.digit_position_labels[digit_name].setText(f"{normalized:.2f}")

    def on_torque_changed(self, digit_name, value):
        """Update stored torque limit for a digit."""
        try:
            # store as float (Nm)
            self.torque_limits[digit_name] = float(value)
        except Exception:
            # ignore invalid inputs
            pass
    
    def on_time_changed(self, value):
        """Update keyframe time."""
        if 0 <= self.current_keyframe_index < len(self.keyframes):
            _, positions = self.keyframes[self.current_keyframe_index]
            self.keyframes[self.current_keyframe_index] = (value, positions)
            self.refresh_keyframe_list()
    
    def add_keyframe(self):
        """Add new keyframe."""
        last_time = self.keyframes[-1][0] if self.keyframes else 0.0
        # default keyframe format: (time, positions_dict, torques_dict)
        self.keyframes.append((last_time + 1.0, {}, {}))
        self.current_keyframe_index = len(self.keyframes) - 1
        self.refresh_keyframe_list()
    
    def delete_keyframe(self):
        """Delete current keyframe."""
        if len(self.keyframes) > 1 and self.current_keyframe_index < len(self.keyframes):
            self.keyframes.pop(self.current_keyframe_index)
            self.current_keyframe_index = min(self.current_keyframe_index, len(self.keyframes) - 1)
            self.refresh_keyframe_list()
    
    def on_keyframe_selected(self):
        """Load keyframe into sliders."""
        items = self.keyframe_list.selectedItems()
        if items:
            index = self.keyframe_list.row(items[0])
            self.current_keyframe_index = index
            
            time_val, positions = self.keyframes[index][0], self.keyframes[index][1]
            # support both (time, positions) and (time, positions, torques)
            torques = {}
            if len(self.keyframes[index]) > 2:
                torques = self.keyframes[index][2]
            self.time_spinbox.blockSignals(True)
            self.time_spinbox.setValue(time_val)
            self.time_spinbox.blockSignals(False)
            
            for digit_name, slider in self.digit_sliders.items():
                normalized = positions.get(digit_name, 0.0)
                value = int(normalized * 100)
                slider.blockSignals(True)
                slider.setValue(value)
                slider.blockSignals(False)
                self.digit_position_labels[digit_name].setText(f"{normalized:.2f}")
                # update torque spinbox display for this keyframe
                if digit_name in self.torque_spinboxes:
                    torque_val = torques.get(digit_name, self.torque_limits.get(digit_name, 0.25))
                    self.torque_spinboxes[digit_name].blockSignals(True)
                    self.torque_spinboxes[digit_name].setValue(torque_val)
                    self.torque_spinboxes[digit_name].blockSignals(False)
    
    def update_keyframe_position(self):
        """Save slider positions to keyframe."""
        if self.current_keyframe_index < len(self.keyframes):
            time_val = self.keyframes[self.current_keyframe_index][0]
            positions = {}
            torques = {}
            
            # Include ALL slider values, even if 0.0 (fully open)
            for digit_name, slider in self.digit_sliders.items():
                normalized = slider.value() / 100.0
                positions[digit_name] = normalized
                # read current torque spinbox value for this digit
                if digit_name in self.torque_spinboxes:
                    try:
                        torques[digit_name] = float(self.torque_spinboxes[digit_name].value())
                    except Exception:
                        torques[digit_name] = self.torque_limits.get(digit_name, 0.25)
            
            self.keyframes[self.current_keyframe_index] = (time_val, positions, torques)
            self.refresh_keyframe_list()
    
    def preview_on_gripper(self):
        """Apply keyframe to gripper."""
        if self.current_keyframe_index < len(self.keyframes):
            # support (time, positions) and (time, positions, torques)
            entry = self.keyframes[self.current_keyframe_index]
            if len(entry) > 2:
                _, positions, torques = entry
            else:
                _, positions = entry
                torques = {}

            # Setup motors with these torques
            self._setup_motors_for_preview(per_digit_torques=torques)

            for digit_name, norm_pos in positions.items():
                self._apply_position(digit_name, norm_pos)
    
    def _setup_motors_for_preview(self, per_digit_torques=None):
        """Set all motors to current-based position mode for safe preview."""
        torque = 0.25  # default torque limit for preview (can be overridden by per_digit_torques)
        try:
            # Set all finger motors
            for i in range(4):
                try:
                    motor = self.hand.fingers[f"finger_{i}"].motor
    
                    if per_digit_torques and f"finger_{i}" in per_digit_torques:
                        torque = per_digit_torques.get(f"finger_{i}", torque)
                    else:
                        torque = self.torque_limits.get(f"finger_{i}", torque)
                    motor.torque_disable()
                    motor.set_current_based_position_mode()
                    motor.set_torque_limit(torque)
                    motor.torque_enable()
                except Exception as e:
                    print(f"[ERROR] finger_{i} setup failed: {e}")
            
            # Set thumb motors
            try:
                if per_digit_torques and "thumb_flexion" in per_digit_torques:
                    torque = per_digit_torques.get("thumb_flexion", torque)
                else:
                    torque = self.torque_limits.get("thumb_flexion", torque)
                self.hand.thumb.flexion.motor.torque_disable()
                self.hand.thumb.flexion.motor.set_current_based_position_mode()
                self.hand.thumb.flexion.motor.set_torque_limit(torque)
                self.hand.thumb.flexion.motor.torque_enable()

                if per_digit_torques and "thumb_abduction" in per_digit_torques:
                    torque = per_digit_torques.get("thumb_abduction", torque)
                else:
                    torque = self.torque_limits.get("thumb_abduction", torque)

                self.hand.thumb.abduction.motor.torque_disable()
                self.hand.thumb.abduction.motor.set_current_based_position_mode()
                self.hand.thumb.abduction.motor.set_torque_limit(torque)
                self.hand.thumb.abduction.motor.torque_enable()
            except Exception as e:
                print(f"[ERROR] Thumb setup failed: {e}")
            
            # Set index abduction if present
            if self.hand.index_abduction:
                try:
                    if per_digit_torques and "index_abduction" in per_digit_torques:
                        torque = per_digit_torques.get("index_abduction", torque)
                    else:
                        torque = self.torque_limits.get("index_abduction", torque)
                    self.hand.index_abduction.motor.torque_disable()
                    self.hand.index_abduction.motor.set_current_based_position_mode()
                    self.hand.index_abduction.motor.set_torque_limit(torque)
                    self.hand.index_abduction.motor.torque_enable()
                except Exception as e:
                    print(f"[ERROR] Index abduction setup failed: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in motor setup: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_position(self, digit_name, normalized_pos):
        """Apply position to motor."""
        if digit_name not in self.calibration:
            return
        
        cal = self.calibration[digit_name]
        start = cal.get("start", 0)
        min_pos = cal.get("min", 0)
        
        motor = None
        try:
            if digit_name.startswith("finger_"):
                idx = int(digit_name.split("_")[1])
                if 0 <= idx < 4:
                    motor = self.hand.fingers[f"finger_{idx}"].motor
            elif digit_name == "thumb_flexion":
                motor = self.hand.thumb.flexion.motor
            elif digit_name == "thumb_abduction":
                motor = self.hand.thumb.abduction.motor
            elif digit_name == "index_abduction" and self.hand.index_abduction:
                motor = self.hand.index_abduction.motor
            
            if not motor:
                return
            
            # Calculate target position
            actual_pos = int(start + (min_pos - start) * normalized_pos)
            motor.set_position(actual_pos)
            
        except Exception as e:
            print(f"[ERROR] Failed to apply position to {digit_name}: {e}")
    
    def refresh_keyframe_list(self):
        """Refresh keyframe display."""
        self.keyframe_list.clear()
        for i, entry in enumerate(self.keyframes):
            # entry may be (time, positions) or (time, positions, torques) or dict
            if isinstance(entry, dict):
                time_val = entry.get("time", 0.0)
                positions = entry.get("positions", {})
            elif isinstance(entry, (list, tuple)):
                time_val = entry[0]
                positions = entry[1] if len(entry) > 1 else {}
            else:
                time_val = 0.0
                positions = {}
            item_text = f"Frame {i}: t={time_val:.1f}s, {len(positions)} pos"
            self.keyframe_list.addItem(item_text)
    
    def get_keyframes(self):
        """Get keyframes."""
        return self.keyframes
    
    def set_keyframes(self, keyframes):
        """Load keyframes."""
        # Normalize loaded keyframes into internal tuple form: (time, positions, torques)
        normalized = []
        for k in keyframes:
            if isinstance(k, dict):
                t = k.get("time", 0.0)
                pos = k.get("positions", {})
                tor = k.get("torques", {})
            elif isinstance(k, (list, tuple)):
                if len(k) == 2:
                    t, pos = k
                    tor = {}
                elif len(k) >= 3:
                    t, pos, tor = k[0], k[1], k[2]
                else:
                    continue
            else:
                continue
            normalized.append((t, pos or {}, tor or {}))

        self.keyframes = normalized
        self.refresh_keyframe_list()


class MotionSaver(QDialog):
    """Dialog for saving a motion."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.metadata = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog."""
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        layout.addRow("Motion Name:", self.name_input)
        
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setMinimum(0.1)
        self.duration_input.setMaximum(60.0)
        self.duration_input.setValue(1.0)
        layout.addRow("Duration (s):", self.duration_input)
        
        self.easing_combo = QComboBox()
        self.easing_combo.addItems([
            "linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad",
            "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic",
            "ease_in_sine", "ease_out_sine", "ease_in_out_sine",
        ])
        self.easing_combo.setCurrentText("ease_in_out_cubic")
        layout.addRow("Easing:", self.easing_combo)
        
        self.repeat_input = QSpinBox()
        self.repeat_input.setMinimum(1)
        self.repeat_input.setValue(1)
        layout.addRow("Repeat:", self.repeat_input)
        
        self.loop_input = QCheckBox("Loop Infinitely")
        layout.addRow("Loop:", self.loop_input)
        
        self.description_input = QLineEdit()
        layout.addRow("Description:", self.description_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
        self.setWindowTitle("Save Motion")
    
    def get_metadata(self):
        """Get metadata."""
        return MotionMetadata(
            name=self.name_input.text(),
            duration=self.duration_input.value(),
            easing=self.easing_combo.currentText(),
            repeat=self.repeat_input.value(),
            loop=self.loop_input.isChecked(),
            description=self.description_input.text(),
        )


class MotionEditorWindow(QMainWindow):
    """Main motion editor window."""
    
    DT = 0.20  # 5 Hz control loop (5x faster than before)
    
    def __init__(self, hand):
        super().__init__()
        self.hand = hand
        self.library = MotionLibrary()
        self.calibration = CalibrationLoader.load()
        
        # Setup control loop timer
        self.control_timer = QTimer()
        self.control_timer.timeout.connect(self.update_hand)
        self.control_timer.start(int(self.DT * 1000))  # Convert to ms
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize main window."""
        self.setWindowTitle("Robotic Hand Motion Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        tabs = QTabWidget()
        
        # Keyframe editor
        self.keyframe_editor = KeyframeEditor(self.hand, self.calibration)
        tabs.addTab(self.keyframe_editor, "Create Motion")
        
        # Library
        library_tab = self.create_library_tab()
        tabs.addTab(library_tab, "Motion Library")
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Control buttons
        top_layout = QHBoxLayout()
        save_btn = QPushButton("Save Current Motion")
        save_btn.clicked.connect(self.save_current_motion)
        top_layout.addWidget(save_btn)
        
        play_btn = QPushButton("Play Current Motion")
        play_btn.clicked.connect(self.play_current_motion)
        top_layout.addWidget(play_btn)
        
        stop_btn = QPushButton("Stop All Motion")
        stop_btn.clicked.connect(self.stop_all_motion)
        top_layout.addWidget(stop_btn)
        
        # Playback speed control
        top_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setMinimum(0.1)
        self.speed_spinbox.setMaximum(5.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setMinimumWidth(70)
        self.speed_spinbox.valueChanged.connect(self.on_speed_changed)
        top_layout.addWidget(self.speed_spinbox)
        top_layout.addWidget(QLabel("x"))
        
        # Loop checkbox
        self.preview_loop_checkbox = QCheckBox("Loop Preview")
        self.preview_loop_checkbox.setChecked(False)
        top_layout.addWidget(self.preview_loop_checkbox)
        
        layout.addLayout(top_layout)
        layout.addWidget(tabs)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def create_library_tab(self):
        """Create library tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Saved Motions:"))
        
        self.library_list = QListWidget()
        layout.addWidget(self.library_list)
        
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_library_list)
        button_layout.addWidget(refresh_btn)
        
        load_btn = QPushButton("Load & Preview")
        load_btn.clicked.connect(self.load_motion_from_library)
        button_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_motion_from_library)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        widget.setLayout(layout)
        
        self.refresh_library_list()
        return widget
    
    def refresh_library_list(self):
        """Refresh library list."""
        self.library_list.clear()
        for motion_name in self.library.list_motions():
            self.library_list.addItem(motion_name)
    
    def save_current_motion(self):
        """Save current keyframes."""
        keyframes = self.keyframe_editor.get_keyframes()
        
        if len(keyframes) < 2:
            QMessageBox.warning(self, "Warning", "Need at least 2 keyframes")
            return
        
        keyframes = sorted(keyframes, key=lambda x: x[0])

        # Ensure first keyframe at t=0.0 (preserve positions/torques)
        if keyframes[0][0] != 0.0:
            entry = keyframes[0]
            if len(entry) > 2:
                keyframes[0] = (0.0, entry[1], entry[2])
            else:
                keyframes[0] = (0.0, entry[1], {})
        
        dialog = MotionSaver(self)
        if dialog.exec_() == QDialog.Accepted:
            metadata = dialog.get_metadata()
            if not metadata.name:
                QMessageBox.warning(self, "Error", "Motion name required")
                return
            
            # Ensure last keyframe time matches metadata duration (preserve positions/torques)
            if metadata.duration != keyframes[-1][0]:
                entry = keyframes[-1]
                if len(entry) > 2:
                    keyframes[-1] = (metadata.duration, entry[1], entry[2])
                else:
                    keyframes[-1] = (metadata.duration, entry[1], {})
            
            if self.library.save_motion(metadata.name, keyframes, metadata):
                QMessageBox.information(self, "Success", f"Saved: {metadata.name}")
                self.refresh_library_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to save")
    
    def play_current_motion(self):
        """Play current keyframes."""
        keyframes = self.keyframe_editor.get_keyframes()
        
        if len(keyframes) < 2:
            QMessageBox.warning(self, "Warning", "Need at least 2 keyframes")
            return
        
        keyframes = sorted(keyframes, key=lambda x: x[0])
        duration = keyframes[-1][0]

        # Validate keyframes: first must be at t=0.0, last at duration (preserve torques)
        if keyframes[0][0] != 0.0:
            entry = keyframes[0]
            if len(entry) > 2:
                keyframes[0] = (0.0, entry[1], entry[2])
            else:
                keyframes[0] = (0.0, entry[1], {})
        if keyframes[-1][0] != duration:
            entry = keyframes[-1]
            if len(entry) > 2:
                keyframes[-1] = (duration, entry[1], entry[2])
            else:
                keyframes[-1] = (duration, entry[1], {})
        
        motion = Motion(
            name="preview",
            keyframes=keyframes,
            duration=duration,
            easing="ease_in_out_cubic",
            loop=self.preview_loop_checkbox.isChecked(),
        )
        
        self.hand.motion_player.play_motion(motion)
    
    def stop_all_motion(self):
        """Stop all motions."""
        self.hand.motion_player.stop_all()
    
    def on_speed_changed(self, value):
        """Update playback speed."""
        self.hand.motion_player.set_playback_speed(value)
    
    def load_motion_from_library(self):
        """Load motion from library (without playing)."""
        items = self.library_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Select a motion")
            return
        
        motion_name = items[0].text()
        result = self.library.load_motion(motion_name)
        if result:
            keyframes, metadata = result
            self.keyframe_editor.set_keyframes(keyframes)
            QMessageBox.information(self, "Info", f"Loaded: {motion_name}\n\nClick 'Play Current Motion' to start")
    
    def delete_motion_from_library(self):
        """Delete movement."""
        items = self.library_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Select a motion")
            return
        
        motion_name = items[0].text()
        reply = QMessageBox.question(self, "Confirm", f"Delete {motion_name}?")
        if reply == QMessageBox.Yes:
            if self.library.delete_motion(motion_name):
                QMessageBox.information(self, "Success", "Motion deleted")
                self.refresh_library_list()
    
    def update_hand(self):
        """Update hand state (called by timer every DT seconds)."""
        try:
            self.hand.update(self.DT)
        except Exception as e:
            print(f"[ERROR] Hand update failed: {e}")


def launch_motion_editor(hand):
    """Launch the motion editor GUI."""
    if not PYQT5_AVAILABLE:
        print("[ERROR] PyQt5 not available")
        return
    
    app = QApplication(sys.argv)
    window = MotionEditorWindow(hand)
    window.show()
    sys.exit(app.exec_())
