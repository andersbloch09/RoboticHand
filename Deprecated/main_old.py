from dynamixel_sdk import *
from controller import Controller
import select
import sys

n_motors = 7 # Number of motors in the hand -1 (0-6)
TORQUE_LIMIT = 0.25
POSITION_INCREMENT = 122
BLACKOUT_FILTER = [0, 2, 3, 5, 6]  # ACTIVE: 1, 4

def open_hand(goal_position, fingers_closed, start_position, controller):
    print("Opening hand...")
    for motor_id, motor in controller.motors.items():
         motor.torque_disable()
         motor.set_torque_limit(1.0)
         motor.torque_enable()
    while all(fingers_closed):
        for motor_id, motor in controller.motors.items():
            if motor_id in BLACKOUT_FILTER:
                fingers_closed[motor_id] = False
            else:
                if fingers_closed[motor_id]:
                    motor.set_position(start_position[motor_id])
                elif abs(motor.get_position() - start_position[motor_id]) < 10:
                    fingers_closed[motor_id] = False

def close_hand(goal_position, fingers_closed, controller):
    print("Closing hand...")
    TORQUE_MAXED = []
    for motor_id, motor in controller.motors.items():
            motor.torque_disable()
            motor.set_torque_limit(TORQUE_LIMIT)
            motor.torque_enable()
            goal_position[motor_id] = motor.get_position()
            TORQUE_MAXED.append(False)
    while not all(fingers_closed):
        for motor_id, motor in controller.motors.items():
            if motor_id in BLACKOUT_FILTER:
                fingers_closed[motor_id] = True
            else:
                if motor.get_torque() > (TORQUE_LIMIT * 0.9):
                    TORQUE_MAXED[motor_id] = True
                else:
                    TORQUE_MAXED[motor_id] = False
                if not TORQUE_MAXED[motor_id]:
                    goal_position[motor_id] += POSITION_INCREMENT
                    motor.set_position(goal_position[motor_id])
                    while abs(motor.get_position() - goal_position[motor_id]) > 10:
                        if motor.get_torque() > (TORQUE_LIMIT * 0.9):
                            TORQUE_MAXED[motor_id] = True
                            break
                        print(f"[ID:{motor_id}]goal_pos/current_pos: {goal_position[motor_id]:.3f}/{motor.get_position():.3f}, torque: {motor.get_torque():.3f} Nm")
                        #time.sleep(0.05)
                    #print(f"Motor ID {motor_id} has torque {motor.get_torque()} Nm and position {motor.get_position()} turns.")
                else:
                    TORQUE_MAXED[motor_id] = True
                    fingers_closed[motor_id] = True
                    print(f"[ID:{motor_id}] Torque limit reached for motor ID {motor_id}.")

def initialize_motors(controller):
    for motor_id, motor in controller.motors.items():
        motor.set_current_based_position_mode()
        print(f"Motor ID {motor_id} set to Current-Based Position Mode.")
        motor.set_torque_limit(TORQUE_LIMIT)
        motor.torque_enable()
        print(f"Motor ID {motor_id} torque limit set to {TORQUE_LIMIT:.1f} Nm and enabled.")

def reset(controller, fingers_closed=[], goal_position=[], start_position=[]):
    for motor_id, motor in controller.motors.items():
        fingers_closed[motor_id] = False
        start_position[motor_id] = motor.get_position()
        goal_position[motor_id] = motor.get_position()
    return fingers_closed, goal_position, start_position

def main():
    controller = Controller(n_motors)
    fingers_closed = [False] * n_motors
    goal_position = [0] * n_motors
    start_position = [0] * n_motors
    initialize_motors(controller)
    fingers_closed, goal_position, start_position = reset(controller, fingers_closed, goal_position, start_position)
    try:
        while True:
            print(f"fingers_closed: {fingers_closed}, goal_position: {goal_position}, start_position: {start_position}")
            if all(fingers_closed):
                open_hand(goal_position, fingers_closed, start_position, controller)
                time.sleep(1)
                fingers_closed, goal_position, start_position = reset(controller, fingers_closed, goal_position, start_position)
            else:
                time.sleep(1)
                close_hand(goal_position, fingers_closed, controller)

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