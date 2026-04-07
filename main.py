from dynamixel_sdk import *
from controller import Controller
import select
import sys

n_motors = 5
TORQUE_LIMIT = 0.1
POSITION_INCREMENT = 122
def kbhit():
    return select.select([sys.stdin], [], [], 0)[0] 

def main():
    controller = Controller(n_motors)
    goal_position = 0
    for motor_id, motor in controller.motors.items():
        motor.set_current_based_position_mode()
        print(f"Motor ID {motor_id} set to Current-Based Position Mode.")
        motor.set_torque_limit(TORQUE_LIMIT)
        motor.torque_enable()
        print(f"Motor ID {motor_id} torque limit set to {TORQUE_LIMIT:.1f} Nm and enabled.")
    try:
            
        while True:
            for motor_id, motor in controller.motors.items():
                if motor_id == 1:
                    motor.set_position(goal_position)
                    while abs(motor.get_position() < abs(goal_position)):
                        print(f"goal_pos/current_pos: {goal_position:.3f}/{motor.get_position():.3f}")
                        time.sleep(0.2)
                    goal_position += POSITION_INCREMENT
                    print(f"Motor ID {motor_id} has torque {motor.get_torque()} Nm and position {motor.get_position()} turns.")
                
    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("\nStopping motors safely...")
        for motor_id, motor in controller.motors.items():
                motor.torque_disable()
                print(f"Motor ID {motor_id} torque disabled.")

        controller.port_Handler.closePort()
        print("Clean shutdown complete")


if __name__ == "__main__":
    main()