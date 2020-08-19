# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:35:42 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit

g=Gradiometer()
atexit.register(g.motor.turnOffMotors)
atexit.register(g.savePos)
atexit.register(g.labjack.close)
g.zero()
foilNum = input('foil number? \n')
direction = input('par or perp? \n')
g.posRun(20, 58, 'foil{}-{}-short'.format(foilNum,direction))
g.goTo(0)
