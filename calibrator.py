"""
Calibration system to measure digit encoder limits on startup.

Stores min/max positions for each digit in a JSON file.
On subsequent runs, skips calibration if file exists.
"""

import json
import time
import os

CALIBRATION_FILE = "calibration.json"


class Calibrator:
    """Calibrates finger and thumb positions by measuring encoder limits."""

    def __init__(self, hand, timeout_per_digit=3.0):
        """
        Args:
            hand: Hand instance (contains all fingers and thumb)
            timeout_per_digit: Max time to spend calibrating one digit (seconds)
        """
        self.hand = hand
        self.timeout_per_digit = timeout_per_digit
        self.calibration_data = {}

    def calibrate_if_needed(self):
        """
        Runs calibration if calibration file doesn't exist.
        Loads existing calibration if file exists.
        Returns True if calibration ran, False if loaded from file.
        """
        if os.path.exists(CALIBRATION_FILE):
            print(f"[CALIBRATION] Loading existing calibration from {CALIBRATION_FILE}")
            with open(CALIBRATION_FILE, "r") as f:
                self.calibration_data = json.load(f)
            self._apply_calibration()
            return False
        else:
            print(f"[CALIBRATION] No calibration file found. Starting calibration...")
            self._run_calibration()
            self._save_calibration()
            self._apply_calibration()
            return True

    def _run_calibration(self):
        """Performs full calibration sequence for all digits."""
        print("\n=== CALIBRATION START ===")
        print("The hand will now measure encoder limits for all digits.")
        print("This involves closing and opening each digit fully.\n")

        # Calibrate all fingers
        for i in range(4):
            finger_key = f"finger_{i}"
            print(f"Calibrating {finger_key}...")
            self.calibration_data[finger_key] = self._calibrate_digit(
                self.hand.fingers[finger_key], finger_key
            )
            print()

        # Calibrate thumb flexion
        print("Calibrating thumb_flexion...")
        self.calibration_data["thumb_flexion"] = self._calibrate_digit(
            self.hand.thumb.flexion, "thumb_flexion"
        )
        print()

        # Calibrate thumb abduction
        print("Calibrating thumb_abduction...")
        self.calibration_data["thumb_abduction"] = self._calibrate_digit(
            self.hand.thumb.abduction, "thumb_abduction"
        )
        print()

        # Calibrate index abduction
        print("Calibrating index_abduction...")
        self.calibration_data["index_abduction"] = self._calibrate_digit(
            self.hand.index_abduction, "index_abduction"
        )
        print()

        print("=== CALIBRATION COMPLETE ===\n")

    def _calibrate_digit(self, digit, digit_name):
        """
        Calibrates a single digit by measuring start, min (close), and max (open) positions.

        Args:
            digit: Finger or ThumbDOF instance
            digit_name: Human-readable name for logging

        Returns:
            dict: {"start": pos, "min": pos, "max": pos}
        """
        # Record start position
        start_pos = digit.motor.get_position()
        print(f"  Start position: {start_pos}")

        # Move to fully closed position
        print(f"  Closing {digit_name}...")
        min_pos = self._move_to_limit(digit, "close", start_pos)
        print(f"  Min position (closed): {min_pos}")

        # Move to fully open position
        print(f"  Opening {digit_name}...")
        max_pos = self._move_to_limit(digit, "open", start_pos)
        print(f"  Max position (open): {max_pos}")

        return {"start": start_pos, "min": min_pos, "max": max_pos}

    def _move_to_limit(self, digit, direction, start_pos):
        """
        Moves a digit in a direction until it stalls (stops moving).

        Args:
            digit: Finger or ThumbDOF instance
            direction: "close" (contract) or "open" (extend)
            start_pos: Starting position for reference

        Returns:
            int: Final position when stalled
        """
        # Initialize motor for calibration: position control mode with torque
        motor = digit.motor
        print(f"    Setting up motor {motor.dxl_id} for {direction}...")
        motor.set_current_based_position_mode()
        motor.torque_disable()
        motor.set_torque_limit(0.3)  # Standard torque limit for calibration
        motor.torque_enable()
        print(f"    Motor {motor.dxl_id} initialized (position mode, torque enabled)")
        
        DT = 0.01  # Control loop timestep (100 Hz)
        stall_threshold = 2  # Position delta threshold (ticks)
        stall_check_interval = 0.2  # Check stall every N seconds
        stall_duration = 2.0  # Require 2 seconds of no movement to confirm stall
        stall_time_accumulated = 0.0

        # Set max velocity for faster movement
        # (profile_velocity: 0-1023 for MX-64, 100-200 is reasonable)
        motor.set_velocity(200)

        # Start movement
        if direction == "close":
            # Move towards minimum: command velocity > 0
            digit.command(1.0)
            print(f"    Commanding motor {motor.dxl_id} to close...")
        else:
            # Move towards maximum: command velocity = 0 (triggers opening)
            digit.command(0.0)
            print(f"    Commanding motor {motor.dxl_id} to open...")

        last_pos = motor.get_position()
        start_time = time.time()
        stall_check_time = 0.0
        print(f"    Initial position: {last_pos}")

        # Loop until stalled or timeout
        while time.time() - start_time < self.timeout_per_digit:
            # Call update() to actually execute motor commands
            digit.update(DT)
            
            time.sleep(DT)
            stall_check_time += DT

            if stall_check_time >= stall_check_interval:
                current_pos = motor.get_position()
                pos_delta = abs(current_pos - last_pos)
                elapsed = time.time() - start_time
                
                print(f"    [{elapsed:.1f}s] pos={current_pos}, delta={pos_delta}, stall_accumulated={stall_time_accumulated:.2f}s")

                if pos_delta < stall_threshold:
                    # No significant movement detected
                    stall_time_accumulated += stall_check_interval
                    if stall_time_accumulated >= stall_duration:
                        # Confirmed stalled
                        print(f"    ✓ Stalled at position {current_pos}")
                        return current_pos
                else:
                    # Position still changing, reset stall timer
                    stall_time_accumulated = 0.0

                last_pos = current_pos
                stall_check_time = 0.0

        # Timeout reached
        final_pos = motor.get_position()
        print(f"    WARNING: Calibration timeout for {direction}. Final position: {final_pos}")
        return final_pos

    def _save_calibration(self):
        """Saves calibration data to JSON file."""
        with open(CALIBRATION_FILE, "w") as f:
            json.dump(self.calibration_data, f, indent=2)
        print(f"Calibration saved to {CALIBRATION_FILE}")

    def _apply_calibration(self):
        """Applies loaded calibration to all digits."""
        # Apply to fingers
        for i in range(4):
            finger_key = f"finger_{i}"
            if finger_key in self.calibration_data:
                cal = self.calibration_data[finger_key]
                self.hand.fingers[finger_key].set_calibration(
                    cal["start"], cal["min"], cal["max"]
                )

        # Apply to thumb
        if "thumb_flexion" in self.calibration_data:
            cal = self.calibration_data["thumb_flexion"]
            self.hand.thumb.flexion.set_calibration(cal["start"], cal["min"], cal["max"])

        if "thumb_abduction" in self.calibration_data:
            cal = self.calibration_data["thumb_abduction"]
            self.hand.thumb.abduction.set_calibration(cal["start"], cal["min"], cal["max"])
        
        if "index_abduction" in self.calibration_data:
            cal = self.calibration_data["index_abduction"]
            self.hand.index_abduction.set_calibration(cal["start"], cal["min"], cal["max"])

        print("Calibration applied to all digits.\n")
