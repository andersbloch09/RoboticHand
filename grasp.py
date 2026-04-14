class Grasp:
    """
    Encapsulates a complete grasp configuration.
    
    A grasp is defined by:
    - Synergy (motion pattern with relative velocity gains)
    - Torque limits per motor (force profile)
    - Optional closure bounds
    
    Different grasps emerge from different gain distributions and torque limits.
    """
    
    def __init__(self, name, synergy, torque_limits_nm):
        """
        Initialize a grasp.
        
        Args:
            name: Grasp identifier (e.g., "power_grip", "peace_sign")
            synergy: Synergy object defining motion pattern {digit: velocity_gain}
            torque_limits_nm: Dict {digit_name: torque_nm}
                             e.g., {
                                 "finger_0": 1.5,
                                 "finger_1": 1.5,
                                 ...,
                                 "thumb_flexion": 1.2,
                                 "thumb_abduction": 1.0,
                                 "index_abduction": 0.8,  # optional
                             }
        """
        self.name = name
        self.synergy = synergy
        self.torque_limits_nm = torque_limits_nm
    
    def start(self, fingers_dict, thumb, index_abduction=None):
        # Set all motors to current-based position control mode and enable torque
        for finger_name, finger in fingers_dict.items():
            motor = finger.motor
            motor.set_current_based_position_mode()
            motor.torque_disable()
            if finger_name in self.torque_limits_nm:
                torque_limit = self.torque_limits_nm[finger_name]
                motor.set_torque_limit(torque_limit)
                motor.set_velocity(10)
            motor.torque_enable()
        
        # Configure thumb flexion motor
        thumb.flexion.motor.set_current_based_position_mode()
        thumb.flexion.motor.torque_disable()
        if "thumb_flexion" in self.torque_limits_nm:
            torque_limit = self.torque_limits_nm["thumb_flexion"]
            thumb.flexion.motor.set_torque_limit(torque_limit)
            thumb.flexion.motor.set_velocity(10)
        thumb.flexion.motor.torque_enable()
        
        # Configure thumb abduction motor
        thumb.abduction.motor.set_current_based_position_mode()
        thumb.abduction.motor.torque_disable()
        if "thumb_abduction" in self.torque_limits_nm:
            torque_limit = self.torque_limits_nm["thumb_abduction"]
            thumb.abduction.motor.set_torque_limit(torque_limit)
            thumb.abduction.motor.set_velocity(10)
        thumb.abduction.motor.torque_enable()
        
        # Configure index abduction if present
        if index_abduction:
            motor = index_abduction.motor
            motor.set_current_based_position_mode()
            motor.torque_disable()
            if "index_abduction" in self.torque_limits_nm:
                torque_limit = self.torque_limits_nm["index_abduction"]
                motor.set_torque_limit(torque_limit)
                motor.set_velocity(10)
            motor.torque_enable()
        
        # Activate synergy to command all digits
        self.synergy.activate(fingers_dict, thumb, index_abduction)
    
    def __repr__(self):
        return f"Grasp(name='{self.name}', synergy={self.synergy.name})"
