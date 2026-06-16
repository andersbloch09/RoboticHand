import sys
import time
import signal
from controller import Controller
from hand import Hand
from motor_config import MotorConfig
from motion_editor_gui import launch_motion_editor

class RoboticHandDemo:
    # Control loop timing (100 Hz)
    CONTROL_FREQ = 100  # Hz
    DT = 1.0 / CONTROL_FREQ  # seconds
    
    def __init__(self, motor_config=None):
        """Initialize controller, hand, and gesture library."""
        self.running = True
        
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
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

def main():
    """Main entry point."""
    demo = None
    try:
        # Parse command line arguments
        mode = "motion_editor"
        
        # Initialize system
        demo = RoboticHandDemo()
        
        if mode == "motion_editor":
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