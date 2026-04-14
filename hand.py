from finger import Finger
from thumb import Thumb
from synergy import Synergy
from motor_config import MotorConfig
from calibrator import Calibrator


class Hand:
    def __init__(self, motors_dict, motor_config=None):
        """
        Initialize hand with motor group and configuration.
        
        Args:
            motors_dict: Dictionary {motor_id: Motor} from Controller.find_motors()
            motor_config: MotorConfig instance mapping motor names to IDs.
                         Defaults to MotorConfig.DEFAULT_CONFIG if None.
        """
        self.motors = motors_dict
        
        # Load or create motor configuration
        if motor_config is None:
            motor_config = MotorConfig()
        self.motor_config = motor_config
        
        # Verify required motors are present
        required_motor_ids = set(motor_config.config.values())
        available_motor_ids = set(motors_dict.keys())
        
        missing = required_motor_ids - available_motor_ids
        if missing:
            raise ValueError(f"Missing motors with IDs: {missing}")
        
        # Initialize fingers (IDs mapped from config)
        self.fingers = {}
        for i in range(4):
            motor_id = motor_config.get_finger_motor_id(i)
            motor = self.motors[motor_id]
            self.fingers[f"finger_{i}"] = Finger(
                motor, base_step=120, stall_threshold=2, stall_time=0.1
            )
        
        # Initialize thumb with flexion and abduction motors
        thumb_flex_id = motor_config.get_thumb_flexion_id()
        thumb_abd_id = motor_config.get_thumb_abduction_id()
        thumb_flex_motor = self.motors[thumb_flex_id]
        thumb_abd_motor = self.motors[thumb_abd_id]
        self.thumb = Thumb(
            thumb_flex_motor, thumb_abd_motor,
            base_step=120, stall_threshold=2, stall_time=0.1
        )
        
        # Optional index abduction motor
        index_abd_id = motor_config.get_index_abduction_id()
        if index_abd_id is not None and index_abd_id in self.motors:
            self.index_abduction = Finger(
                self.motors[index_abd_id], base_step=120,
                stall_threshold=2, stall_time=0.1
            )
        else:
            self.index_abduction = None
        
        # Current active grasp (if any)
        self.active_grasp = None
    
    def initialize_calibration(self):
        calibrator = Calibrator(self)
        calibrator.calibrate_if_needed()
    
    def update(self, dt):
        # Update all fingers
        for finger in self.fingers.values():
            finger.update(dt)
        
        # Update thumb (both DOFs)
        self.thumb.update(dt)
        
        # Update index abduction if present
        if self.index_abduction:
            self.index_abduction.update(dt)
    
    def open_all(self):
        """Open all fingers and thumb."""
        for finger in self.fingers.values():
            finger.open()
        self.thumb.open()
        if self.index_abduction:
            self.index_abduction.open()
    
    def hold_all(self):
        """Hold all fingers and thumb in current position."""
        for finger in self.fingers.values():
            finger.hold()
        self.thumb.hold()
        if self.index_abduction:
            self.index_abduction.hold()
    
    def activate_grasp(self, grasp):
        """
        Activate a grasp configuration.
        
        Args:
            grasp: Grasp object containing synergy and torque limits
        """
        self.active_grasp = grasp
        grasp.start(self.fingers, self.thumb, self.index_abduction)
    
    def deactivate_grasp(self):
        """Deactivate current grasp and release all digits."""
        if self.active_grasp:
            self.active_grasp = None
        self.open_all()
    
    def get_finger_states(self):
        """
        Get current state of all fingers.
        
        Returns:
            dict: {digit_name: state_string}
        """
        states = {name: finger.state for name, finger in self.fingers.items()}
        states["thumb_flexion"] = self.thumb.flexion.state
        states["thumb_abduction"] = self.thumb.abduction.state
        if self.index_abduction:
            states["index_abduction"] = self.index_abduction.state
        return states
    
    def are_all_stalled(self):
        """Check if all fingers and thumb are in HOLDING state."""
        all_fingers_stalled = all(f.is_stalled() for f in self.fingers.values())
        thumb_stalled = self.thumb.is_stalled()
        index_abd_stalled = True if not self.index_abduction else self.index_abduction.is_stalled()
        return all_fingers_stalled and thumb_stalled and index_abd_stalled
