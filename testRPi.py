"""This is a "dummy" RPi.GPIO library used for development on non-Raspberry Pi computers. Its only purpose is to
ensure the GUI code compiles. """

BOARD = "board"
BCM = "bcm"
OUT = "out"
IN = "in"


def input(pin):
    print(pin)


def output(pin, value):
    print(pin, ":", value)


def setmode(mode):
    print(mode)


def setup(pin, value):
    print(pin, ":", value)


def cleanup():
    print("clean-up")
