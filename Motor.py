from Adafruit_MotorHAT import Adafruit_MotorHAT


class Motor:
    """
    Represents a stepper motor.

    :param motor_number: 1 for lower motor, 2 for upper motor
    :param motor_speed: speed of the motor (RPM)
    """

    def __init__(self, motor_number, motor_speed):
        """Constructor method"""
        self.mh = Adafruit_MotorHAT()
        self.myStepper = self.mh.getStepper(200, motor_number)
        self.myStepper.setSpeed(motor_speed)

    def turn_off_motors(self):
        """turns off all motors on the MotorHAT"""
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
        print("motor turned off")
