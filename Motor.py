#MOTOR

from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor

class Motor:
    def __init__(self):
        self.mh = Adafruit_MotorHAT()
        self.myStepper = self.mh.getStepper(200, 1)

    def turnOffMotors(self):
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
        print('turned off')
