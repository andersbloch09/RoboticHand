"""
Motor configuration and mapping system.

Defines static motor IDs and maps them to fingers/thumb.
Supports flexible configuration for different hardware setups.
"""


class MotorConfig:
    """
    Static motor ID mapping configuration.
    
    Supports 7 motors total (IDs 0-6):
    - Fingers 0-4: Flexion motors
    - Thumb: Flexion + Abduction motors
    """
    
    # Default motor ID mapping
    # Customize to match your hardware setup
    DEFAULT_CONFIG = {
        "finger_0_flexion": 4,      # Index finger flexion
        "finger_1_flexion": 0,      # Middle finger flexion
        "finger_2_flexion": 5,      # Ring finger flexion
        "finger_3_flexion": 2,      # Pinky finger flexion
        "thumb_flexion": 1,         # Thumb flexion
        "thumb_abduction": 6,       # Thumb abduction (left/right)
        "index_abduction": 3,       # Index finger abduction (optional)
    }
    
    def __init__(self, config=None):
        """
        Initialize motor configuration.
        
        Args:
            config: Dict mapping motor names to IDs.
                   Defaults to DEFAULT_CONFIG if None.
        """
        self.config = config or self.DEFAULT_CONFIG.copy()
        self._validate()
    
    def _validate(self):
        """Validate motor configuration."""
        ids = list(self.config.values())
        
        # Check for duplicate IDs
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate motor IDs in config: {self.config}")
        
        # Check all IDs are in valid range
        for name, motor_id in self.config.items():
            if not isinstance(motor_id, int) or motor_id < 0 or motor_id > 7:
                raise ValueError(f"Invalid motor ID {motor_id} for {name}. Must be 0-7.")
    
    def get_finger_motor_id(self, finger_index):
        """
        Get flexion motor ID for a finger (0-4).
        
        Args:
            finger_index: Finger number (0-4)
        
        Returns:
            Motor ID for flexion
        """
        key = f"finger_{finger_index}_flexion"
        if key not in self.config:
            raise ValueError(f"Finger {finger_index} not configured")
        return self.config[key]
    
    def get_thumb_flexion_id(self):
        """Get thumb flexion motor ID."""
        return self.config["thumb_flexion"]
    
    def get_thumb_abduction_id(self):
        """Get thumb abduction motor ID."""
        return self.config["thumb_abduction"]
    
    def get_index_abduction_id(self):
        """Get index finger abduction motor ID."""
        return self.config.get("index_abduction")
    
    @staticmethod
    def create_custom(finger_ids, thumb_flex_id, thumb_abd_id, index_abd_id=None):
        """
        Create custom motor configuration.
        
        Args:
            finger_ids: List of 5 motor IDs for fingers 0-4 (flexion)
            thumb_flex_id: Motor ID for thumb flexion
            thumb_abd_id: Motor ID for thumb abduction
            index_abd_id: Optional motor ID for index abduction
        
        Returns:
            MotorConfig instance
        """
        if len(finger_ids) != 5:
            raise ValueError("Must provide 5 finger motor IDs")
        
        config = {
            "finger_0_flexion": finger_ids[0],
            "finger_1_flexion": finger_ids[1],
            "finger_2_flexion": finger_ids[2],
            "finger_3_flexion": finger_ids[3],
            "finger_4_flexion": finger_ids[4],
            "thumb_flexion": thumb_flex_id,
            "thumb_abduction": thumb_abd_id,
        }
        
        if index_abd_id is not None:
            config["index_abduction"] = index_abd_id
        
        return MotorConfig(config)
    
    def __repr__(self):
        return f"MotorConfig({self.config})"
