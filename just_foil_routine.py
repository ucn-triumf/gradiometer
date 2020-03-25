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
g.zero()
foilNum = input('foil number? \n')
direction = input('par or perp? \n')
g.posRun(25, 53, 'foil{}-{}-short'.format(foilNum,direction))
g.goTo(0)
