#GRADIOMETER

import atexit

from Motor import Motor
from Cart import Cart

class Gradiometer:

    def __init__(self):
        
        self.motor = Motor()
        self.cart = Cart()

gradiometer = Gradiometer()
atexit.register(gradiometer.motor.turnOffMotors)
