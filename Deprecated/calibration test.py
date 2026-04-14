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

TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0
OPERATING_MODE_EXTENDED_POSITION = 4

TICKS_PER_REV = 4096
CURRENT_UNIT = 3.361  # mA per unit (6521.76 mA / 1941 from MX-64 datasheet)
KT_NM_PER_A = 1.463

# ===== CONTROL PARAMS =====
TARGET_TORQUE = 0.3          # target torque for calibration (Nm)
TORQUE_TOLERANCE = 0.05      # acceptable deviation from target (Nm)
STEP_TURNS = -0.03           # constant movement step during calibration (turns per loop)
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

def setup_motor(motor):
    motor.disable()
    if not motor.set_operating_mode(OPERATING_MODE_EXTENDED_POSITION):
        print(f"⚠️ Failed to set Extended Position Mode on ID {motor.id}")
    else:
        print(f"ID {motor.id}: Extended Position Mode enabled")
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
                # ===== CALIBRATION PHASE =====
                if phase == "CALIBRATION":
                    position_goal += STEP_TURNS
                    position_goal = max(MIN_POSITION, min(MAX_POSITION, position_goal))
                    m.move_to(position_goal)
                    
                # ===== REPEAT PHASE =====
                elif phase == "REPEAT":
                    # Return to the exact calibration position
                    m.move_to(calibration_position)

                # Re-check torque after the move command
                if phase != "REPEAT":
                    time.sleep(POST_MOVE_SETTLE_S)
                else:
                    # REPEAT phase - settle longer for stable measurements
                    time.sleep(REPEAT_SETTLE_S)

                # Take multiple readings and average to eliminate oscillation noise
                current_readings = []
                for _ in range(NUM_READINGS):
                    raw = m.get_current_raw()
                    if raw is not None:
                        current_readings.append(raw * CURRENT_UNIT)
                    time.sleep(0.01)  # Small delay between readings
                
                if current_readings:
                    current_mA = median(current_readings)
                    raw_current = int(current_mA / CURRENT_UNIT)
                else:
                    current_mA = None
                    raw_current = None
                
                torque = (current_mA / 1000.0) * KT_NM_PER_A if current_mA is not None else None


                # ===== CALIBRATION CHECK =====
                if phase == "CALIBRATION" and torque is not None:
                    if abs(torque) >= TARGET_TORQUE:
                        calibration_position = position_goal
                        print(f"\nCALIBRATION COMPLETE!")
                        print(f"   Target torque {TARGET_TORQUE:.3f} Nm reached at position {calibration_position:.3f} turns")
                        print(f"   Measured torque: {torque:.3f} Nm")
                        print(f"   Starting REPEAT phase - will return to this position {REPEAT_COUNT} times...\n")
                        phase = "REPEAT"

                # ===== REPEAT CHECK =====
                elif phase == "REPEAT" and torque is not None:
                    torque_error = abs(abs(torque) - TARGET_TORQUE)
                    if torque_error <= TORQUE_TOLERANCE and abs(torque) > 0.1:  # Ensure positive torque, not reversed/noise
                        torque_counter += 1
                        print(f"Repeat {repeat_iteration + 1}/{REPEAT_COUNT}: Torque {torque:.3f} Nm (±{torque_error:.3f} Nm from target)")
                        repeat_iteration += 1
                        if repeat_iteration >= REPEAT_COUNT:
                            print(f"\nCALIBRATION TEST COMPLETE - All {REPEAT_COUNT} repeats successful!")
                            stop_requested = True
                    else:
                        # Debug: show why this repeat didn't count
                        if abs(torque) <= 0.1:
                            reason = "torque reversed/collapsed"
                        else:
                            reason = f"torque {abs(torque):.3f} outside tolerance"
                        print(f"Repeat attempt: {reason}")

                if torque is None and not warned_torque_unavailable:
                    print("Torque read unavailable")
                    warned_torque_unavailable = True

                raw_text = str(raw_current) if raw_current is not None else "N/A"
                mA_text = f"{current_mA:7.1f}" if current_mA is not None else "    N/A"
                tq_text = f"{torque:6.3f}" if torque is not None else "   N/A"
                phase_text = phase
                calib_text = f"calib_pos={calibration_position:.3f}" if calibration_position is not None else "calibrating..."
                
                # Display the position the motor is at
                disp_pos = calibration_position if phase == "REPEAT" else position_goal
                    
                print(
                    f"[{phase_text}] {calib_text} | pos={disp_pos:6.3f} | "
                    f"I={mA_text} mA | torque={tq_text} Nm",
                )

            if stop_requested:
                break

            if position_goal <= MIN_POSITION and phase == "CALIBRATION":
                print("\nReached minimum position without finding target torque!")
                break

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