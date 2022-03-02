# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:35:42 2020

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
g.pos_run(20, 58, 'foil{}-{}-short'.format(foilNum, direction))
g.go_to(0)
