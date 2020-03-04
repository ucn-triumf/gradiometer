#GRADIOMETER

import atexit
import pickle

from Motor import Motor

class Gradiometer:

    def __init__(self):
        
        self.motor = Motor()
        self.pos = self.loadPos()
    
    def loadPos(self):
        posFile = open('POSITION.pickle','rb')
        try:
            pos = pickle.load(posFile)
        except EOFError:
            self.zero()
            self.savePos()
            self.loadPos()
        posFile.close()
        return pos
    
    def savePos(self):
        posFile = open('POSITION.pickle','wb')
        pickle.dump(self.pos, posFile)
        posFile.close()
        print('saved pos')

    def zero(self):
        self.setPos(0)
    
    def setPos(self,x):
        self.pos = x

    def getPos(self):
        return self.pos

def main():
    gradiometer = Gradiometer()
    atexit.register(gradiometer.motor.turnOffMotors)
    atexit.register(gradiometer.savePos)

if __name__ == '__main__':
    main()