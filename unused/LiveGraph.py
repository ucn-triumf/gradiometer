#!/usr/bin/python
import sys
import traceback
import numpy
import os
import u6
import time
import logging
import atexit

import pyqtgraph as pg

from threading import Thread
from multiprocessing import Process

from datetime import datetime
from pyqtgraph.Qt import QtGui

from termcolor import colored  # Coloured start and stop statements
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#  User input functions
def get_int(prompt, lo=None, hi=None):
    while True:
        try:
            n = int(raw_input(prompt))
        except ValueError:
            print("ERROR: Expected Integer")
        else:  # got integer, check range
            if ((lo is None or n >= lo) and
                    (hi is None or n <= hi)):
                break  # valid
            print("Integer is not in Range")
    return n

def get_str(prompt):
    while True:
        try:
            n = str(raw_input(prompt))
        except ValueError:
            print("ERROR: Expected String")
        else:
            break  # valid
    return n


def get_float(prompt, lo=None, hi=None):
    while True:
        try:
            n = float(raw_input(prompt))
        except ValueError:
            print ("Enter a float")
        else:
            if (lo is None or n >= lo) and (hi is None or n <= hi):
                break # valid
            print("Not in range")
    return n

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Copied from Adafruit examples "StepperMotor.py"
class Motor:
    def __init__(self,velocity,lap_number,direction):
	# create a default object, no changes to I2C address or frequency
        self.mh = Adafruit_MotorHAT()
        self.myStepper = self.mh.getStepper(200, 1)  # 200 steps/rev, motor port #1
        
        #velocity_RPM = 378.43/(1050/velocity - 15.75)  # different fits to the calibration data
        #velocity_RPM = (velocity*367/1050)**(1/0.844)
        velocity_RPM = 4.036e3/((1050/velocity)**1.49)
        
        self.lap_time	= 1050/velocity   # [s]
	self.lap_number = lap_number
	self.direction = direction
        self.user_input = [None]
		
        self.myStepper.setSpeed(velocity_RPM)             # 30 RPM
	
	# recommended for auto-disabling motors on shutdown!
    def turnOffMotors(self):
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
	
        atexit.register(turnOffMotors)
    
    def listen(self):
        # listens for terminal input to stop motor
        self.user_input = raw_input("Press enter to stop cart: ")
        
    def run(self):
        # initializes the listening thread to stop the motor at any point
        
        # I couldn't get the myStepper.step function to stop printing output, so I temporarily disable output.
        # figure out how to do this better
        nullwrite = NullWriter()
        oldstdout = sys.stdout
        sys.stdout = nullwrite # disable output
        
        start_time 	= time.time() 
        lap_counter     = 1
        prev_lap        = 1
        
        while self.user_input == [None] and lap_counter <= self.lap_number:
            elapsed_time = time.time() - start_time    
            lap_counter = numpy.floor(int(elapsed_time/self.lap_time)) + 1
            if self.direction == 0:
                self.myStepper.step(1, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
            else:
                self.myStepper.step(1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)

            if lap_counter%2 == 0 and prev_lap != lap_counter:
                if self.direction == 0:
                    self.direction = 1
                else:
                    self.direction = 0
                    prev_lap = lap_counter
        
        sys.stdout = oldstdout # enable output

# used to turn off output from myStepper function.
class NullWriter(object):
    def write(self, arg):
        pass

#  Main class - takes LabJack device and controls stream
class DeviceStream:
    def __init__(self, mode, maxrequests, ainchannels, runtime, mag,
                 ain0curve, ain1curve, ain2curve, ain3curve, ain4curve, ain5curve, device):
        #  Args (probably a better way to do this?)
        self.mode = mode
        self.maxrequests = maxrequests
        self.ainchannels = ainchannels
        self.runtime = runtime
        self.mag = mag
        self.ain0curve = ain0curve
        self.ain1curve = ain1curve
        self.ain2curve = ain2curve
        self.ain3curve = ain3curve
        self.ain4curve = ain4curve
        self.ain5curve = ain5curve
        self.device = device

        #  Extra data
        self.missed = 0  # LabJack
        self.dataCount = 0  # LabJack
        self.packetCount = 0  # LabJack
        self.samples = 0
        self.xdata = []
        self.ain0data = []
        self.ain1data = []
        self.ain2data = []
        self.ain3data = []
        self.ain4data = []
        self.ain5data = []
        self.xdev1list = []
        self.ydev1list = []
        self.zdev1list = []
        self.xdev2list = []
        self.ydev2list = []
        self.zdev2list = []

    # Starts and stops stream and logs data
    def readdata(self):
        print colored("Starting stream...", "green")
        self.device.streamStart()
        starttime = datetime.now()
        print "Stream start time is %s" % starttime
        # Print appropriate header for number of channels being read
        if self.mode == 2:
            print('{:36}{:21}{:21}{:21}{:21}{:21}{:21}'.format('Sample Time', 'X (uT)', 'Y (uT)', 'Z (uT)', 'X STD', 'Y STD', 'Z STD'))

            logging.info('{:36}{:21}{:21}{:21}{:21}{:21}{:21}'.format('Sample Time', 'X (uT)', 'Y (uT)', 'Z (uT)', 'X STD', 'Y STD', 'Z STD'))
        else:
            print('{:36}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}'.format('Sample Time', 'AIN0', 'AIN1', 'AIN2',
                                                                         'AIN3', 'AIN4', 'AIN5', 'X STD 1', 'X STD 2', 'Y STD 1', 'Y STD 2', 'Z STD 1', 'Z STD 2'))
            logging.info('{:36}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}{:21}'.format('Sample Time', 'AIN0', 'AIN1', 'AIN2',
                                                                         'AIN3', 'AIN4', 'AIN5', 'X STD 1', 'X STD 2', 'Y STD 1', 'Y STD 2', 'Z STD 1', 'Z STD 2'))
        # Copied from LabJack U6 Sample code
        try:
            for r in self.device.streamData():
                if r is not None:
                    if (datetime.now() - starttime).seconds >= self.runtime * 60:
                        break
                    if r['errors'] != 0:
                        print "Error: %s ; " % r['errors'], datetime.now()
                    if r['numPackets'] != self.device.packetsPerRequest:
                        print "----- UNDERFLOW : %s : " % r['numPackets'], datetime.now()
                    if r['missed'] != 0:
                        self.missed += r['missed']
                        print "+++ Missed ", r['missed']

                    currenttime = (datetime.now() - starttime).total_seconds()
                    self.xdata.append(currenttime)

                    # First 3 AIN channels are always in use regardless of mode, calculate average value so far
                    ain0avg = sum(r["AIN0"]) / len(r["AIN0"])
                    ain1avg = sum(r["AIN1"]) / len(r["AIN1"])
                    ain2avg = sum(r["AIN2"]) / len(r["AIN2"])

                    self.ain0data.append(ain0avg)
                    self.ain1data.append(ain1avg)
                    self.ain2data.append(ain2avg)

                    self.ain0curve.setData(self.xdata, self.ain0data)
                    self.ain1curve.setData(self.xdata, self.ain1data)
                    self.ain2curve.setData(self.xdata, self.ain2data)

                    xdev1 = numpy.std(numpy.array(r["AIN0"]) * self.mag / 10)
                    self.xdev1list.append(xdev1)
                    ydev1 = numpy.std(numpy.array(r["AIN1"]) * self.mag / 10)
                    self.ydev1list.append(ydev1)
                    zdev1 = numpy.std(numpy.array(r["AIN2"]) * self.mag / 10)
                    self.zdev1list.append(zdev1)

                    #  Add extra AIN channels if mode 1/3
                    if self.mode == 1 or self.mode == 3:
                        ain3avg = sum(r["AIN3"]) / len(r["AIN3"])
                        ain4avg = sum(r["AIN4"]) / len(r["AIN4"])
                        ain5avg = sum(r["AIN5"]) / len(r["AIN5"])
                        self.ain3data.append(ain3avg)
                        self.ain4data.append(ain4avg)
                        self.ain5data.append(ain5avg)
                        self.ain3curve.setData(self.xdata, self.ain3data)
                        self.ain4curve.setData(self.xdata, self.ain4data)
                        self.ain5curve.setData(self.xdata, self.ain5data)
                        xdev2 = numpy.std(numpy.array(r["AIN3"]) * self.mag / 10)
                        ydev2 = numpy.std(numpy.array(r["AIN4"]) * self.mag / 10)
                        zdev2 = numpy.std(numpy.array(r["AIN2"]) * self.mag / 10)
                        self.xdev2list.append(xdev2)
                        self.ydev2list.append(ydev2)
                        self.zdev2list.append(zdev2)

                        print('{}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}'.format(datetime.now(), ain0avg,
                                                                                  ain1avg, ain2avg, ain3avg,
                                                                                  ain4avg, ain5avg, xdev1, xdev2, ydev1, ydev2, zdev1, zdev2))
                        logging.info('{}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}{:20}'.format(datetime.now(), ain0avg,
                                                                                         ain1avg, ain2avg, ain3avg,
                                                                                         ain4avg, ain5avg, xdev1,
                                                                                         xdev2, ydev1, ydev2, zdev1, zdev2))

                    else:
                        print('{}{:20}{:20}{:20}{:20}{:20}{:20}'.format(datetime.now(), ain0avg, ain1avg, ain2avg,
                                                              xdev1, ydev1, zdev1))
                        logging.info('{}{:20}{:20}{:20}{:20}{:20}{:20}'.format(datetime.now(), ain0avg, ain1avg, ain2avg,
                                                                     xdev1, ydev1, zdev1))

                    # Update graph and other data lists
                    QtGui.QApplication.processEvents()
                    self.dataCount += 1
                    self.packetCount += 1
                    self.samples += len(r["AIN0"])
                else:
                    print "No data", datetime.now()
                    print "".join(i for i in traceback.format_exc())

        except Exception as e:
            tb = sys.exc_info()[-1]
            print traceback.extract_tb(tb, limit=1)[-1][1]  # Print what line the Exception occured on
            print colored("Error, exception:", "red"), e  #  Print the exception

        finally:
            stoptime = datetime.now()
            self.device.streamStop()
            self.device.close()
            print "Stopped stream at %s" % stoptime
            if self.packetCount is not 0:
                #  Define final values
                sampletotal = self.packetCount * self.device.streamSamplesPerPacket
                scantotal = sampletotal / len(self.ainchannels)
                timetotal = stoptime - starttime
                #  Read out experiment results
                print "%s requests with %s packets per request with %s samples per packet = %s total samples" % (
                    self.dataCount, (float(self.packetCount) / self.dataCount),
                    self.device.streamSamplesPerPacket, sampletotal)
                print "%s samples lost due to error" % self.missed
                scantotal -= self.missed
                print "Adjusted total: %s" % scantotal # This is LabJack's idea but it prints odd numbers sometimes
                print "Experiment time:", timetotal

    
    
def main():
    # User input
    mode 	= 3#get_int("Which mode do you want to run in? [1- gradiometer, 2- single, 3 - dual]: ", 1, 3)
    logfile 	= 'garbo.log'#get_str("Filename for save?: ") + ".log"
    velocity	= 20#get_float("Cart velocity [mm/s]?: ", 0.01 ,20) 							#uncalibrated max & min
    n_laps	= 2 #get_int("Number of laps? [x2]: ", 1, 10)    
    direction = 1 #get_int("Starting direction [BACKWARD-0, FORWARD-1]: ",0,1)    
    #runtime 	= get_float("Runtime [min]?: ", 0, 10000)  
    runtime = n_laps*1050/velocity / 60  # needs to be minutes...
    
    print('Runtime has been set to: {} min'.format(runtime))
    maxrequests = 100 #get_int("Maximum requests (number of packets to be read?): ", 1, 1000)
    scanfreq 	= 1000 #get_int("Scan frequency? (Sample Frequency / #AINs, typ 1000Hz) ==> ", 0.001, 10000)
    logfreq 	= 600 #get_int("Log Frequency? [Logs/min] ==> ", 0.0000001, 10000000)
    
    
    ready = Motor(velocity,n_laps,direction)

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                        filename=os.getcwd() + "/NewRunLogs/" + logfile, filemode='w')
    logging.info('{:18}{:18}{:18}{:18}{:18}'.format('# Samples/CH', 'X (uT)', 'Y (uT)', 'Z (uT)', 'Net (uT)'))

    # Set up QWidget
    app = QtGui.QApplication([])
    win = pg.GraphicsWindow()
    win.setWindowTitle("Live Plot")
    p3 = win.addLayout()

    #  AIN0
    ain0plot = win.addPlot()
    ain0plot.enableAutoRange("y", enable=True)
    ain0plot.setXRange(0, runtime*60)
    ain0curve = ain0plot.plot()
    ain0curve.setPen("r")
    ain0plot.setLabel('bottom', "Time (s)")
    ain0plot.setTitle("AIN0 Average Reading")
    ain0plot.setLabel('left', "Amplitude (V)")
    p3.addItem(ain0plot, row=0, col=0)

    #  AIN 1
    ain1plot = win.addPlot()
    ain1plot.enableAutoRange("y", enable=True)
    ain1plot.setXRange(0, runtime * 60)
    ain1curve = ain1plot.plot()
    ain1curve.setPen("g")
    ain1plot.setTitle("AIN1 Average Reading")
    ain1plot.setLabel('bottom', "Time (s)")
    ain1plot.setLabel('left', "Amplitude (V)")
    p3.addItem(ain0plot, row=0, col=1)

    # AIN 2
    ain2plot = win.addPlot()
    ain2plot.enableAutoRange("y", enable=True)
    ain2plot.setXRange(0, runtime * 60)
    ain2curve = ain2plot.plot()
    ain2curve.setPen("b")
    ain2plot.setTitle("AIN2 Average Reading")
    ain2plot.setLabel('bottom', "Time (s)")
    ain2plot.setLabel('left', 'Amplitude (V)')
    p3.addItem(ain0plot, row=0, col=2)

    # AIN 3
    ain3plot = win.addPlot()
    ain3plot.enableAutoRange("y", enable=True)
    ain3plot.setXRange(0, runtime * 60)
    ain3curve = ain3plot.plot()
    ain3curve.setPen("y")
    ain3plot.setTitle("AIN3 Average Reading")
    ain3plot.setLabel('bottom', "Time (s)")
    ain3plot.setLabel('left', 'Amplitude (V)')
    p3.addItem(ain0plot, row=1, col=0)

    # AIN 4
    ain4plot = win.addPlot()
    ain4plot.enableAutoRange("y", enable=True)
    ain4plot.setXRange(0, runtime * 60)
    ain4curve = ain4plot.plot()
    ain4curve.setPen("m")
    ain4plot.setTitle("AIN4 Average Reading")
    ain4plot.setLabel('bottom', "Time (s)")
    ain4plot.setLabel('left', 'Amplitude (V)')
    p3.addItem(ain0plot, row=1, col=1)

    # AIN 5
    ain5plot = win.addPlot()
    ain5plot.enableAutoRange("y", enable=True)
    ain5plot.setXRange(0, runtime * 60)
    ain5curve = ain5plot.plot()
    ain5curve.setPen("c")
    ain5plot.setTitle("AIN5 Average Reading")
    ain5plot.setLabel('bottom', "Time (s)")
    ain5plot.setLabel('left', 'Amplitude (V)')
    p3.addItem(ain0plot, row=1, col=2)

    # Set variables based on magnitude 1 (100) 2 (1000) 3 (1000)
    if mode == 1:
        ainchannels = range(6)
        channeloptions = [0] * 6
        mag = 100

    elif mode == 3:
        ainchannels = range(6)
        channeloptions = [0]*6
        mag = 1000

    else:
        ainchannels = range(3)
        channeloptions = [0] * 3
        mag = 1000
        win.removeItem(ain3plot)
        win.removeItem(ain4plot)
        win.removeItem(ain5plot) # TODO: Add extra graphs here instead of removing items

    d = u6.U6()

    if d is None:
        print "Device not configured."
        sys.exit(0)

    d.getCalibrationData()
    d.streamConfig(NumChannels=len(ainchannels), ChannelNumbers=ainchannels, ChannelOptions=channeloptions,
                   SettlingFactor=1, ResolutionIndex=1, ScanFrequency=scanfreq)

    dev = DeviceStream(mode, maxrequests, ainchannels, runtime, mag,
                       ain0curve, ain1curve, ain2curve, ain3curve, ain4curve, ain5curve, device=d)
    
    t1 = Thread(target = ready.run)
    t2 = Thread(target = dev.readdata)
    t3 = Thread(target = ready.listen)

    t1.setDaemon(True)
    t2.setDaemon(True)
    t3.setDaemon(True)
    
    t1.start()
    t2.start()
    t3.start()
    
    
    
    pg.QtGui.QApplication.exec_()
    
    

if __name__ == "__main__":
    main()
4