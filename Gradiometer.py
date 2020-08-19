#GRADIOMETER

import sys
import traceback
import atexit
import pickle
import numpy as np
import matplotlib.pyplot as plt
import math
import csv
from datetime import datetime

import u6

from Motor import Motor
from Fluxgate import Fluxgate

class Gradiometer:

    CM_PER_STEP = 0.082268

    def __init__(self):
        
        self.motor = Motor()
        self.pos = self.loadPos()
        self.labjack = u6.U6()
        self.fg1 = Fluxgate(self.labjack,1)
        self.fg2 = Fluxgate(self.labjack,2)

    def goTo(self,cm):
        dis = cm-self.pos
        steps = math.floor(abs(dis/self.CM_PER_STEP))
        print('goTo: starting at', self.pos)
        print('goTo: will take',steps,'steps')
        if dis>0:
            self.motor.myStepper.step(steps, self.motor.mh.BACKWARD, self.motor.mh.DOUBLE)
            self.setPos(self.pos+(self.CM_PER_STEP*steps))
        elif dis<0:
            self.motor.myStepper.step(steps, self.motor.mh.FORWARD, self.motor.mh.DOUBLE)
            self.setPos(self.pos-(self.CM_PER_STEP*steps))
        else:
            print('already at position')
        print('goTo: finished at position',self.pos)
        #self.motor.turnOffMotors()
    
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
    
    def posRun(self,start,stop,tag,graph=False,samples_per_pos=5):
        filename = 'Run_Data/{}-{}.csv'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),tag)
        csvfile = open(filename, 'w')
        fieldnames = ['timestamp','time','position',
                      'x1','y1','z1',
                      'x2','y2','z2',
                      'dx1','dy1','dz1',
                      'dx2','dy2','dz2']
        writer = csv.DictWriter(csvfile,fieldnames)
        writer.writeheader()

        self.goTo(start)
        print('starting run at {}cm'.format(self.pos))

        dis = stop-self.pos
        steps = math.ceil(abs(dis/self.CM_PER_STEP))+1
        startTime = datetime.now()
        print('will take {} steps'.format(steps))
        if dis>0:
            direction = self.motor.mh.BACKWARD
        else:
            direction = self.motor.mh.FORWARD
        try:
            for step in range(steps):
                timeStamp = datetime.now()
                time = (timeStamp-startTime).total_seconds()
                position = self.pos
                [x1,y1,z1],[dx1,dy1,dz1] = self.fg1.sample(samples_per_pos)
                [x2,y2,z2],[dx2,dy2,dz2] = self.fg2.sample(samples_per_pos)
                print('measuring at {:3.4f}cm, x1={:2.3f} y1={:2.3f} z1={:2.3f}, x2={:2.3f} y2={:2.3f} z2={:2.3f}'.format(self.pos,x1,y1,z1,x2,y2,z2))
                writer.writerow({'timestamp':timeStamp,'time':time,'position':position,
                                 'x1':x1,'y1':y1,'z1':z1,
                                 'x2':x2,'y2':y2,'z2':z2,
                                 'dx1':dx1,'dy1':dy1,'dz1':dz1,
                                 'dx2':dx2,'dy2':dy2,'dz2':dz2})
                self.oneStep(direction)
            print('finished at {}cm'.format(self.pos))
        except KeyboardInterrupt:
            print('run stopped at {}cm'.format(self.pos))
        finally:
            csvfile.close()
            self.motor.turnOffMotors()
            self.savePos()

        if graph:
            self.plotter(filename,mode=1)

    def timeRun(self,sec,tag,cm=None,graph=False):
        if cm==None:
            cm=self.getPos()
        filename = 'Run_Data/{}-{}.csv'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),tag)
        csvfile = open(filename, 'w')
        fieldnames = ['timestamp','time','position','x1','y1','z1','x2','y2','z2','dx1','dy1','dz1','dx2','dy2','dz2']
        writer = csv.DictWriter(csvfile,fieldnames)
        writer.writeheader()

        ainchannels = range(6)
        channeloptions = [0] * 6
        scanfreq = 1000
        self.labjack.getCalibrationData()
        self.labjack.streamConfig(NumChannels=len(ainchannels),ResolutionIndex=1,SettlingFactor=0,ChannelNumbers=ainchannels,ChannelOptions=channeloptions,ScanFrequency=scanfreq)

        missed = 0
        dataCount = 0
        packetCount = 0

        self.goTo(cm)
        print('starting run at {}cm'.format(self.pos))
        position = self.getPos()

        try:
            self.labjack.streamStart()
            startTime = datetime.now()
            print('starting run at {}'.format(startTime))

            for r in self.labjack.streamData():
                if r is not None:
                    #stop condition
                    if (datetime.now()-startTime).seconds > sec:
                        break
                    if r['errors'] != 0:
                        print("Error: %s ; " % r['errors'], datetime.now())
                    if r['numPackets'] != self.labjack.packetsPerRequest:
                        print("----- UNDERFLOW : %s : " % r['numPackets'], datetime.now())
                    if r['missed'] != 0:
                        missed += r['missed']
                        print("+++ Missed ", r['missed'])
                    
                    timeStamp = datetime.now()
                    time = (timeStamp-startTime).total_seconds() 
                    x1 = r['AIN0']
                    y1 = r['AIN1']
                    z1 = r['AIN2']
                    x2 = r['AIN3']
                    y2 = r['AIN4']
                    z2 = r['AIN5']

                    x1val = sum(x1)/len(x1)
                    y1val = sum(y1)/len(y1)
                    z1val = sum(z1)/len(z1)
                    x2val = sum(x2)/len(x2)
                    y2val = sum(y2)/len(y2)
                    z2val = sum(z2)/len(z2)
                    
                    dx1 = np.std(x1)
                    dy1 = np.std(y1)
                    dz1 = np.std(z1)
                    dx2 = np.std(x2)
                    dy2 = np.std(y2)
                    dz2 = np.std(z2)

                    print('measuring at {:4.2f}, x1={:2.3f} y1={:2.3f} z1={:2.3f}, x2={:2.3f} y2={:2.3f} z2={:2.3f}'.format(time,x1val,y1val,z1val,x2val,y2val,z2val))
                    writer.writerow({'timestamp':timeStamp, 'time':time,'position':position,
                                     'x1':x1val,'y1':y1val,'z1':z1val,
                                     'x2':x2val,'y2':y2val,'z2':z2val,
                                     'dx1':dx1,'dy1':dy1,'dz1':dz1,
                                     'dx2':dx2,'dy2':dy2,'dz2':dz2})

                    dataCount += 1
                    packetCount += r['numPackets']
                
                else:
                    print('no data')
        
        except Exception as e:
            tb = sys.exc_info()[-1]
            print(traceback.extract_tb(tb, limit=1)[-1][1]) # Print what line the Exception occured on
            print(e) #  Print the exception
        finally:
            stopTime = datetime.now()
            self.labjack.streamStop()
            #self.labjack.close()
            print('ending run at {}'.format(stopTime))
            sampleTotal = packetCount * self.labjack.streamSamplesPerPacket
            scanTotal = sampleTotal / len(ainchannels)
            print("{} requests with {} packets per request with {} samples per packet = {} samples total.".format(dataCount, (float(packetCount)/dataCount), self.labjack.streamSamplesPerPacket, sampleTotal))
            print("{} samples were lost due to errors.".format(missed))
            scanTotal -= missed
            print ("Adjusted total: {}".format(scanTotal))
            csvfile.close()
            #self.motor.turnOffMotors()
            self.savePos()
        
        if graph==True:
            self.plotter(filename,mode=2)
    
    def plotter(self,csvfile,mode):
        results = np.loadtxt(csvfile, delimiter=',', skiprows=1, usecols=[1,2,3,4,5,6,7,8])
        print(results.dtype)
        fig,[ax1,ax2]=plt.subplots(2,1,sharex=True)
        ax1.grid()
        ax1.set_title('Fluxgate 1')
        ax2.grid()
        ax2.set_title('Fluxgate 2')
        time = results[:,0]
        y1pos = results[:,1]
        z1pos = y1pos-1.5
        x1pos = y1pos-3
        x1 = results[:,2]
        y1 = results[:,3]
        z1 = results[:,4]
        x2 = results[:,5]
        y2 = results[:,6]
        z2 = results[:,7]
        if mode==1:
            ax1.plot(x1pos,x1,y1pos,y1,z1pos,z1)
            ax2.plot(x1pos,x2,y1pos,y2,z1pos,z2)
            plt.show()
        if mode==2:
            ax1.plot(time,x1,time,y1,time,z1)
            ax2.plot(time,x2,time,y2,time,z2)
            plt.show()


def main():
    g = Gradiometer()
    atexit.register(g.motor.turnOffMotors)
    atexit.register(g.savePos)
    atexit.register(g.labjack.close)

if __name__ == '__main__':
    main()
