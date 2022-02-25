# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 13:38:09 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit

g=Gradiometer()
atexit.register(g.motor.turn_off_motors)
atexit.register(g.save_pos)
atexit.register(g.labjack.close)
g.zero()
g.pos_run(0, 80, 'background')
g.goTo(0)
