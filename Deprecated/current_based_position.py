import time
import ctypes
import msvcrt
from dynamixel_sdk import *
from numpy import median

# ===== SETTINGS =====
PORT = 'COM3'
BAUDRATE = 9600
PROTOCOL_VERSION = 2.0

# ===== CONTROL TABLE =====
ADDR_OPERATING_MODE   = 11
ADDR_TORQUE_ENABLE    = 64
ADDR_GOAL_POSITION    = 116
ADDR_PRESENT_POSITION = 132
ADDR_PRESENT_VELOCITY = 128
ADDR_PRESENT_CURRENT  = 126
ADDR_GOAL_CURRENT = 102
ADDR_PROFILE_VELOCITY = 112
ADDR_CURRENT_LIMIT = 38

TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0
OPERATING_MODE_EXTENDED_POSITION = 4
OPERATING_MODE_CURRENT_BASED_POSITION = 5

TICKS_PER_REV = 4096
CURRENT_UNIT = 3.361  # mA per unit (6521.76 mA / 1941 from MX-64 datasheet)
KT_NM_PER_A = 1.463

# ===== CONTROL PARAMS =====
TARGET_TORQUE = 0.11          # target torque for calibration (Nm)
TORQUE_TOLERANCE = 0.05      # acceptable deviation from target (Nm)
STEP_TURNS = -10             # constant movement step during calibration (turns per loop)
POST_MOVE_SETTLE_S = 0.3     # wait for motor to come to complete standstill before measuring
CONTROL_DT_S = 0.05          # main control-loop period
REPEAT_COUNT = 5             # number of times to repeat returning to calibration point
MICRO_MOTION = 0.05          # back off from limit significantly to stabilize torque (was 0.001, increased)
REPEAT_SETTLE_S = 0.3        # longer settle time in repeat phase to stabilize measurements (matched to calibration)
NUM_READINGS = 5             # number of current readings to average for stability

# ===== HELPERS =====
def to_signed16(val):
    return ctypes.c_int16(val).value

def to_signed32(val):
    return ctypes.c_int32(val).value

