#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  AutoCalibrationTest.py
#  
#  Copyright 2022  <pi@gradiometer>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
import RPi.GPIO as GPIO
from Gradiometer import Gradiometer
import time

limit_switch_lower_right = 6
limit_switch_lower_left = 5
limit_switch_upper_right = 13
limit_switch_upper_left = 12


GPIO.setmode(GPIO.BCM)
GPIO.setup(limit_switch_lower_right,GPIO.IN)
GPIO.setup(limit_switch_lower_left,GPIO.IN)
GPIO.setup(limit_switch_upper_right,GPIO.IN)
GPIO.setup(limit_switch_upper_left,GPIO.IN)

mh = Adafruit_MotorHAT()
myStepper = mh.getStepper(200, 2)
myStepper.setSpeed(60)   

while GPIO.input(limit_switch_lower_left)==0:
    myStepper.step(1,Adafruit_MotorHAT.BACKWARD,Adafruit_MotorHAT.DOUBLE)
    
if GPIO.input(limit_switch_lower_left)==1:
    print("reached backward limit")
    
while GPIO.input(limit_switch_lower_right)==0:
    myStepper.step(1,Adafruit_MotorHAT.FORWARD,Adafruit_MotorHAT.DOUBLE)
    
if GPIO.input(limit_switch_lower_right)==1:
    print("reached forward limit")
    
myStepper.step(100,Adafruit_MotorHAT.BACKWARD,Adafruit_MotorHAT.DOUBLE)
print("done calibrating")


"""while GPIO.input(limit_switch_upper_left)==0:
    myStepper.step(1,Adafruit_MotorHAT.FORWARD,Adafruit_MotorHAT.DOUBLE)
    
if GPIO.input(limit_switch_upper_left)==1:
    print("reached backward limit")
    
while GPIO.input(limit_switch_upper_right)==0:
    myStepper.step(1,Adafruit_MotorHAT.BACKWARD,Adafruit_MotorHAT.DOUBLE)
    
if GPIO.input(limit_switch_upper_right)==1:
    print("reached forward limit")
    
myStepper.step(100,Adafruit_MotorHAT.FORWARD,Adafruit_MotorHAT.DOUBLE)
print("done calibrating")
"""




