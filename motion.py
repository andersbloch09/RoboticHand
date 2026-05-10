"""
Motion system for complex, coordinated multi-DOF movements.

Keyframe-based animation with easing functions.
Supports synchronized multi-DOF control and queueable sequences.

Example - Index finger circular motion:
    motion = Motion(
        name="index_circle",
        keyframes=[
            (0.0, {"finger_0": 0.0, "finger_0_abd": 0.5}),  # Start: flexed, centered
            (0.5, {"finger_0": 0.5, "finger_0_abd": 1.0}),  # Opening, moving right
            (1.0, {"finger_0": 1.0, "finger_0_abd": 0.5}),  # Fully open, centered
            (1.5, {"finger_0": 0.5, "finger_0_abd": 0.0}),  # Closing, moving left
            (2.0, {"finger_0": 0.0, "finger_0_abd": 0.5}),  # Back to start
        ],
        duration=2.0,
        easing="ease_in_out_cubic",
    )
"""

import math
import json
import os
from enum import Enum
from typing import Dict, List, Tuple, Callable


class EasingFunction:
    """Collection of easing functions for smooth interpolation."""

    @staticmethod
    def linear(t: float) -> float:
        """Linear: no easing, constant speed."""
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Accelerating from zero velocity."""
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Decelerating to zero velocity."""
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Acceleration until halfway, then deceleration."""
        return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Accelerating from zero velocity (cubic)."""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Decelerating to zero velocity (cubic)."""
        return 1 + (t - 1) ** 3

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Smooth acceleration and deceleration (cubic)."""
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    @staticmethod
    def ease_in_sine(t: float) -> float:
        """Accelerating from zero velocity (sine)."""
        return 1 - math.cos((t * math.pi) / 2)

    @staticmethod
    def ease_out_sine(t: float) -> float:
        """Decelerating to zero velocity (sine)."""
        return math.sin((t * math.pi) / 2)

    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Smooth acceleration and deceleration (sine)."""
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def get_function(name: str) -> Callable[[float], float]:
        """Get easing function by name."""
        functions = {
            "linear": EasingFunction.linear,
            "ease_in_quad": EasingFunction.ease_in_quad,
            "ease_out_quad": EasingFunction.ease_out_quad,
            "ease_in_out_quad": EasingFunction.ease_in_out_quad,
            "ease_in_cubic": EasingFunction.ease_in_cubic,
            "ease_out_cubic": EasingFunction.ease_out_cubic,
            "ease_in_out_cubic": EasingFunction.ease_in_out_cubic,
            "ease_in_sine": EasingFunction.ease_in_sine,
            "ease_out_sine": EasingFunction.ease_out_sine,
            "ease_in_out_sine": EasingFunction.ease_in_out_sine,
        }
        if name not in functions:
            raise ValueError(f"Unknown easing function: {name}. Available: {list(functions.keys())}")
        return functions[name]


class Motion:
    """
    A single complex movement with keyframed multi-DOF control.
    
    Maps normalized digit positions (0.0 to 1.0) over time.
    0.0 = fully open (start position)
    1.0 = fully closed (calibrated min limit)
    """
    
    class State(Enum):
        IDLE = "IDLE"
        PLAYING = "PLAYING"
        PAUSED = "PAUSED"
        FINISHED = "FINISHED"
    
    def __init__(
        self,
        name: str,
        keyframes: List[Tuple[float, Dict[str, float]]],
        duration: float,
        easing: str = "ease_in_out_cubic",
        repeat: int = 1,
        loop: bool = False,
    ):
        """
        Initialize a motion.
        
        Args:
            name: Motion identifier (e.g., "index_circle")
            keyframes: List of (time, {digit_name: normalized_position})
                      - time: seconds from 0 to duration
                      - digit_name: e.g., "finger_0", "thumb_flexion", "finger_0_abd"
                      - normalized_position: 0.0 (open) to 1.0 (closed)
            duration: Total motion duration in seconds
            easing: Easing function name (see EasingFunction.get_function)
            repeat: Number of times to repeat motion
            loop: If True, repeat infinitely
        """
        self.name = name
        # Normalize keyframes to (time, positions_dict, torques_dict)
        normalized = []
        for k in keyframes:
            # support dict-style or tuple/list
            if isinstance(k, dict):
                t = k.get("time")
                pos = k.get("positions", {})
                tor = k.get("torques", {})
            elif isinstance(k, (list, tuple)):
                if len(k) == 2:
                    t, pos = k
                    tor = {}
                elif len(k) >= 3:
                    t, pos, tor = k[0], k[1], k[2]
                else:
                    raise ValueError("Invalid keyframe format")
            else:
                raise ValueError("Invalid keyframe format")
            normalized.append((t, pos or {}, tor or {}))

        self.keyframes = sorted(normalized, key=lambda x: x[0])  # Sort by time
        self.duration = duration
        self.easing_fn = EasingFunction.get_function(easing)
        self.repeat = repeat if not loop else float('inf')
        self.loop = loop
        
        # Validate normalized keyframes
        if not self.keyframes:
            raise ValueError("Motion must have at least one keyframe")
        if self.keyframes[0][0] != 0.0:
            raise ValueError("First keyframe must be at time 0.0")
        if self.keyframes[-1][0] != duration:
            raise ValueError("Last keyframe must be at motion duration")

        print(f"[DEBUG] Motion '{name}' created with {len(self.keyframes)} keyframes:")
        for t, pos, tor in self.keyframes:
            print(f"  t={t:.2f}s: {list(pos.keys())} torques={list(tor.keys())}")
        
        # State
        self.state = self.State.IDLE
        self.elapsed_time = 0.0
        self.current_repeat = 0
        self._last_targets = {}
        # Track last elapsed time to detect keyframe events (torque changes)
        self._last_elapsed_time = 0.0
    
    def update(self, dt: float) -> (Dict[str, float], Dict[str, float]):
        """
        Update motion and return current digit targets and torque change events.
        
        Args:
            dt: Time step (seconds)
        
        Returns:
            {digit_name: normalized_position} for all active digits
        """
        if self.state == self.State.IDLE:
            return {}, {}
        
        if self.state == self.State.PAUSED:
            return self._last_targets, {}
        
        # Advance time
        prev_time = self._last_elapsed_time
        self.elapsed_time += dt
        
        # Check if motion finished
        if self.elapsed_time >= self.duration:
            self.current_repeat += 1
            print(f"[DEBUG] {self.name}: completed repeat {self.current_repeat}/{self.repeat}")
            if self.current_repeat >= self.repeat:
                self.state = self.State.FINISHED
                print(f"[DEBUG] {self.name}: FINISHED after {self.current_repeat} repeats")
                # collect torque events for any keyframes crossed up to duration, then stop
                torque_events = self._collect_torque_events(prev_time, self.duration)
                self._last_elapsed_time = self.duration
                return self._last_targets, torque_events
            else:
                # Loop: reset time
                # gather torque events for segment prev_time -> duration
                torque_events = self._collect_torque_events(prev_time, self.duration)
                # then for the wrapped segment 0.0 -> remaining time
                wrapped = self.elapsed_time - self.duration
                if wrapped > 0:
                    torque_events.update(self._collect_torque_events(0.0, wrapped))
                self.elapsed_time = wrapped
                print(f"[DEBUG] {self.name}: looping, reset time to {self.elapsed_time:.3f}")
                self._last_elapsed_time = self.elapsed_time
                # Return current interpolated targets and torque events
                targets = self._interpolate_at_time(self.elapsed_time)
                self._last_targets = targets
                return targets, torque_events
        
        # Collect torque events for keyframes crossed in this update
        torque_events = self._collect_torque_events(prev_time, self.elapsed_time)

        # Interpolate positions at current time
        targets = self._interpolate_at_time(self.elapsed_time)
        self._last_targets = targets
        self._last_elapsed_time = self.elapsed_time
        return targets, torque_events

    def _collect_torque_events(self, start_time: float, end_time: float) -> Dict[str, float]:
        """Collect torque settings for keyframes whose time is within (start_time, end_time].

        Returns a mapping digit_name -> torque_value for all torques specified at those keyframes.
        If multiple keyframes set the same digit, later keyframe in time wins.
        """
        events = {}
        for t, pos, tor in self.keyframes:
            if start_time < t <= end_time:
                if tor:
                    events.update(tor)
        return events
    
    def _interpolate_at_time(self, time: float) -> Dict[str, float]:
        """
        Interpolate digit positions at a given time using keyframes and easing.
        
        Args:
            time: Time within motion (0.0 to duration)
        
        Returns:
            {digit_name: interpolated_position}
        """
        targets = {}
        
        # Find neighboring keyframes
        for i in range(len(self.keyframes) - 1):
            t1, frame1, _ = self.keyframes[i]
            t2, frame2, _ = self.keyframes[i + 1]
            
            if t1 <= time <= t2:
                # Interpolate between frame1 and frame2
                dt = t2 - t1
                if dt == 0:
                    # Simultaneous keyframes; use frame2
                    segment_targets = frame2
                else:
                    # Normalized time within this segment [0, 1]
                    t_norm = (time - t1) / dt
                    # Apply easing
                    t_eased = self.easing_fn(t_norm)
                    
                    # Interpolate each digit
                    segment_targets = {}
                    all_digits = set(frame1.keys()) | set(frame2.keys())
                    for digit in all_digits:
                        pos1 = frame1.get(digit, 0.0)
                        pos2 = frame2.get(digit, 0.0)
                        # Linear interpolation with eased time
                        segment_targets[digit] = pos1 + (pos2 - pos1) * t_eased
                
                targets.update(segment_targets)
                print(f"[DEBUG] {self.name} t={time:.3f}: segment [{t1:.3f}-{t2:.3f}] t_norm={t_norm:.3f} targets={list(targets.keys())}")
        
        if not targets:
            print(f"[DEBUG] {self.name} t={time:.3f}: NO KEYFRAMES FOUND! (duration={self.duration})")
        return targets
    
    def play(self):
        """Start playing motion from beginning."""
        self.state = self.State.PLAYING
        self.elapsed_time = 0.0
        self.current_repeat = 0
        self._last_targets = {}
    
    def pause(self):
        """Pause motion at current time."""
        if self.state == self.State.PLAYING:
            self.state = self.State.PAUSED
    
    def resume(self):
        """Resume paused motion."""
        if self.state == self.State.PAUSED:
            self.state = self.State.PLAYING
    
    def stop(self):
        """Stop motion and return to idle."""
        self.state = self.State.IDLE
        self.elapsed_time = 0.0
        self.current_repeat = 0
        self._last_targets = {}
    
    def is_finished(self) -> bool:
        """Check if motion has finished playing."""
        return self.state == self.State.FINISHED
    
    def is_playing(self) -> bool:
        """Check if motion is currently playing."""
        return self.state == self.State.PLAYING
    
    def __repr__(self):
        return (
            f"Motion(name='{self.name}', duration={self.duration}s, "
            f"repeat={self.repeat}, state={self.state.value})"
        )


class MotionSequence:
    """
    Queue of motions that play sequentially with optional parallelism.
    """
    
    def __init__(self, name: str, motions: List[Motion], parallel: bool = False):
        """
        Initialize motion sequence.
        
        Args:
            name: Sequence identifier
            motions: List of Motion objects to play
            parallel: If True, all motions play simultaneously
        """
        self.name = name
        self.motions = motions
        self.parallel = parallel
        self.current_index = 0
        self.is_playing = False
    
    def play(self):
        """Start playing sequence."""
        self.current_index = 0
        self.is_playing = True
        if self.motions:
            self.motions[0].play()
    
    def stop(self):
        """Stop sequence."""
        self.is_playing = False
        for motion in self.motions:
            motion.stop()
    
    def update(self, dt: float) -> Dict[str, float]:
        """
        Update sequence and merged targets from active motions.
        
        Args:
            dt: Time step
        
        Returns:
            Merged {digit_name: position} from all active motions
        """
        if not self.is_playing:
            return {}, {}
        
        merged_targets = {}

        if self.parallel:
            # All motions play at once
            merged_torque_events = {}
            for motion in self.motions:
                if not motion.is_finished():
                    targets, torques = motion.update(dt)
                    merged_targets.update(targets)
                    merged_torque_events.update(torques)

            # Check if all finished
            if all(m.is_finished() for m in self.motions):
                self.is_playing = False
            return merged_targets, merged_torque_events
        else:
            # Sequential: play one motion at a time
            if self.current_index < len(self.motions):
                current_motion = self.motions[self.current_index]
                targets, torques = current_motion.update(dt)
                merged_targets.update(targets)

                # If current motion finished, advance to next
                if current_motion.is_finished():
                    self.current_index += 1
                    if self.current_index < len(self.motions):
                        self.motions[self.current_index].play()
                    else:
                        self.is_playing = False

            return merged_targets, torques
    
    def is_finished(self) -> bool:
        """Check if all motions finished."""
        return not self.is_playing
    
    def __repr__(self):
        mode = "parallel" if self.parallel else "sequential"
        return f"MotionSequence(name='{self.name}', motions={len(self.motions)}, mode={mode})"


class MotionPlayer:
    """
    Applies motion targets to hand digits during control loop.
    """
    
    def __init__(self, hand, playback_speed=1.0):
        """
        Initialize motion player.
        
        Args:
            hand: Hand instance
            playback_speed: Multiplier for motion playback speed (>1.0 = faster, <1.0 = slower)
        """
        self.hand = hand
        self.current_sequence = None
        self.active_motions = []
        self.calibration = self._load_calibration()
        self.playback_speed = playback_speed  # Speed multiplier
    
    def play_sequence(self, sequence: MotionSequence):
        """Start playing a motion sequence."""
        sequence.play()
        self.current_sequence = sequence
    
    def play_motion(self, motion: Motion):
        """Start playing a single motion."""
        motion.play()
        self.active_motions.append(motion)
        self._ensure_position_mode()
    
    def set_playback_speed(self, speed: float):
        """Set motion playback speed multiplier."""
        if speed <= 0:
            print(f"[ERROR] Playback speed must be > 0, got {speed}")
            return
        self.playback_speed = speed
    
    def stop_all(self):
        """Stop all active motions and sequences."""
        if self.current_sequence:
            self.current_sequence.stop()
            self.current_sequence = None
        for motion in self.active_motions:
            motion.stop()
        self.active_motions = []
    
    def update(self, dt: float):
        """
        Update active motions and command hand digits.
        
        Args:
            dt: Time step
        """
        # Apply playback speed multiplier
        scaled_dt = dt * self.playback_speed
        
        if not hasattr(self, '_speed_logged'):
            print(f"[DEBUG] MotionPlayer: dt={dt:.3f}, playback_speed={self.playback_speed}, scaled_dt={scaled_dt:.3f}")
            self._speed_logged = True
        
        merged_targets = {}
        merged_torque_events = {}

        # Update sequence if active
        if self.current_sequence:
            targets, torques = self.current_sequence.update(scaled_dt)
            merged_targets.update(targets)
            merged_torque_events.update(torques)

            if self.current_sequence.is_finished():
                self.current_sequence = None
        
        # Update independent motions
        finished = []
        for motion in self.active_motions:
            targets, torques = motion.update(scaled_dt)
            if targets:
                merged_targets.update(targets)
            if torques:
                merged_torque_events.update(torques)

            if motion.is_finished():
                finished.append(motion)

        for motion in finished:
            self.active_motions.remove(motion)

        # First apply torque events (disable -> set limit -> enable)
        for digit, torque_value in merged_torque_events.items():
            try:
                self._apply_torque_change(digit, torque_value)
            except Exception as e:
                print(f"[ERROR] Failed to apply torque change for {digit}: {e}")

        # Then apply merged position targets to hand digits
        self._apply_targets(merged_targets)

    def _apply_torque_change(self, digit_name: str, torque_value: float):
        """Apply torque change to a given digit: disable torque, set limit, enable torque."""
        if digit_name not in self.calibration:
            # still attempt to map known digit names
            pass

        motor = None
        try:
            if digit_name.startswith("finger_"):
                idx = int(digit_name.split("_")[1])
                motor = self.hand.fingers.get(f"finger_{idx}").motor if self.hand.fingers.get(f"finger_{idx}") else None
            elif digit_name == "thumb_flexion":
                motor = self.hand.thumb.flexion.motor
            elif digit_name == "thumb_abduction":
                motor = self.hand.thumb.abduction.motor
            elif digit_name == "index_abduction" and self.hand.index_abduction:
                motor = self.hand.index_abduction.motor

            if not motor:
                return

            # Perform disable -> set limit -> enable sequence
            try:
                motor.torque_disable()
            except Exception:
                # continue even if disable not supported
                pass
            motor.set_torque_limit(float(torque_value))
            motor.torque_enable()
        except Exception as e:
            print(f"[ERROR] _apply_torque_change failed for {digit_name}: {e}")
    
    def _apply_targets(self, targets: Dict[str, float]):
        """
        Apply normalized positions to motors using calibration data.
        
        Maps normalized positions (0.0-1.0) to encoder positions:
        0.0 = open (start position)
        1.0 = closed (min position)
        
        Args:
            targets: {digit_name: normalized_position}
        """
        if not targets:
            return
        
        for digit_name, norm_pos in targets.items():
            # Clamp to [0, 1]
            norm_pos = max(0.0, min(1.0, norm_pos))
            
            # Get motor and apply position command
            if digit_name.startswith("finger_"):
                # Extract finger index
                finger_idx = int(digit_name.split("_")[1])
                if 0 <= finger_idx < 4:
                    self._apply_position(digit_name, norm_pos)
                else:
                    print(f"[ERROR] Finger index {finger_idx} out of range")
            
            elif digit_name == "thumb_flexion":
                self._apply_position(digit_name, norm_pos)
            
            elif digit_name == "thumb_abduction":
                self._apply_position(digit_name, norm_pos)
            
            elif digit_name == "index_abduction":
                self._apply_position(digit_name, norm_pos)
            else:
                print(f"[WARNING] Unknown digit: {digit_name}")
    
    def _apply_position(self, digit_name: str, normalized_pos: float):
        """
        Apply normalized position to motor using calibration.
        
        Args:
            digit_name: Name of digit (e.g., "finger_0", "thumb_flexion")
            normalized_pos: Position 0.0 (open) to 1.0 (closed)
        """
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
    
    def _load_calibration(self) -> Dict:
        """Load calibration data from calibration.json."""
        calibration_file = "calibration.json"
        if not os.path.exists(calibration_file):
            print(f"[ERROR] Calibration file not found: {calibration_file}")
            return {}
        
        try:
            with open(calibration_file, "r") as f:
                cal_data = json.load(f)
            return cal_data
        except Exception as e:
            print(f"[ERROR] Failed to load calibration: {e}")
            return {}
    
    def _ensure_position_mode(self):
        """Ensure all motors are in position control mode with torque enabled."""
        try:
            # Set all finger motors to position mode
            for i in range(4):
                motor = self.hand.fingers[f"finger_{i}"].motor
                motor.set_current_based_position_mode()
                motor.set_torque_limit(0.25)
                motor.torque_enable()
            
            # Set thumb motors to position mode
            self.hand.thumb.flexion.motor.set_current_based_position_mode()
            self.hand.thumb.flexion.motor.set_torque_limit(0.25)
            self.hand.thumb.flexion.motor.torque_enable()
            self.hand.thumb.abduction.motor.set_current_based_position_mode()
            self.hand.thumb.abduction.motor.set_torque_limit(0.25)
            self.hand.thumb.abduction.motor.torque_enable()
            
            # Set index abduction if present
            if self.hand.index_abduction:
                self.hand.index_abduction.motor.set_current_based_position_mode()
                self.hand.index_abduction.motor.set_torque_limit(0.25)
                self.hand.index_abduction.motor.torque_enable()
        except Exception as e:
            print(f"[ERROR] Failed to set position mode: {e}")
    
    def is_active(self) -> bool:
        """Check if any motions are playing."""
        return bool(self.current_sequence) or bool(self.active_motions)
