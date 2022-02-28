import atexit

from Gradiometer import Gradiometer

LOWER_MOTOR = 1
UPPER_MOTOR = 2
# used in all the cases when the motor speed should not be chosen by the user
STANDARD_MOTOR_SPEED = 60
remoteDev = False


def init_grad(motor_number, motor_speed):
    """Initializes gradiometer and sets atext functions for safe usage
    Only call this function once as only one gradiometer can be created

    Returns:
        Gradiometer: gradiometer that has just been initialized
    """
    g = Gradiometer(motor_number, motor_speed)
    atexit.register(g.motor.turn_off_motors)
    atexit.register(g.save_pos)
    atexit.register(g.labjack.close)
    return g


def return_to_prev_window(self):
    self.close()
    self.gradiometer.labjack.close()
    self.gradiometer.save_pos()
    self.gradiometer.motor.turn_off_motors()
