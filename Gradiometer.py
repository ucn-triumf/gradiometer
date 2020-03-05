#GRADIOMETER

import atexit
import pickle
import numpy as np
import math

from Motor import Motor

class Gradiometer:

    CM_PER_STEP = 0.0825

    def __init__(self):
        
        self.motor = Motor()
        self.pos = self.loadPos()

    def goTo(self,cm):
        dis = cm-self.pos
        steps = math.floor(abs(dis/self.CM_PER_STEP))
        if dis>0:
            print('starting at', self.pos)
            print('taking',steps,'steps')
            self.motor.myStepper.step(steps, self.motor.mh.BACKWARD, self.motor.mh.DOUBLE)
            self.setPos(self.pos+(self.CM_PER_STEP*steps))
            print('at position',self.pos)
        elif dis<0:
            print('starting at', self.pos)
            print('taking',steps,'steps')
            self.motor.myStepper.step(steps, self.motor.mh.FORWARD, self.motor.mh.DOUBLE)
            self.setPos(self.pos-(self.CM_PER_STEP*steps))
            print('at position',self.pos)
        else:
            print('already at position')
        self.motor.turnOffMotors()
    
    def loadPos(self):
        posFile = open('POSITION.pickle','rb')
        try:
            pos = pickle.load(posFile)
        except EOFError:
            self.zero()
            self.savePos()
            self.loadPos()
        posFile.close()
        return pos
    
    def savePos(self):
        posFile = open('POSITION.pickle','wb')
        pickle.dump(self.pos, posFile)
        posFile.close()
        print('saved pos')

    def zero(self):
        self.setPos(0)
    
    def setPos(self,x):
        self.pos = x

    def getPos(self):
        return self.pos

    def calibration(self):
        self.motor.myStepper.step(1000, self.motor.mh.FORWARD, self.motor.mh.DOUBLE)

def main():
    gradiometer = Gradiometer()
    atexit.register(gradiometer.motor.turnOffMotors)
    atexit.register(gradiometer.savePos)

    gradiometer.calibration()

if __name__ == '__main__':
    main()
