
from dynamixel_sdk import PortHandler, PacketHandler
import json

class MX_64:
    def __init__(self, dxl_id, dxl_io, json_file, protocol=1, control_table_protocol=None):
        """Initializes a new DynamixelMotor object"""

        # protocol 2 series motors can run using protocol 1, but still use the new control table.
        # this sets the control table choice to the default if one is not explicitly requested.
        if protocol == 1 or control_table_protocol is None:
            control_table_protocol = protocol

        # loads the JSON config file and gathers the appropriate control table.
        fd = open(json_file)
        config = json.load(fd)
        fd.close()
        if control_table_protocol == 1:
            config = config.get("Protocol_1")
        else:
            config = config.get("Protocol_2")

        # sets the motor object values based on inputs or JSON options.
        self.CONTROL_TABLE_PROTOCOL = control_table_protocol
        self.dxl_id = dxl_id
        self.dxl_io = dxl_io
        self.PROTOCOL = protocol
        self.CONTROL_TABLE = config.get("Control_Table")
        self.min_position = config.get("Values").get("Min_Position")
        self.max_position = config.get("Values").get("Max_Position")
        self.max_angle = config.get("Values").get("Max_Angle")
        self.CURRENT_UNIT = 3.361  # mA per unit (6521.76 mA / 1941 from MX-64 datasheet)
        self.KT_NM_PER_A = 1.463
        self.TICKS_PER_REV = 4096

    def write_control_table(self, data_name, value):
        """Writes a value to a control table area of a specific name"""
        self.dxl_io.write_control_table(self.PROTOCOL, self.dxl_id, value, self.CONTROL_TABLE.get(data_name)[0],
                                        self.CONTROL_TABLE.get(data_name)[1])

    def read_control_table(self, data_name):
        """Reads the value from a control table area of a specific name"""
        return self.dxl_io.read_control_table(self.PROTOCOL, self.dxl_id, self.CONTROL_TABLE.get(data_name)[0],
                                              self.CONTROL_TABLE.get(data_name)[1])

    def set_velocity_mode(self, goal_current=None):
        """Sets the motor to run in velocity (wheel) mode and sets the goal current if provided"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets velocity mode by setting both angle limits to 0.
            self.write_control_table("CW_Angle_Limit", 0)
            self.write_control_table("CCW_Angle_Limit", 0)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 1)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_position_mode(self, min_limit=None, max_limit=None, goal_current=None):
        """Sets the motor to run in position (joint) mode and sets the goal current if provided.
        If position limits are not specified, the full range of motion is used instead"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets position mode by having different values for min and max position.
            if min_limit is None or max_limit is None:
                min_limit = self.min_position
                max_limit = self.max_position
            # Convert signed to unsigned if needed
            if min_limit < 0:
                min_limit = min_limit + 0x100000000
            if max_limit < 0:
                max_limit = max_limit + 0x100000000
            self.write_control_table("CW_Angle_Limit", min_limit)
            self.write_control_table("CCW_Angle_Limit", max_limit)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 3)
            if min_limit is not None:
                # Convert signed to unsigned if needed
                if min_limit < 0:
                    min_limit = min_limit + 0x100000000
                self.write_control_table("Min_Position_Limit", min_limit)
            if max_limit is not None:
                # Convert signed to unsigned if needed
                if max_limit < 0:
                    max_limit = max_limit + 0x100000000
                self.write_control_table("Max_Position_Limit", max_limit)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_extended_position_mode(self, goal_current=None):
        """Sets the motor to run in extended position (multi-turn) mode"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets multi turn mode by setting both angle limits to max value.
            self.write_control_table("CW_Angle_Limit", self.max_position)
            self.write_control_table("CCW_Angle_Limit", self.max_position)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 4)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)
    
    def set_current_based_position_mode(self, goal_current=None):
        """Sets the motor to run in current-based position mode"""
        if self.CONTROL_TABLE_PROTOCOL == 2:
            self.write_control_table("Operating_Mode", 5)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_torque_limit(self, torque_nm):
        """Sets the current limit for current-control mode (bidirectional)"""
        # MX-64 range: -2047 to 2047 (each unit ≈ 3.36 mA)
        current_mA = torque_nm / self.KT_NM_PER_A * 1000.0  # Convert nm to mA
        limit_units = int(current_mA / self.CURRENT_UNIT)
        # Clamp to valid range
        limit_units = max(-2047, min(2047, limit_units))
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 calls torque limit Max Torque and only has a unidirectional current limit.
            if torque_nm < 0:
                print("[WARNING]: Protocol 1 does not support negative torque limits. Setting to 0.")
                torque_nm = 0
            self.write_control_table("Max_Torque", limit_units)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for bidirectional current limit.
            self.write_control_table("Current_Limit", limit_units)

    def move_to(self, turns):
        """Sets the goal position of the motor"""
        ticks = int(turns * self.TICKS_PER_REV)
        self.write_control_table("Goal_Position", ticks)

    def get_torque(self):
        """Returns the current motor torque in Nm"""
        current = self.get_current()        
        if current is None:
            return None
        # Convert from units to mA, then to A, then to Nm using the torque constant
        return (current * self.CURRENT_UNIT / 1000.0) * self.KT_NM_PER_A



    def set_velocity(self, velocity):
        """Sets the goal velocity of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
            if velocity < 0:
                velocity = abs(velocity)
                velocity += 1024
            self.write_control_table("Moving_Speed", velocity)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            if self.read_control_table("Operating_Mode") == 1:
                self.write_control_table("Goal_Velocity", velocity)
            else:
                velocity = int(velocity/0.229)  # Convert RPM to velocity units
                velocity = max(0, min(285, velocity))  # Clamp to motor's actual range
                self.write_control_table("Profile_Velocity", velocity)

    def set_acceleration(self, acceleration):
        """Sets the goal acceleration of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            self.write_control_table("Goal_Acceleration", acceleration)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            self.write_control_table("Profile_Acceleration", acceleration)

    def set_position(self, position):
        """Sets the goal position of the motor, converting signed to unsigned if needed"""
        # Convert to integer
        position = int(position)
        # Convert signed 32-bit to unsigned if negative
        if position < 0:
            position = position + 0x100000000  # 4294967296
        self.write_control_table("Goal_Position", position)

    def set_angle(self, angle):
        """Sets the goal position of the motor with a given angle in degrees"""
        self.set_position(
            # formula for mapping the range from min to max angle to min to max position.
            int(((angle / self.max_angle) * ((self.max_position + 1) - self.min_position)) + self.min_position))

    def get_position(self):
        """Returns the motor position"""
        raw_pos = self.read_control_table("Present_Position")
        # Convert 32-bit unsigned to signed if > 2^31
        if raw_pos > 0x7FFFFFFF:  # 2147483648
            raw_pos -= 0x100000000  # 4294967296
        return raw_pos

    def get_angle(self):
        """Returns the motor position as an angle in degrees"""
        return ((self.get_position() - self.min_position) / (
                (self.max_position + 1) - self.min_position)) * self.max_angle

    def get_current(self):
        """Returns the current motor load"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            current = self.read_control_table("Present_Load")
            if current < 0:
                return -1
            if current > 1023:
                # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
                current -= 1023
                current *= -1
            return current
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            current = self.read_control_table("Present_Current")
            # Convert 16-bit unsigned to signed if > 32767 (2^15 - 1)
            if current > 0x7FFF:  # 32767
                current -= 0x10000  # 65536
            return current

    def torque_enable(self):
        """Enables motor torque"""
        self.write_control_table("Torque_Enable", 1)

    def torque_disable(self):
        """Disables motor torque"""
        self.write_control_table("Torque_Enable", 0)