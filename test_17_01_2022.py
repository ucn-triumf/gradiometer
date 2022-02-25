# -*- coding: utf-8 -*-
"""
Created on Fri Sep 04 08:04:12 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit
import time

g=Gradiometer()
atexit.register(g.motor.turnOffMotors)
atexit.register(g.savePos)
atexit.register(g.labjack.close)
g.zero()

g.goTo(20.0)
time.sleep(5)
g.goTo(5.0)


