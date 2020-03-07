#FLUXGATE

class Fluxgate:

    def __init__(self,labjack,num):
        
        self.labjack = labjack
        self.registers = 6
        if num == 1:
            self.xReg = 0
            self.yReg = 2
            self.zReg = 4
        elif num == 2:
            self.xReg = 6
            self.yReg = 8
            self.zReg = 10
        else:
            print('wrong number')
    
    def sample(self):
        return self.labjack.readRegister(self.xReg,self.registers)