# ===== MOTOR CLASS =====
class Motor:
    def __init__(self, motor_id, packetHandler, portHandler):
        self.id = motor_id
        self.packetHandler = packetHandler
        self.portHandler = portHandler

    def safe_write1(self, addr, value):
        result, error = self.packetHandler.write1ByteTxRx(self.portHandler, self.id, addr, value)
        return result == COMM_SUCCESS and error == 0
    
    def safe_write2(self, addr, value):
        value = ctypes.c_uint16(value).value
        result, error = self.packetHandler.write2ByteTxRx(self.portHandler, self.id, addr, value)
        return result == COMM_SUCCESS and error == 0

    def safe_write4(self, addr, value):
        value = ctypes.c_uint32(value).value
        result, error = self.packetHandler.write4ByteTxRx(self.portHandler, self.id, addr, value)
        return result == COMM_SUCCESS and error == 0

    def safe_read2(self, addr):
        val, result, error = self.packetHandler.read2ByteTxRx(self.portHandler, self.id, addr)
        if result != COMM_SUCCESS or error:
            return None
        return to_signed16(val)

    def safe_read4(self, addr):
        val, result, error = self.packetHandler.read4ByteTxRx(self.portHandler, self.id, addr)
        if result != COMM_SUCCESS or error:
            return None
        return to_signed32(val)

    # ===== SIGNAL =====
    def get_current_raw(self):
        return self.safe_read2(ADDR_PRESENT_CURRENT)

    def get_current_mA(self):
        raw = self.get_current_raw()
        if raw is None:
            return None
        return raw * CURRENT_UNIT
    
    def get_current_limit(self):
        raw = self.safe_read2(ADDR_CURRENT_LIMIT)
        if raw is None:
            return None
        return raw * CURRENT_UNIT

    def get_torque_estimate(self):
        current = self.get_current_mA()
        if current is None:
            return None
        return (current / 1000.0) * KT_NM_PER_A

    # ===== STATE =====
    def get_position(self):
        pos = self.safe_read4(ADDR_PRESENT_POSITION)
        return pos / TICKS_PER_REV if pos is not None else None

    def set_profile_velocity(self, rpm):
        # Max 285 from decimal
        # Convert RPM to ticks/s (MX-64: 0.229 RPM per unit)
        velocity_units = int(rpm / 0.229)
        velocity_units = max(0, min(285, velocity_units))  # Clamp to motor's actual range
        return self.safe_write4(ADDR_PROFILE_VELOCITY, velocity_units)

    def get_velocity(self):
        return self.safe_read4(ADDR_PRESENT_VELOCITY)

    # ===== CONTROL =====
    def enable(self):
        return self.safe_write1(ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

    def disable(self):
        return self.safe_write1(ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    def move_to(self, turns):
        ticks = int(turns * TICKS_PER_REV)
        return self.safe_write4(ADDR_GOAL_POSITION, ticks)
    
    def set_goal_current(self, current_mA):
        """Set goal current in current-control mode (bidirectional)"""
        # Current in units: positive = CCW, negative = CW
        # MX-64 range: -2047 to 2047 (each unit ≈ 3.36 mA)
        current_units = int(current_mA / CURRENT_UNIT)
        # Clamp to valid range
        current_units = max(-2047, min(2047, current_units))
        return self.safe_write2(ADDR_GOAL_CURRENT, current_units)

    def set_operating_mode(self, mode):
        result, error = self.packetHandler.write1ByteTxRx(self.portHandler, self.id, ADDR_OPERATING_MODE, mode)
        return result == COMM_SUCCESS and error == 0
    
    def set_torque_limit(self, torque_nm):
        """Set the current limit for current-control mode (bidirectional)"""
        # Current limit in units: positive value sets max CCW current, negative sets max CW current
        # MX-64 range: -2047 to 2047 (each unit ≈ 3.36 mA)
        current_mA = torque_nm / KT_NM_PER_A * 1000.0  # Convert nm to mA
        limit_units = int(current_mA / CURRENT_UNIT)
        # Clamp to valid range
        limit_units = max(-2047, min(2047, limit_units))
        print(f"Setting torque limit: {torque_nm:.1f} Nm -> {current_mA:.1f} mA -> {limit_units} units")
        return self.safe_write2(ADDR_CURRENT_LIMIT, limit_units)


def setup_motor(motor):
    motor.disable()
    if not motor.set_operating_mode(OPERATING_MODE_CURRENT_BASED_POSITION):
        print(f"⚠️ Failed to set Current-Based Position Mode on ID {motor.id}")
    else:
        print(f"ID {motor.id}: Current-Based Position Mode enabled")
    success = motor.set_torque_limit(TARGET_TORQUE)  # Set torque limit in Nm for current control
    if not success:
        print(f"Failed to set torque limit on ID {motor.id}")
    else:
        print(f"ID {motor.id}: Torque limit set to {TARGET_TORQUE:.1f} Nm")
    motor.enable()


def main():
    # ===== INIT =====
    portHandler = PortHandler(PORT)
    packetHandler = PacketHandler(PROTOCOL_VERSION)

    if not portHandler.openPort():
        print("Failed to open port"); exit()

    if not portHandler.setBaudRate(BAUDRATE):
        print("Failed to set baudrate"); exit()

    portHandler.setPacketTimeout(10)

    print("Port ready")

    # ===== MOTORS =====
    motors = [Motor(6, packetHandler, portHandler)]

    for m in motors:
        setup_motor(m)
   
    position_goal = None
    calibration_position = None
    MIN_POSITION = -100.0
    MAX_POSITION = 100

    torque_counter = 0
    filtered_torque = None

    print("Running... Press any key to stop")

    # Initialize goal from current motor position so negative motion stays valid
    initial_position = motors[0].get_position()
    if initial_position is None:
        position_goal = 0.0
        print("Could not read initial position, using 0.0 turns")
    else:
        position_goal = max(MIN_POSITION, min(MAX_POSITION, initial_position))
        print(f"Initial position: {position_goal:.3f} turns")

    # ===== LOOP =====
    try:
        stop_requested = False
        warned_torque_unavailable = False
        phase = "CALIBRATION"  # "CALIBRATION" or "REPEAT"
        repeat_iteration = 0

        while True:
            for m in motors:
                m.set_profile_velocity(20)  # Set a moderate velocity for smooth movement
                # ===== CALIBRATION PHASE =====
                if phase == "CALIBRATION":
                    position_goal += STEP_TURNS
                    position_goal = max(MIN_POSITION, min(MAX_POSITION, position_goal))
                    m.move_to(position_goal)

                    time.sleep(POST_MOVE_SETTLE_S)

                    torque = m.get_current_mA()
                    print(torque)
                    print(m.get_current_limit())


            if msvcrt.kbhit():
                print("\nUser requested stop")
                msvcrt.getch()
                break

            time.sleep(CONTROL_DT_S)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("\nStopping motors safely...")
        for m in motors:
            try:
                m.disable()
            except:
                pass

        portHandler.closePort()
        print("Clean shutdown complete")


if __name__ == "__main__":
    main()