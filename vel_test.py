from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor

import time
import atexit
import threading
import math
import sys

class NullWriter(object):
    def write(self, arg):
        pass


# create a default object, no changes to I2C address or frequency
mh = Adafruit_MotorHAT()

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

# return user input
user_input 	= [None] # used for stopping the cart in case something goes wrong. just press enter to stop. 

speed_val 	= float(raw_input("Speed for cart in mm/s [0 - 26 mm/s]: "))
lap_number	= int(raw_input('Number of laps: '))*2
direction 	= int(raw_input("Starting direction [BACKWARD-0, FORWARD-1]: "))

#RPM = 378.43/(1050/speed_val - 15.75)
#RPM = (speed_val*367/1050)**(1/0.844)
RPM = 4.036e3/((1050/speed_val)**1.49)

print('--- Starting ---')
print('RPM set to: {}'.format(RPM))


# spawn a new thread to wait for input 
def get_user_input(user_input_ref):
    user_input_ref[0] = raw_input("Enter any key to stop: ")

mythread = threading.Thread(target=get_user_input, args=(user_input,))
mythread.daemon = True
mythread.start()

myStepper = mh.getStepper(200, 1)  # 200 steps/rev, motor port #1 leave as is. dependent on motor angular resolution ( i have not ensured that this is the correct value for our motor, but it doesn't matter )
myStepper.setSpeed(RPM)  



start_time 	= time.time() 
lap_time	= 1050/speed_val   # [s]
lap_counter     = 1
prev_lap        = 1

print('To stop the cart, press enter.')

# I couldn't get the myStepper.step function to stop printing output, so I temporarily disable output.
# figure out how to do this better 
nullwrite = NullWriter()
oldstdout = sys.stdout
sys.stdout = nullwrite # disable output

while user_input == [None] and lap_counter <= lap_number:
    elapsed_time = time.time() - start_time    
    lap_counter = math.floor(int(elapsed_time/lap_time)) + 1
    if direction == 0:
       	myStepper.step(1, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.DOUBLE)
    else:
        myStepper.step(1, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)

    if lap_counter%2 == 0 and prev_lap != lap_counter:
        if direction == 0:
            direction = 1
        else:
            direction = 0
        prev_lap = lap_counter

sys.stdout = oldstdout # enable output

print('Travel time:', time.time()-start_time)

turnOffMotors()