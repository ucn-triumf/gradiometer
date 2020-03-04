#CART

import pickle

class Cart:

    def __init__(self, motor):

        self.pos = self.loadPos()
        self.motor = motor
    
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