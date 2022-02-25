# MOTOR

from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor


class Motor:
    def __init__(
        self, motor_number, motor_speed
    ):  # motor number is 1 for the lower motor and 2 for the upper motor
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
