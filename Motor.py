#MOTOR

try:
    from Adafruit_Motor_HAT_Python_Library.Adafruit_MotorHAT.Adafruit_MotorHAT_Motors import Adafruit_MotorHAT, Adafruit_StepperMotor
except ImportError:
    print('first import failed')

try:
    from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor
except ImportError:
    print('second import failed')

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
