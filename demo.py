# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 13:30:38 2020

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
g.pos_run(20, 58, 'foil{}-{}-short'.format(foilNum, direction), graph=True)
g.go_to(0)
