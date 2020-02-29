#CART

import pickle

class Cart:

    def __init__(self):

        self.pos = self.loadPos()
    
    def loadPos(self):
        posFile = open('POSITION.pickle','rb')
        pos = pickle.load(posFile)
        posFile.close()
        return pos
    
    def savePos(self):
        posFile = open('POSITION.pickle','wb')
        pickle.dump(self.pos)
        posFile.close()