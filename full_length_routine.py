# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:31:47 2020

@author: bunch
"""

from Gradiometer import Gradiometer
import atexit

g=Gradiometer()
atexit.register(g.motor.turnOffMotors)
atexit.register(g.savePos)
g.zero()
foilNum = input('foil number?')
direction = input('par or perp?')
g.posRun(0, 80, 'foil{}-{}-full'.format(foilNum,direction))
g.goTo(0)