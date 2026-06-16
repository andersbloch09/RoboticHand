class ThumbDOF:
    # State constants
    IDLE = "IDLE"
    CLOSING = "CLOSING"
    HOLDING = "HOLDING"
    OPENING = "OPENING"
    
    def __init__(self, motor, base_step=10, stall_threshold=2, stall_time=0.1):
        """
        Initialize thumb DOF with motor attachment.
        
        Args:
            motor: MX_64 motor instance for this DOF
            base_step: Position increment per update cycle (ticks) - used if no calibration
            stall_threshold: Position delta threshold to detect stall (ticks)
            stall_time: Time duration to confirm stall state (seconds)
        """
        self.motor = motor
        self.state = self.IDLE
        self.velocity_scale = 0.0
        
        # Motion parameters
        self.base_step = base_step
        self.goal_position = 0
        self.start_position = 0
        
        # Calibration data
        self.calibrated = False
        self.calibration_start = 0
        self.calibration_min = 0
        self.calibration_max = 0
        
        # Stall detection parameters
        self.stall_threshold = stall_threshold
        self.stall_time = stall_time
        self.stall_timer = 0.0
        self.last_position = 0
    
    def set_calibration(self, start_pos, min_pos, max_pos):
        """
        Set calibrated position limits for direct targeting.
        
        Args:
            start_pos: Rest position (encoder ticks)
            min_pos: Fully closed position (encoder ticks)
            max_pos: Fully open position (encoder ticks)
        """
        self.calibration_start = start_pos
        self.calibration_min = min_pos
        self.calibration_max = max_pos
        self.calibrated = True
    
    def command(self, velocity_scale):
        """
        Command DOF motion based on velocity scale.
        
        Args:
            velocity_scale: Velocity scale (0.0 to 1.0+)
                           > 0: Close/flex the DOF
                           = 0: Open/extend the DOF (return to start position)
        """
        self.velocity_scale = velocity_scale
        
        if velocity_scale > 0:
            # Closing: transition to CLOSING from any state
            if self.state != self.CLOSING:
                self.state = self.CLOSING
                self.start_position = self.motor.get_position()
                if self.calibrated:
                    self.goal_position = self.calibration_min
                else:
                    self.goal_position = self.start_position
                self.last_position = self.start_position
                self.stall_timer = 0.0
        else:
            # Opening: transition to OPENING from any state (except already IDLE/OPENING)
            if self.state not in (self.OPENING, self.IDLE):
                self.state = self.OPENING
                self.velocity_scale = 1.0  # Full speed opening
                if self.calibrated:
                    self.goal_position = self.calibration_start
                else:
                    self.goal_position = self.start_position
                self.stall_timer = 0.0
    
    def update(self, dt):
        """
        Non-blocking update step. Called from Hand.update() each cycle.
        
        Args:
            dt: Time step (seconds)
        """
        current_position = self.motor.get_position()
        
        if self.state == self.CLOSING:
            # Use direct targeting to calibrated min position
            if self.calibrated:
                # Set goal directly to calibrated minimum; motor will accelerate towards it
                self.motor.set_position(self.goal_position)
            else:
                # Fallback: incremental stepping if not calibrated
                step = self.base_step * self.velocity_scale
                self.goal_position += step
                self.motor.set_position(self.goal_position)
            
            # Detect stall via position change
            position_delta = abs(current_position - self.last_position)
            
            if position_delta < self.stall_threshold:
                # Position not changing; accumulate stall time
                self.stall_timer += dt
                if self.stall_timer >= self.stall_time:
                    # Confirmed stall = contact/torque limit reached
                    self.state = self.HOLDING
            else:
                # Position is still changing; reset stall timer
                self.stall_timer = 0.0
            
            self.last_position = current_position
        
        elif self.state == self.OPENING:
            # Use direct targeting to start or calibrated start position
            if self.calibrated:
                self.motor.set_position(self.goal_position)
            else:
                step = self.base_step * self.velocity_scale
                self.goal_position -= step
                
                # Clamp to start position
                if self.goal_position <= self.start_position:
                    self.goal_position = self.start_position
                    self.state = self.IDLE
                
                self.motor.set_position(self.goal_position)
    
    def open(self):
        """Begin opening back to start position."""
        if self.state in (self.CLOSING, self.HOLDING):
            self.state = self.OPENING
            self.velocity_scale = 1.0  # Full speed opening
    
    def hold(self):
        """Hold current position."""
        self.state = self.HOLDING
        self.velocity_scale = 0.0
    
    def is_stalled(self):
        """Check if this DOF is currently in stalled/holding state."""
        return self.state == self.HOLDING


class Thumb:
    """
    Thumb control abstraction with 2 degrees of freedom (DOF).
    
    - Flexion DOF: Bending fingers inward
    - Abduction DOF: Left/right spreading
    
    Each DOF has independent state machine and stall detection.
    """
    
    def __init__(self, flexion_motor, abduction_motor, base_step=10, 
                 stall_threshold=2, stall_time=0.1):
        """
        Initialize thumb with flexion and abduction motors.
        
        Args:
            flexion_motor: MX_64 motor for flexion (closing thumb)
            abduction_motor: MX_64 motor for abduction (spreading thumb)
            base_step: Position increment per update cycle (ticks)
            stall_threshold: Position delta threshold to detect stall (ticks)
            stall_time: Time duration to confirm stall state (seconds)
        """
        # Two independent DOFs
        self.flexion = ThumbDOF(flexion_motor, base_step, stall_threshold, stall_time)
        self.abduction = ThumbDOF(abduction_motor, base_step, stall_threshold, stall_time)
    
    def command(self, velocity_scale_flexion=0.0, velocity_scale_abduction=0.0):
        """
        Command thumb motion on both DOFs.
        
        Args:
            velocity_scale_flexion: Flexion speed (0.0 to 1.0+)
            velocity_scale_abduction: Abduction speed (0.0 to 1.0+, can be negative for opposite direction)
        """
        # ALWAYS command both DOFs (even if 0.0, to trigger opening)
        self.flexion.command(velocity_scale_flexion)
        self.abduction.command(velocity_scale_abduction)
    
    def update(self, dt):
        """
        Non-blocking update step. Called from Hand.update() each cycle.
        
        Args:
            dt: Time step (seconds)
        """
        self.flexion.update(dt)
        self.abduction.update(dt)
    
    def open(self):
        """Open (extend) thumb back to start position."""
        self.flexion.open()
        self.abduction.open()
    
    def hold(self):
        """Hold current position."""
        self.flexion.hold()
        self.abduction.hold()
    
    def is_stalled(self):
        """Check if both DOFs are stalled."""
        return self.flexion.is_stalled() and self.abduction.is_stalled()
    
    def get_state(self):
        """Get state of both DOFs."""
        return {
            "flexion": self.flexion.state,
            "abduction": self.abduction.state,
        }