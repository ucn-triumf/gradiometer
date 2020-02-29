#GRADIOMETER

import atexit

from Motor import Motor
from Cart import Cart

class Gradiometer:

    def __init__(self):
        
        self.motor = Motor()
        self.cart = Cart(self.motor)

def main():
    gradiometer = Gradiometer()
    atexit.register(gradiometer.motor.turnOffMotors)

if __name__ == '__main__':
    main()