import atexit
from Gradiometer import Gradiometer

# Motor numbers
LOWER_MOTOR = 1
UPPER_MOTOR = 2
# used in all the cases when the motor speed should not be chosen by the user
STANDARD_MOTOR_SPEED = 60


def init_grad(motor_number, motor_speed):
    """
    Initializes gradiometer and sets atext functions for safe usage
    Only call this function once as only one gradiometer can be created

    :returns: gradiometer that has just been initialized
    """
    g = Gradiometer(motor_number, motor_speed)
    atexit.register(g.motor.turn_off_motors)
    atexit.register(g.save_pos)
    atexit.register(g.labjack.close)
    return g


def return_to_prev_window(current_window):
    """
    Closes the RunWindow and unfreezes the TaskSelection window.

    :param current_window: the current GUI window (RunWindow)
    """
    current_window.close()
    current_window.gradiometer.labjack.close()
    current_window.gradiometer.save_pos()
    current_window.gradiometer.motor.turn_off_motors()
