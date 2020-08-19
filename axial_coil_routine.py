# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 20:08:12 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import numpy as np
import atexit

g=Gradiometer()
atexit.register(g.motor.turnOffMotors)
atexit.register(g.savePos)
atexit.register(g.labjack.close)
g.zero()
positions = np.linspace(0,80,17)
for pos in positions:
    g.timeRun(10,'axial-IOswitch-{}'.format(pos),pos,False)
