import sys
import time
import signal
from controller import Controller
from hand import Hand
from motor_config import MotorConfig
from gestures import Gestures
from motion_editor_gui import launch_motion_editor


class RoboticHandDemo:
    """
    Demo application for robotic hand control system.
    
    Demonstrates:
    - Initialization with motor ID mapping
    - Non-blocking control loop
    - Gesture-based execution (Thumbs Up, Peace, Rock, OK, etc.)
    - Clean shutdown
    """
    
    # Control loop timing (100 Hz)
    CONTROL_FREQ = 100  # Hz
    DT = 1.0 / CONTROL_FREQ  # seconds
    
    def __init__(self, motor_config=None):
        """Initialize controller, hand, and gesture library."""
        self.running = True
        
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("[INFO] Initializing Robotic Hand Control System")
        
        # Initialize hardware controller
        self.controller = Controller(n_motors=7)
        print(f"[INFO] Controller initialized with motors: {list(self.controller.motors.keys())}")
        
        # Load motor configuration (with proper motor ID mapping)
        if motor_config is None:
            motor_config = MotorConfig()
        self.motor_config = motor_config
        print(f"[INFO] Motor configuration: {motor_config}")
        
        # Initialize hand abstraction with motor mapping
        self.hand = Hand(self.controller.motors, motor_config)
        print("[INFO] Hand abstraction initialized")
        
        # Run calibration on startup
        print("[INFO] Starting calibration...")
        self.hand.initialize_calibration()
        print("[INFO] Calibration complete")
        
        # Load gesture library
        self.gestures = Gestures.get_all_gestures()
        print(f"[INFO] Loaded {len(self.gestures)} gestures: {list(self.gestures.keys())}")
        
        print("[INFO] Initialization complete. Ready for gesture execution.")
    
    def run_gesture_sequence(self, duration_per_gesture=5.0):
        """
        Run a sequence of all available gestures.
        
        Args:
            duration_per_gesture: Time to hold each gesture (seconds)
        """
        gesture_names = list(self.gestures.keys())
        
        print(f"\n[INFO] Starting gesture sequence ({len(gesture_names)} gestures)")
        print(f"[INFO] Each gesture will be held for {duration_per_gesture} seconds\n")
        
        for i, gesture_name in enumerate(gesture_names):
            if not self.running:
                break
            
            gesture = self.gestures[gesture_name]
            print(f"\n>>> Gesture {i+1}/{len(gesture_names)}: {gesture_name.upper()}")
            self._execute_gesture(gesture, duration_per_gesture)
        
        # Final release
        print("\n>>> Releasing hand...")
        self.hand.deactivate_grasp()
        self._run_loop(1.0)
        
        print("\n[INFO] Gesture sequence complete")
    
    def run_single_gesture(self, gesture_name, duration_sec=4.0):
        """
        Execute a single gesture.
        
        Args:
            gesture_name: Name of gesture from gestures library
            duration_sec: Duration to hold gesture (seconds)
        """
        if gesture_name not in self.gestures:
            available = ", ".join(self.gestures.keys())
            print(f"[ERROR] Gesture '{gesture_name}' not found")
            print(f"[INFO] Available gestures: {available}")
            return
        
        gesture = self.gestures[gesture_name]
        print(f"\n[INFO] Executing gesture: {gesture_name.upper()}")
        self._execute_gesture(gesture, duration_sec)
        print("[INFO] Gesture complete")
    
    def run_interactive_demo(self):
        """
        Run interactive demo where user can select gestures.
        """
        print("\n" + "="*60)
        print("  ROBOTIC HAND GESTURE DEMO — INTERACTIVE MODE")
        print("="*60)
        
        gesture_list = list(self.gestures.keys())
        
        while self.running:
            print("\n[Available Gestures]")
            for i, name in enumerate(gesture_list, 1):
                print(f"  {i}. {name}")
            print("  0. Exit")
            
            try:
                choice = input("\n[Select gesture (number)]: ").strip()
                
                if choice == "0":
                    break
                
                idx = int(choice) - 1
                if 0 <= idx < len(gesture_list):
                    gesture_name = gesture_list[idx]
                    duration = input("[Hold for (seconds), default 2.0]: ").strip()
                    duration = float(duration) if duration else 2.0
                    
                    self.run_single_gesture(gesture_name, duration)
                else:
                    print("[ERROR] Invalid selection")
            
            except ValueError:
                print("[ERROR] Please enter a valid number")
            except KeyboardInterrupt:
                break
    
    def _execute_gesture(self, gesture, duration_sec):
        """
        Execute a gesture for specified duration.
        
        Sequence:
        1. Activate grasp
        2. Wait for all digits to reach stall/holding (gesture completion)
        3. Hold gesture for duration_sec
        4. Release
        
        Args:
            gesture: Grasp object to activate
            duration_sec: Duration to HOLD the gesture after completion (seconds)
        """
        print(f"[INFO] Activating gesture: {gesture.name}")
        self.hand.activate_grasp(gesture)
        
        # Phase 2: Hold gesture for specified duration
        print(f"[INFO] Holding gesture for {duration_sec}s")
        hold_start = time.time()
        last_status_time = hold_start
        
        while (time.time() - hold_start) < duration_sec and self.running:
            self._run_loop(self.DT)
            
            # Print status every 1 second
            current_time = time.time()
            if current_time - last_status_time >= 1.0:
                elapsed = current_time - hold_start
                states = self.hand.get_finger_states()
                stalled_count = sum(1 for s in states.values() if s == "HOLDING")
                #print(f"  [Hold {elapsed:.1f}s] {stalled_count}/{len(states)} DOF stalled | States: {states}")
                last_status_time = current_time
        self.hand.activate_grasp(Gestures.open_hand())  # Release to open hand after gesture
        
        # Open hand after holding
        hold_start = time.time()
        last_status_time = hold_start
        
        while (time.time() - hold_start) < duration_sec and self.running:
            self._run_loop(self.DT)
            
            # Print status every 1 second
            current_time = time.time()
            if current_time - last_status_time >= 1.0:
                elapsed = current_time - hold_start
                states = self.hand.get_finger_states()
                stalled_count = sum(1 for s in states.values() if s == "HOLDING")
                #print(f"  [Hold {elapsed:.1f}s] {stalled_count}/{len(states)} DOF stalled | States: {states}")
                last_status_time = current_time
    
    def _run_loop(self, duration_sec):
        """
        Run control loop for specified duration.
        
        Args:
            duration_sec: Duration to run (seconds)
        """
        start_time = time.time()
        while (time.time() - start_time) < duration_sec and self.running:
            # Non-blocking update step
            self.hand.update(self.DT)
            
            # Sleep for remainder of time step to maintain frequency
            # Use small 10ms increments to remain responsive to shutdown signal
            elapsed = time.time() - start_time
            remaining = (duration_sec - elapsed)
            if remaining > self.DT:
                sleep_increment = 0.01  # 10ms increments
                sleep_total = 0.0
                while sleep_total < self.DT and self.running:
                    time.sleep(min(sleep_increment, self.DT - sleep_total))
                    sleep_total += sleep_increment
            else:
                break
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and termination signals gracefully."""
        print("\n[INFO] Shutdown signal received")
        self.running = False
        raise KeyboardInterrupt()
    
    def cleanup(self):
        """Cleanup: release all digits and close port. Safe to call multiple times."""
        if not self.controller:
            return  # Already cleaned up
            
        print("\n[INFO] Cleaning up resources")
        try:
            self.hand.open_all()
            self.hand.update(self.DT)  # Execute final update to release
        except Exception as e:
            print(f"[WARNING] Error during hand release: {e}")
        
        try:
            if self.controller.port_Handler and self.controller.port_Handler.is_open():
                self.controller.port_Handler.closePort()
                print("[INFO] Serial port closed")
        except Exception as e:
            print(f"[WARNING] Error closing port: {e}")
        
        # Mark as cleaned up
        self.controller = None


def print_usage():
    """Print usage information."""
    print("\nUsage: python main.py [mode] [options]")
    print("\nModes:")
    print("  sequence              Run all gestures in sequence (default)")
    print("  interactive           Interactive gesture selection")
    print("  gesture <name>        Execute single gesture")
    print("  motion_editor         Launch motion editor GUI")
    print("\nGesture names:")
    print("  thumbs_up, peace_sign, rock_sign, ok_sign, open_hand,")
    print("  power_fist, point, precision_grip")
    print("\nExamples:")
    print("  python main.py                              # Run sequence")
    print("  python main.py interactive                  # Interactive mode")
    print("  python main.py gesture thumbs_up            # Single gesture")
    print("  python main.py gesture peace_sign 10        # Gesture for 10s")
    print("  python main.py motion_editor                # Launch motion editor GUI")


def main():
    """Main entry point."""
    demo = None
    try:
        # Create gesture library reference
        available_gestures = list(Gestures.get_all_gestures().keys())
        
        # Parse command line arguments
        mode = "sequence"
        gesture_name = None
        duration = 5.0
        
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == "gesture" and len(sys.argv) > 2:
                gesture_name = sys.argv[2]
                if len(sys.argv) > 3:
                    try:
                        duration = float(sys.argv[3])
                    except ValueError:
                        print(f"[ERROR] Invalid duration: {sys.argv[3]}")
                        print_usage()
                        sys.exit(1)
            elif mode not in ("sequence", "interactive", "motion_editor"):
                print(f"[ERROR] Unknown mode: {mode}")
                print_usage()
                sys.exit(1)
        
        # Initialize system
        demo = RoboticHandDemo()
        
        # Run requested mode
        if mode == "sequence":
            demo.run_gesture_sequence(duration_per_gesture=5.0)
        elif mode == "interactive":
            demo.run_interactive_demo()
        elif mode == "gesture":
            if gesture_name is None:
                print("[ERROR] Please specify gesture name")
                print_usage()
                sys.exit(1)
            if gesture_name not in available_gestures:
                print(f"[ERROR] Unknown gesture: {gesture_name}")
                print(f"[INFO] Available: {', '.join(available_gestures)}")
                sys.exit(1)
            demo.run_single_gesture(gesture_name, duration)
        elif mode == "motion_editor":
            print("[INFO] Launching motion editor GUI...")
            launch_motion_editor(demo.hand)
        
    except KeyboardInterrupt:
        print("\n[INFO] User interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if demo:
            demo.cleanup()
        print("[INFO] Shutdown complete")


if __name__ == "__main__":
    main()

