
 
from guizero import App, Text, TextBox, PushButton, Slider, Picture, Combo, info
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import time
import board
import sys
import threading

class Motor:
	def __init__(self):
		self.LEFT = False
		self.RIGHT = False


	def change_dist(self):
		dist = float(distance.value)
		d = int(2 * dist/0.173)
		kit = MotorKit(i2c=board.I2C())
		if which_motor.value == 'Fluxgate':
			for i in range(d):
				if f_or_b_choice.value == 'Forward':
					kit.stepper1.onestep()
					time.sleep(0.15)
				elif f_or_b_choice.value == 'Backward':
					kit.stepper1.onestep(direction = stepper.BACKWARD)
					time.sleep(0.15)
		elif which_motor.value == 'Tray':
			for i in range(d):
				if f_or_b_choice.value == 'Forward':
					kit.stepper2.onestep()
					time.sleep(0.15)
				elif f_or_b_choice.value == 'Backward':
					kit.stepper2.onestep(direction = stepper.BACKWARD)
					
					time.sleep(0.15)

	def move(self):
		i = 0
		kit = MotorKit(i2c=board.I2C())		
		my_thread = threading.Thread(target = self.stop_moving)
		my_thread.daemon = True
		my_thread.start()
		if which_motor.value == 'Fluxgate':
			while self.LEFT:
				kit.stepper1.onestep()
				time.sleep(0.15)
			while self.RIGHT:
				kit.stepper1.onestep(direction = stepper.BACKWARD)
				time.sleep(0.15)
		elif which_motor.value == 'Tray':
			while self.RIGHT:
				i = i + 1
				print(i)
				kit.stepper2.onestep(direction = stepper.BACKWARD)
				time.sleep(0.15)
			while self.LEFT:
				i = i + 1
				print(i)
				kit.stepper2.onestep()
				time.sleep(0.15)


	def move_left(self):
		self.LEFT = True
		self.move()

	def move_right(self):
		self.RIGHT = True
		self.move()

	def stop_moving(self):
		wait = input('Hit Enter: ')
		self.RIGHT = False
		self.LEFT = False

motor = Motor()
app = App(title="Manual Motor Control", layout = 'grid', width = 500, height = 350)
message = Text(app, text = "Type distance in box", grid = [0, 0], align = 'left')
distance = TextBox(app, width = 10, grid = [1, 0], align = 'left')
cm_text = Text(app, text = 'cm', grid = [2, 0], align = 'left')
f_or_b = Text(app, text = 'Move motor forwards or backwards?', grid = [0, 1], align = 'left')
f_or_b_choice = Combo(app, options = ['Forward', 'Backward'], grid = [1,1], align = 'left')
which = Text(app, text = 'Move tray or fluxgate?', grid = [0, 2], align = 'left')
which_motor = Combo(app, options = ['Tray', 'Fluxgate'], grid = [1, 2], align = 'left')
update_dist = PushButton(app, command = motor.change_dist, text='Enter', grid = [0, 3], align = 'left')
hold_text = Text(app, text = 'Hold to manually move', grid = [0, 4], align = 'left')
left = PushButton(app, text = 'Left', grid = [1, 4], align = 'right')
right = PushButton(app, text = 'Right', grid = [2, 4], align = 'left')
left.when_left_button_pressed = motor.move_left
right.when_left_button_pressed = motor.move_right
note = Text(app, text = 'Note: To stop motor from moving, press the enter button in terminal.', grid = [0, 5, 4, 1], align = 'left')


app.display()
