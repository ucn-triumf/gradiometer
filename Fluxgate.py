import numpy as np


class Fluxgate:
    """
    Represents a fluxgate.

    :param labjack: Labjack object
    :param num: fluxgate number
    """
    def __init__(self, labjack, num):
        """Constructor method"""
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
            print("wrong number")
            # maybe this should throw an error instead

    def sample(self, samples_per_pos):
        """
        Takes a single measurement from the fluxgate

        :param samples_per_pos: number of samples averaged together for each measurement.
        :returns: tuple (float_array(3,), float_array(3,)): an array of the average for each axis, an array of the
        stdev for each axis
        """
        samples = np.zeros((samples_per_pos, 3))
        for i in range(samples_per_pos):
            samples[i, :] = self.labjack.readRegister(self.xReg, self.registers)
        return np.average(samples, 0), np.std(samples, 0) / np.sqrt(samples_per_pos)
