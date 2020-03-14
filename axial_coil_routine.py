# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 20:08:12 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import numpy as np

g=Gradiometer()
g.zero()
positions = range(81)
for pos in positions:
    g.timeRun(5,'axial-probe-{}'.format(pos),pos,False)
g.motor.turnOffMotors()
g.savePos()
