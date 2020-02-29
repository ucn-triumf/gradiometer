#MOTOR

import atexit

class Motor:
    def __init__(self):

    def turnOffMotors(self):
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
	
    atexit.register(turnOffMotors)