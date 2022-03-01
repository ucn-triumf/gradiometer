# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:31:47 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit

g=Gradiometer()
atexit.register(g.motor.turn_off_motors)
atexit.register(g.save_pos)
atexit.register(g.labjack.close)
g.zero()
foilNum = input('foil number? \n')
direction = input('par or perp? \n')
g.pos_run(0, 80, 'foil{}-{}-full'.format(foilNum, direction))
g.goTo(0)
