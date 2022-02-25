# -*- coding: utf-8 -*-
"""
Created on Fri Sep 04 08:04:12 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit

g=Gradiometer()
atexit.register(g.motor.turn_off_motors)
atexit.register(g.save_pos)
atexit.register(g.labjack.close)
g.zero()

g.pos_run(0, 10, 'pos5')
g.pos_run(0, 10, 'pos10', samples_per_pos=10)
g.pos_run(0, 10, 'pos50', samples_per_pos=50)

g.timeRun(5,'time1000')
g.timeRun(5,'time500',scanFreq=500)
g.timeRun(5,'time2000',scanFreq=2000)
g.timeRun(5,'time8000',scanFreq=8000)