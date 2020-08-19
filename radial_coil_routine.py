# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 16:47:55 2020

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
positions = np.linspace(14,64,51)
for pos in positions:
    input('set to {}cm and continue'.format(pos))
    g.timeRun(10,'radial-shield-{}'.format(pos),pos,False)