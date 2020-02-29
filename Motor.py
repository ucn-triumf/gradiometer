#MOTOR

from Adafruit_Motor_HAT_Python_Library.Adafruit_MotorHAT.Adafruit_MotorHAT_Motors import Adafruit_MotorHAT, Adafruit_StepperMotor


class Motor:
    def __init__(self):
        self.mh = Adafruit_MotorHAT()
        self.myStepper = self.mh.getStepper(200, 1)

    def turnOffMotors(self):
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
        print('turn off')