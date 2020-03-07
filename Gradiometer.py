#GRADIOMETER

import atexit
import pickle
import numpy as np
import math
import csv
from datetime import datetime

try:
    from LabJackPython.src import u6
except ImportError:
    import u6

from Motor import Motor
from Fluxgate import Fluxgate

class Gradiometer:

    CM_PER_STEP = 0.0825

    def __init__(self):
        
        self.motor = Motor()
        self.pos = self.loadPos()
        self.labjack = u6.U6()
        self.fg1 = Fluxgate(self.labjack,1)
        self.fg2 = Fluxgate(self.labjack,2)

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
    
    def oneStep(self, direction):
        if direction == self.motor.mh.BACKWARD:
            self.motor.myStepper.oneStep(direction, self.motor.mh.DOUBLE)
            self.setPos(self.pos+self.CM_PER_STEP)
        elif direction == self.motor.mh.FORWARD:
            self.motor.myStepper.oneStep(direction, self.motor.mh.DOUBLE)
            self.setPos(self.pos-self.CM_PER_STEP)
    
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
    
    def run(self,start,stop,tag):
        filename = 'Run Data/{}-{}.csv'.format(datetime.now(),tag)
        csvfile = open(filename, 'w')
        fieldnames = ['time','position','x1','y2','z3','x2','y2','z2']
        writer = csv.DictWriter(csvfile,fieldnames)
        writer.writeheader()

        self.goTo(start)
        print('starting run at {}cm'.format(self.pos))

        dis = stop-self.pos
        steps = math.ceil(abs(dis/self.CM_PER_STEP))+1
        print('will take {} steps'.format(steps))
        if dis>0:
            direction = self.motor.mh.BACKWARD
        else:
            direction = self.motor.mh.FORWARD
        
        for step in range(steps):
            print('measuring at {}cm'.format(self.pos))
            time = datetime.now()
            position = self.pos
            [x1,y1,z1] = self.fg1.sample()
            [x2,y2,z2] = self.fg2.sample()
            writer.writerow({'time':time,'position':position,'x1':x1,'y1':y1,'z1':z1,'x2':x2,'y2':y2,'z2':z2})
            self.oneStep(direction)
        csvfile.close()
        print('finished at {}cm'.format(self.pos))

def main():
    gradiometer = Gradiometer()
    atexit.register(gradiometer.motor.turnOffMotors)
    atexit.register(gradiometer.savePos)

if __name__ == '__main__':
    main()
