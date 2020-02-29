#CART

import pickle

class Cart:

    def __init__(self, motor):

        self.pos = self.loadPos()
        self.motor = motor
    
    def loadPos(self):
        posFile = open('POSITION.pickle','rb')
        pos = pickle.load(posFile)
        posFile.close()
        return pos
    
    def savePos(self):
        posFile = open('POSITION.pickle','wb')
        pickle.dump(self.pos)
        posFile.close()