# FINGER STATES
# IDLE: Finger is not actively controlled, awaiting commands.
# CLOSING: The finger is in the process of closing, commanding increasing position.
#          Motion stops physically when motor torque limit is reached.
# HOLDING: The finger has reached torque limit and stopped; maintaining position.
# OPENING: The finger is in the process of opening back to the start position.

class Finger:
    """
    Non-blocking finger control abstraction.
    
    Uses calibrated min/max positions for direct targeting.
    Detects contact/stall via position change, NOT torque feedback.
    """
    
    # State constants
    IDLE = "IDLE"
    CLOSING = "CLOSING"
    HOLDING = "HOLDING"
    OPENING = "OPENING"
    
    def __init__(self, motor, base_step=10, stall_threshold=2, stall_time=0.1):
        """
        Initialize finger with motor attachment.
        
        Args:
            motor: MX_64 motor instance for this finger
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
        Command finger motion based on velocity scale.
        
        Args:
            velocity_scale: Velocity scale (0.0 to 1.0+)
                           > 0: Close finger
                           = 0: Open finger (return to start position)
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
        """Begin opening finger back to start position."""
        if self.state in (self.CLOSING, self.HOLDING):
            self.state = self.OPENING
            self.velocity_scale = 1.0  # Full speed opening
    
    def hold(self):
        """Hold current position."""
        self.state = self.HOLDING
        self.velocity_scale = 0.0
    
    def is_stalled(self):
        """Check if finger is currently in stalled/holding state."""
        return self.state == self.HOLDING
