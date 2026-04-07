from dynamixel_sdk import *
from controller import Controller
import select
import sys

n_motors = 5
TORQUE_LIMIT = 0.1
POSITION_INCREMENT = -122

def main():
    controller = Controller(n_motors)
    
    goal_position = [0,0,0,0,0,0]
    for motor_id, motor in controller.motors.items():
        motor.set_current_based_position_mode()
        print(f"Motor ID {motor_id} set to Current-Based Position Mode.")
        motor.set_torque_limit(TORQUE_LIMIT)
        motor.torque_enable()
        print(f"Motor ID {motor_id} torque limit set to {TORQUE_LIMIT:.1f} Nm and enabled.")
        goal_position[motor_id] = motor.get_position()
        
    try:
            
        while True:
            for motor_id, motor in controller.motors.items():
                if motor_id == 4 or motor_id == 2:
                    pass
                else:
                    if motor.get_torque() > TORQUE_LIMIT * 0.9:
                        TORQUE_MAXED = True
                    else:
                        TORQUE_MAXED = False
                    if not TORQUE_MAXED:
                        goal_position[motor_id] += POSITION_INCREMENT
                        if goal_position[motor_id] < 0:
                            goal_position[motor_id] = 0
                        motor.set_position(goal_position[motor_id])
                        while abs(motor.get_position() - goal_position[motor_id]) > 10:
                            if motor.get_torque() > TORQUE_LIMIT * 0.9:
                                TORQUE_MAXED = True
                                break
                            print(f"[ID:{motor_id}]goal_pos/current_pos: {goal_position[motor_id]:.3f}/{motor.get_position():.3f}, torque: {motor.get_torque():.3f} Nm")
                            time.sleep(0.2)
                        print(f"Motor ID {motor_id} has torque {motor.get_torque()} Nm and position {motor.get_position()} turns.")
                    else:
                        print(f"[ID:{motor_id}] Torque limit reached at {motor.get_torque():.3f} Nm, holding position at {motor.get_position():.3f} turns.")
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