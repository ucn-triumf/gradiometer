
from datetime import datetime
import traceback
import sys
import u6
import time

from guizero import App, Text, TextBox, PushButton, Slider, Picture, Combo, info, CheckBox, Box, Window
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from scipy.optimize import curve_fit
#from bfit.bfit.fitting.minuit import minuit
#Set up matplotlib backend to TkAgg Gui Software
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

import time
import board
import sys
import threading

from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


Sample_Hz = 8.33
#the V_to_muT conversion should be variable
#value of 10 uT/V is for the mag-03MSL100 FGs
V_to_muT_mag_03MSL100 = 10 #uT/V
#value of 50 uT/V is for the mag-690_FL500 FGs
V_to_muT_mag_690_FL500 = 50 #uT/V
#value of 100 uT/V is for the mag-690_FL500 FGs
V_to_muT_mag_690_FL1000 = 100 #uT/V

# Scan frequency at 5 kHz
SCAN_FREQUENCY = 5000
#Uncertainty of Magnetometer
u = 0.005 #uT

#Set up u6
#d = None
#d = u6.U6()




class Read:
	def __init__(self):
		#Define values for B-fields in all axis from both fluxgates
		self.Bx = ''
		self.By = ''
		self.Bz = ''
		self.Bx2 = ''
		self.By2 = ''
		self.Bz2 = ''
		self.Bxs = []
		self.Bys = []
		self.Bzs = []
		self.Bxs2 = []
		self.Bys2 = []
		self.Bzs2 = []
		self.t = []
		self.dis = []
		self.plot_x = False
		self.plot_y = False
		self.plot_z = False
		self.plot_x2 = False
		self.plot_y2 = False
		self.plot_z2 = False
		self.close = True
		self.d = None
		self.d = u6.U6()
		self.new_par = pd.DataFrame(columns=['name', 'p0', 'blo', 'bhi', 'res', 'err-', 'err+'])
		self.distance = '0'
		

	
	def change_dist(self):
		dist = distance.value
		choice = f_or_b_choice.value
		motor = which_motor.value
		dist = float(dist)
		di = int(dist * 595 / 76.2)
		kit = MotorKit(i2c=board.I2C())
		if motor == 'Fluxgate':
			for i in range(di):
				self.dis = np.append(self.dis, 76.2 * i / 595)
				if choice == 'Forward':
					kit.stepper1.onestep()
					time.sleep(0.01)
					try:
						self.single_scan()
					except:
						pass

				elif choice == 'Backward':
					kit.stepper1.onestep(direction = stepper.BACKWARD)
					time.sleep(0.01)
					try:
						self.single_scan()
					except:
						pass

		elif motor== 'Tray':
			print(choice)
			print(di)
			for i in range(di):
				self.dis = np.append(self.dis, 76.2 * i / 595)
				if choice == 'Forward':
					kit.stepper2.onestep()
					time.sleep(0.01)
					try:
						self.single_scan()
					except:
						pass

				elif choice == 'Backward':
					kit.stepper2.onestep(direction = stepper.BACKWARD)
					time.sleep(0.01)
					try:
						self.single_scan()
					except:
						pass



	def save(self):
		filename = 'csv/' + f_title.value + '.csv'
		categories = {'Time': self.t}
		if self.plot_x == True:
			categories['Bx (\u03BC T)'] = self.Bxs
		if self.plot_y == True:
			categories['By (\u03BC T)'] = self.Bys
		if self.plot_z == True:
			categories['Bz (\u03BC T)'] = self.Bzs
		if self.plot_x2 == True:
			categories['Bx-2 (\u03BC T)'] = self.Bxs2
		if  self.plot_y2 == True:
			categories['By-2 (\u03BC T)'] = self.Bys2
		if self.plot_z2 == True:
			categories['Bz-2 (\u03BC T)'] = self.Bzs2
		if len(self.dis) != 0:
			categories['Distance (cm)'] = self.dis
		df = pd.DataFrame(categories)
		header = [ '#TUCAN Gradiometer B-field Measurements',
			'#',
			f'#Scan freq: {SCAN_FREQUENCY} Hz',
			f'#Sample freq: {Sample_Hz} Hz',
			f'#Range of Fluxgate: {FG_RANGE.value} \u03BC T']
		if zaxis.value == 1 or xaxis.value == 1 or yaxis.value == 1:
			#shouldn't these offsets depends on the choice of the FG used?
			header = header + [f'#Fluxgate 1 Serial No. {FG1_choice.value}', 
			f'#\t x-offset: 0.5896 \u00B1 0.0015 \u03BC T',
			f'#\t y-offset: 0.5861 \u00B1 0.0007 \u03BC T',
			f'#\t z-offset: 0.4189 \u00B1 0.0007 \u03BC T']
		if zaxis2.value == 1 or xaxis2.value == 1 or yaxis2.value == 1:
			header = header + [f'#Fluxgate 2 Serial No. {FG2_choice.value}',
			f'#\t x-offset: 0.4813 \u00B1 0.0175 \u03BC T',
			f'#\t y-offset: 0.5278 \u00B1 0.0009 \u03BC T']
			header = header + [f'#Date: {datetime.now()}',
			f'#Start Time: {self.t[0]}',
			f'#End Time: {self.t[-1]}',
			f'#Experimenters: {names.value}',
			f'#Comments: {Comment.value}',
			'# \n']
		with open(filename, 'w') as fid:
			fid.write('\n'.join(header))
		#Save to csv
		df.to_csv(filename, mode='a', index=False)
		name = 'figures/' + f_title.value + '.pdf'
		f.savefig(name)
	
		
	def fit_input(self):
		#which Data to fit
		if axis_choose.value == 'Bx-1':
			xval = self.Bxs
		if axis_choose.value == 'By-1':
			xval = self.Bys
		if axis_choose.value == 'Bz-1':
			xval = self.Bzs
		if axis_choose.value == 'Bx-2':
			xval = self.Bxs2
		if axis_choose.value == 'By-2':
			xval = self.Bys2
		if axis_choose.value == 'Bz-2':
			xval = self.Bzs2
		#Get fit data
		xstr = self.Bxs
		ystr = self.Bys
		tstr = self.t
		#make model
		parstr = params.value
		parnames = parstr.split(', ')
		print(parnames)
		eqn = equation.value
		model = 'lambda x, %s : %s' % (parstr, eqn)
		print(model)
		model_fn = eval(model)
		print(model_fn)
		#Set up p0 and bounds
		p0 = self.new_par['p0'].values
		blo = self.new_par['blo'].values
		bhi = self.new_par['bhi'].values
		p0 = list(map(float, p0))
		blo = list(map(float, blo))
		bhi = list(map(float, bhi))
		tval = self.dt_to_s(tstr)
		#xerrs_h = xval + u * xval
		#xerrs_l = xval - u * xval
		popt, pcov = curve_fit(model_fn, tval, xval)
		poptnames = str(popt)
		covnames = str(np.sqrt(np.diag(pcov)))
		pop_window = Window(app, title = 'Fitted Data', height = 550, width = 550, layout = 'grid')
		#Plot fit with data
		e = Figure(figsize=(5,5), dpi = 100, layout = 'constrained')
		b = e.add_subplot(111)
		b.plot(tval, xval, label = 'Data')
		b.plot(tval, [model_fn(t, *popt) for t in tval], label = 'Fit')
		b.set_xlabel('Time (s)')
		b.set_ylabel('B-field (\u03BC T)')
		b.legend()
		#b.text(0, 11, f'{parnames} = {poptnames}', wrap = True)
		#b.subplots(layout="constrained")
		canvas = FigureCanvasTkAgg(e, pop_window.tk)
		canvas.draw()
		canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 6)
		canvas._tkcanvas.grid(row = 0, column = 0, columnspan = 6)
		params_text = Text(pop_window, text = f'For {parnames} we have values {poptnames}', grid = [1,1])
		cov_text = Text(pop_window, text = f'For Standard Deviations we have {covnames}', grid = [1, 2])
		#fign = Text(pop_window, text = 'Name of Figure', grid = [0, 3], align = 'left')
		#name_fig = TextBox(pop_window, width = 30, grid = [1,3], align = 'left')
		e.savefig('/home/pi/gradiometer/figures/' + name_fig.value + '.pdf')
		
	def dt_to_s(self, t_array):
		t_prev = 0
		time = np.array([])
		for i in t_array:
			i = i.strftime('%H:%M:%S.%f')
			hr = float(i[0:2])
			min = float(i[3:5])
			sec = float(i[6:])
			if t_prev == 0:
				time = np.append(time, 0)
				t_prev = min * 60 + sec
			else:
				time = np.append(time, min*60 + sec - t_prev)
		return time
		
	def save_fit(self, b, name):
		name = '/home/pi/gradiometer/figures/' + name + '.pdf'
		b.savefig(name)
		


	def set_x(self):
		if xaxis.value == 1:
			self.plot_x = True
		else:
			self.plot_x = False


	def set_y(self):
		if yaxis.value == 1:
			self.plot_y = True
		else:
			self.plot_y = False

	def set_z(self):
		if zaxis.value == 1:
			self.plot_z = True
		else:
			self.plot_z = False

	def set_x2(self):
		if xaxis2.value == 1:
			self.plot_x2 = True
		else:
			self.plot_x2 = False

	def set_y2(self):
		if yaxis2.value == 1:
			self.plot_y2 = True
		else:
			self.plot_y2 = False

	def set_z2(self):
		if zaxis2.value == 1:
			self.plot_z2 = True
		else:
			self.plot_z2 = False


	def single_scan(self):
		# Scan frequency at 5 kHz
		SCAN_FREQUENCY = 5000
		#Applying proper calibration to reading
		self.d.getCalibrationData()
		self.d.streamConfig(NumChannels=6, ChannelNumbers = [0, 1, 2, 3, 4, 5], ChannelOptions = [0, 0, 0, 0, 0, 0], SettlingFactor = 1, ResolutionIndex=1, ScanFrequency=SCAN_FREQUENCY)
		self.close = False
		
		#set the right scaling to uT for the given model
		if FG1_scale.value=='mag-03':
			FG1_V_to_muT = V_to_muT_mag_03MSL100
		elif FG1_scale.value=='mag-690-1000':
			FG1_V_to_muT = V_to_muT_mag_690_FL1000
		else: 
			FG1_V_to_muT = V_to_muT_mag_690_FL500
			
		if FG2_scale.value=='mag-03':
			FG2_V_to_muT = V_to_muT_mag_03MSL100
		elif FG2_scale.value=='mag-690-1000':
			FG2_V_to_muT = V_to_muT_mag_690_FL1000
		else:
			FG2_V_to_muT = V_to_muT_mag_690_FL500
		

		if self.d is None:
			self.Bx = 'empty'
			self.By = 'empty'
			self.Bz = 'empty'
			self.Bx2 = 'empty'
			self.By2 = 'empty'
			self.Bz2 = 'empty'
		self.d.streamStart()
		start = datetime.now()

		time_start = time.perf_counter()
		missed = 0
		dataCount = 0
		packetCount = 0
		done = 0
		
		for r in self.d.streamData():
			if r is not None:
				if done == 1:
					self.close = True
					self.d.streamStop()
					self.d.close()
					self.d = u6.U6()
					dataCount = 0
				if dataCount < 2:
					dataCount +=1
					false_1 = str(sum(r['AIN3'])/len(r['AIN3']) * FG2_V_to_muT)
					false_1= str(sum(r['AIN4'])/len(r['AIN4']) * FG2_V_to_muT)
					false_1 = str(sum(r['AIN5'])/len(r['AIN5']) * FG2_V_to_muT)
					false_1 = str(sum(r['AIN0'])/len(r['AIN0']) * FG1_V_to_muT)
					false_1= str(sum(r['AIN1'])/len(r['AIN1']) * FG1_V_to_muT)
					false_1 = str(sum(r['AIN2'])/len(r['AIN2']) * FG1_V_to_muT)
				else:
					a.clear()
					self.Bx2 = str(sum(r['AIN3'])/len(r['AIN3']) * FG2_V_to_muT)
					self.By2 = str(sum(r['AIN4'])/len(r['AIN4']) * FG2_V_to_muT)
					self.Bz2 = str(sum(r['AIN5'])/len(r['AIN5']) * FG2_V_to_muT)
					self.Bx = str(sum(r['AIN0'])/len(r['AIN0']) * FG1_V_to_muT)
					self.By = str(sum(r['AIN1'])/len(r['AIN1']) * FG1_V_to_muT)
					self.Bz = str(sum(r['AIN2'])/len(r['AIN2']) * FG1_V_to_muT)
					Bx_text.value = self.Bx[:5]
					By_text.value = self.By[:5]
					Bz_text.value = self.Bz[:5]
					self.Bxs = np.append(self.Bxs, float(self.Bx))
					self.Bys = np.append(self.Bys, float(self.By))
					self.Bzs = np.append(self.Bzs, float(self.Bz))
					self.Bxs2 = np.append(self.Bxs2, float(self.Bx2))
					self.Bys2 = np.append(self.Bys2, float(self.By2))
					self.Bzs2 = np.append(self.Bzs2, float(self.Bz2))
					self.t = np.append(self.t, datetime.now())
					dataCount += 1
					#Plot the Live Graph
					#Read which axis to plot first
					if self.plot_x == True:
						a.plot(self.t, self.Bxs, label = 'Bx', color = 'blue')
						error_x = u * self.Bxs
						#a.fill_between(self.t, self.Bxs + error_x, self.Bxs - error_x, color = 'cyan', zorder = 1)
					if self.plot_y == True:
						a.plot(self.t, self.Bys, label = 'By', color = 'purple')
						error_y = u * self.Bys
						#a.fill_between(self.t, self.Bys + error_y, self.Bys - error_y, color = 'salmon', zorder = 1)
					if self.plot_z == True:
						a.plot(self.t, self.Bzs, label = 'Bz', color = 'steelblue')						
						error_z = u * self.Bzs
						#a.fill_between(self.t, self.Bzs + error_z, self.Bzs - error_z, color = 'greenyellow', zorder = 1)
					if self.plot_x2 == True:
						a.plot(self.t, self.Bxs2, label = 'Bx-2', color= 'red')
						error_x2 = u * self.Bxs2
						#a.fill_between(self.t, self.Bxs2 + error_x2, self.Bxs2 - error_x2, color = 'coral', zorder = 1)
					if self.plot_y2 == True:
						a.plot(self.t, self.Bys2, label = 'By-2', color = 'darkorange')
						error_y2 = u * self.Bys2
						#a.fill_between(self.t, self.Bys2 + error_y2, self.Bys2 - error_y2, color = 'lightgreen', zorder = 1)
					if self.plot_z2 == True:
						a.plot(self.t, self.Bzs2, label = 'Bz-2', color = 'violet')
						error_z2 = u * self.Bzs2
						#a.fill_between(self.t, self.Bzs2 + error_z2, self.Bzs2 - error_z2, color = 'plum', zorder = 1)
					a.set_xlabel('Time')
					a.set_ylabel('B-field (\u03BC T)')
					a.legend()
					plt.setp(a.get_xticklabels(), rotation = 20, horizontalalignment = 'right')
					canvas.draw()
					done = 1
					app.update()

	def scan(self):
		# Scan frequency at 5 kHz
		SCAN_FREQUENCY = 5000
		#Applying proper calibration to reading
		self.d.getCalibrationData()
		self.d.streamConfig(NumChannels=6, ChannelNumbers = [0, 1, 2, 3, 4, 5], ChannelOptions = [0, 0, 0, 0, 0, 0], SettlingFactor = 1, ResolutionIndex=1, ScanFrequency=SCAN_FREQUENCY)
		self.close = False
		
		#set the right scaling to uT for the given model
		if FG1_scale.value=='mag-03':
			FG1_V_to_muT = V_to_muT_mag_03MSL100
		elif FG1_scale.value=='mag-690-1000':
			FG1_V_to_muT = V_to_muT_mag_690_FL1000
		else: 
			FG1_V_to_muT = V_to_muT_mag_690_FL500
			
		if FG2_scale.value=='mag-03':
			FG2_V_to_muT = V_to_muT_mag_03MSL100
		elif FG2_scale.value=='mag-690-1000':
			FG2_V_to_muT = V_to_muT_mag_690_FL1000
		else:
			FG2_V_to_muT = V_to_muT_mag_690_FL500

		if self.d is None:
			self.Bx = 'empty'
			self.By = 'empty'
			self.Bz = 'empty'
			self.Bx2 = 'empty'
			self.By2 = 'empty'
			self.Bz2 = 'empty'
		self.d.streamStart()
		start = datetime.now()

		time_start = time.perf_counter()
		missed = 0
		dataCount = 0
		packetCount = 0

		for r in self.d.streamData():
			if r is not None:
				if int(time.perf_counter() - time_start) >= float(t.value):
					self.close = True
					self.d.streamStop()
					self.d.close()
					self.d = u6.U6()
					dataCount = 0
				if dataCount == 0:
					dataCount +=1
				else:
					a.clear()
					self.Bx2 = str(sum(r['AIN3'])/len(r['AIN3']) * FG2_V_to_muT)
					self.By2 = str(sum(r['AIN4'])/len(r['AIN4']) * FG2_V_to_muT)
					self.Bz2 = str(sum(r['AIN5'])/len(r['AIN5']) * FG2_V_to_muT)
					self.Bx = str(sum(r['AIN0'])/len(r['AIN0']) * FG1_V_to_muT)
					self.By = str(sum(r['AIN1'])/len(r['AIN1']) * FG1_V_to_muT)
					self.Bz = str(sum(r['AIN2'])/len(r['AIN2']) * FG1_V_to_muT)
					Bx_text.value = self.Bx[:5]
					By_text.value = self.By[:5]
					Bz_text.value = self.Bz[:5]
					self.Bxs = np.append(self.Bxs, float(self.Bx))
					self.Bys = np.append(self.Bys, float(self.By))
					self.Bzs = np.append(self.Bzs, float(self.Bz))
					self.Bxs2 = np.append(self.Bxs2, float(self.Bx2))
					self.Bys2 = np.append(self.Bys2, float(self.By2))
					self.Bzs2 = np.append(self.Bzs2, float(self.Bz2))
					self.t = np.append(self.t, datetime.now())
					dataCount += 1
					#Plot the Live Graph
					#Read which axis to plot first
					if self.plot_x == True:
						a.plot(self.t, self.Bxs, label = 'Bx', color = 'blue')
						error_x = u * self.Bxs
						#a.fill_between(self.t, self.Bxs + error_x, self.Bxs - error_x, color = 'cyan', zorder = 1)
					if self.plot_y == True:
						a.plot(self.t, self.Bys, label = 'By', color = 'purple')
						error_y = u * self.Bys
						#a.fill_between(self.t, self.Bys + error_y, self.Bys - error_y, color = 'salmon', zorder = 1)
					if self.plot_z == True:
						a.plot(self.t, self.Bzs, label = 'Bz', color = 'steelblue')						
						error_z = u * self.Bzs
						#a.fill_between(self.t, self.Bzs + error_z, self.Bzs - error_z, color = 'greenyellow', zorder = 1)
					if self.plot_x2 == True:
						a.plot(self.t, self.Bxs2, label = 'Bx-2', color= 'red')
						error_x2 = u * self.Bxs2
						#a.fill_between(self.t, self.Bxs2 + error_x2, self.Bxs2 - error_x2, color = 'coral', zorder = 1)
					if self.plot_y2 == True:
						a.plot(self.t, self.Bys2, label = 'By-2', color = 'darkorange')
						error_y2 = u * self.Bys2
						#a.fill_between(self.t, self.Bys2 + error_y2, self.Bys2 - error_y2, color = 'lightgreen', zorder = 1)
					if self.plot_z2 == True:
						a.plot(self.t, self.Bzs2, label = 'Bz-2', color = 'violet')
						error_z2 = u * self.Bzs2
						#a.fill_between(self.t, self.Bzs2 + error_z2, self.Bzs2 - error_z2, color = 'plum', zorder = 1)
					a.set_xlabel('Time')
					a.set_ylabel('B-field (\u03BC T)')
					a.legend()
					plt.setp(a.get_xticklabels(), rotation = 20, horizontalalignment = 'right')
					canvas.draw()
					app.update()

	def run_indefinite(self):
		# Scan frequency at 5 kHz
		SCAN_FREQUENCY = 5000
		#Applying proper calibration to reading
		self.d.getCalibrationData()
		self.d.streamConfig(NumChannels=6, ChannelNumbers = [0, 1, 2, 3, 4, 5], ChannelOptions = [0, 0, 0, 0, 0, 0], SettlingFactor = 1, ResolutionIndex=1, ScanFrequency=SCAN_FREQUENCY)
		self.close = False
		
		#set the right scaling to uT for the given model
		if FG1_scale.value=='mag-03':
			FG1_V_to_muT = V_to_muT_mag_03MSL100
		elif FG1_scale.value=='mag-690-1000':
			FG1_V_to_muT = V_to_muT_mag_690_FL1000
		else: 
			FG1_V_to_muT = V_to_muT_mag_690_FL500
			
		if FG2_scale.value=='mag-03':
			FG2_V_to_muT = V_to_muT_mag_03MSL100
		elif FG2_scale.value=='mag-690-1000':
			FG2_V_to_muT = V_to_muT_mag_690_FL1000
		else:
			FG2_V_to_muT = V_to_muT_mag_690_FL500
			
			
		print(FG2_V_to_muT)

		if self.d is None:
			self.Bx = 'empty'
			self.By = 'empty'
			self.Bz = 'empty'
			self.Bx2 = 'empty'
			self.By2 = 'empty'
			self.Bz2 = 'empty'
		self.d.streamStart()
		start = datetime.now()

		time_start = time.perf_counter()
		missed = 0
		dataCount = 0
		packetCount = 0
		for r in self.d.streamData():
			if r is not None :
				if dataCount < 2:
					dataCount +=1
				else:
					a.clear()
					self.Bx2 = str(sum(r['AIN3'])/len(r['AIN3']) * FG2_V_to_muT)
					self.By2 = str(sum(r['AIN4'])/len(r['AIN4']) * FG2_V_to_muT)
					self.Bz2 = str(sum(r['AIN5'])/len(r['AIN5']) * FG2_V_to_muT)
					self.Bx = str(sum(r['AIN0'])/len(r['AIN0']) * FG1_V_to_muT)
					self.By = str(sum(r['AIN1'])/len(r['AIN1']) * FG1_V_to_muT)
					self.Bz = str(sum(r['AIN2'])/len(r['AIN2']) * FG1_V_to_muT)
					Bx_text.value = self.Bx[:5]
					By_text.value = self.By[:5]
					Bz_text.value = self.Bz[:5]
					self.Bxs = np.append(self.Bxs, float(self.Bx))
					self.Bys = np.append(self.Bys, float(self.By))
					self.Bzs = np.append(self.Bzs, float(self.Bz))
					self.Bxs2 = np.append(self.Bxs2, float(self.Bx2))
					self.Bys2 = np.append(self.Bys2, float(self.By2))
					self.Bzs2 = np.append(self.Bzs2, float(self.Bz2))
					self.t = np.append(self.t, datetime.now())
					dataCount += 1
					#Plot the Live Graph
					#Read which axis to plot first
					if self.plot_x == True:
						a.plot(self.t, self.Bxs, label = 'Bx', color = 'blue')
						error_x = u * self.Bxs
						#a.fill_between(self.t, self.Bxs + error_x, self.Bxs - error_x, color = 'cyan', zorder = 1)
					if self.plot_y == True:
						a.plot(self.t, self.Bys, label = 'By', color = 'purple')
						error_y = u * self.Bys
						#a.fill_between(self.t, self.Bys + error_y, self.Bys - error_y, color = 'salmon', zorder = 1)
					if self.plot_z == True:
						a.plot(self.t, self.Bzs, label = 'Bz', color = 'steelblue')						
						error_z = u * self.Bzs
						#a.fill_between(self.t, self.Bzs + error_z, self.Bzs - error_z, color = 'greenyellow', zorder = 1)
					if self.plot_x2 == True:
						a.plot(self.t, self.Bxs2, label = 'Bx-2', color= 'red')
						error_x2 = u * self.Bxs2
						#a.fill_between(self.t, self.Bxs2 + error_x2, self.Bxs2 - error_x2, color = 'coral', zorder = 1)
					if self.plot_y2 == True:
						a.plot(self.t, self.Bys2, label = 'By-2', color = 'darkorange')
						error_y2 = u * self.Bys2
						#a.fill_between(self.t, self.Bys2 + error_y2, self.Bys2 - error_y2, color = 'lightgreen', zorder = 1)
					if self.plot_z2 == True:
						a.plot(self.t, self.Bzs2, label = 'Bz-2', color = 'violet')
						error_z2 = u * self.Bzs2
						#a.fill_between(self.t, self.Bzs2 + error_z2, self.Bzs2 - error_z2, color = 'plum', zorder = 1)
					a.set_xlabel('Time')
					a.set_ylabel('B-field (\u03BC T)')
					a.legend()
					plt.setp(a.get_xticklabels(), rotation = 20, horizontalalignment = 'right')
					canvas.draw()
					app.update()


	def terminate(self):
		self.Bxs = []
		self.Bys = []
		self.Bzs = []
		self.Bxs2 = []
		self.Bys2 = []
		self.Bzs2 = []
		self.t = []
		self.dis = []
		a.clear()
		canvas.draw()
		app.update()
		self.close = True
		self.d.streamStop()
		self.d.close()
		self.d = u6.U6()
		t.value = 0
		
	def stop_plot(self):
		self.close = True
		self.d.streamStop()
		self.d.close()
		self.d = u6.U6()
		

	def close_app(self):
		if self.close == False:
			self.d.streamStop()
			self.d.close()
			app.destroy()
			quit()
		else:
			app.destroy()
			quit()

#Matplotlib Stuff
f = Figure(figsize=(8,6), dpi = 100, layout = 'constrained')
a = f.add_subplot(111)


#GuiZero Stuff
read = Read()
app = App(title = 'Live B-field Readout', layout = 'grid', width = 1300, height = 1200)
message_x = Text(app, text = 'Bx: ', grid = [0,0])
Bx_text = Text(app, text = read.Bx, grid = [1, 0])
message_y = Text(app, text = 'By: ', grid = [0,1])
By_text = Text(app, text = read.By, grid = [1, 1])
message_z = Text(app, text = 'Bz: ', grid = [0,2])
Bz_text= Text(app, text = read.Bz, grid = [1, 2])
microT2 = Text(app, text = '\u03BC T', grid = [2, 0], align = 'left')
microT1 = Text(app, text = '\u03BC T', grid = [2, 1], align = 'left')
microT3 = Text(app, text = '\u03BC T', grid = [2, 2], align = 'left')

Fluxgate_Box = Box(app, layout = 'grid', grid = [0, 3, 8, 1], border = True, align = 'left')
FG_text = Text(Fluxgate_Box, text = 'Fluxgate 1 Serial No. : ', grid = [0, 0])
#FG1_choice = Combo(Fluxgate_Box, options = ['2122', '2325'], grid = [1, 0])
FG1_choice = TextBox(Fluxgate_Box, width = 8, grid = [1,0], align = 'left')
FG2_text = Text(Fluxgate_Box, text = 'Fluxgate 2 Serial No. : ', grid = [0, 1])
#FG2_choice = Combo(Fluxgate_Box, options = ['2122', '2325'], grid = [1,1]) 
FG2_choice = TextBox(Fluxgate_Box, width = 8, grid = [1,1], align = 'left')

FluxgateScaling_Box = Box(app, layout = 'grid', grid = [2, 3, 8, 1], border = True, align = 'left')
scale_text = Text(FluxgateScaling_Box, text = 'Fluxgate 1 model : ', grid = [0, 0])
FG1_scale = Combo(FluxgateScaling_Box, options = ['mag-03', 'mag-690-500', 'mag-690-1000'], grid = [1, 0])
scale2_text = Text(FluxgateScaling_Box, text = 'Fluxgate 2 model : ', grid = [0, 1])
FG2_scale = Combo(FluxgateScaling_Box, options = ['mag-03', 'mag-690-500', 'mag-690-1000'], grid = [1,1]) 

Setting_Box = Box(app, layout = 'grid', grid = [4, 3, 9, 1], border = True, align = 'left')
Which_axis = Text(Setting_Box, text = 'Fluxgate 1 axis:', grid = [0, 0])
xaxis = CheckBox(Setting_Box, text = 'x-axis', grid = [1, 0], command = read.set_x)
yaxis = CheckBox(Setting_Box, text = 'y-axis', grid = [2, 0], command = read.set_y)
zaxis = CheckBox(Setting_Box, text = 'z-axis', grid = [3, 0], command = read.set_z)
Which_axis2 = Text(Setting_Box, text = 'Fluxgate 2 axis:', grid = [0, 1], align = 'left')
xaxis2 = CheckBox(Setting_Box, text = 'x-axis', grid = [1, 1], command = read.set_x2)
yaxis2 = CheckBox(Setting_Box, text = 'y-axis', grid = [2, 1], command = read.set_y2)
zaxis2 = CheckBox(Setting_Box, text = 'z-axis', grid = [3, 1], command = read.set_z2)
plot_box = Box(app, layout = 'grid', border = True, grid = [0, 5, 5, 1], align = 'left')
t = TextBox(plot_box, width = 7, grid = [1, 0])
time_text = Text(plot_box, text = 'Time(s)', grid = [0, 0])
Update = PushButton(plot_box, command = read.scan, text = 'Update', grid = [2, 0])
long_box = Box(app, layout = 'grid', grid = [0, 6, 5, 1], border = True, align = 'left')
indefinite_run = Text(long_box, text = 'Indefinite Run', grid = [0, 0])
long_run = PushButton(long_box, command = read.run_indefinite, text = 'Run', grid = [1, 0])
long_term = PushButton(long_box, command = read.terminate, text = 'Terminate', grid = [3, 0])
long_stop = PushButton(long_box, command = read.stop_plot, text = 'Stop', grid = [2, 0])
#Move tray at same time
Move_Box = Box(app, layout = 'grid', grid = [8, 8], border = True, align = 'left')
message = Text(Move_Box, text = "Type distance in box", grid = [0, 0], align = 'left')
distance = TextBox(Move_Box, width = 10, grid = [1, 0], align = 'left', text = '0')
cm_text = Text(Move_Box, text = 'cm', grid = [2, 0], align = 'left')
f_or_b = Text(Move_Box, text = 'Move motor forwards or backwards?', grid = [0, 1], align = 'left')
f_or_b_choice = Combo(Move_Box, options = ['Forward', 'Backward'], grid = [1,1], align = 'left')
which = Text(Move_Box, text = 'Move tray or fluxgate?', grid = [0, 2], align = 'left')
which_motor = Combo(Move_Box, options = ['Tray', 'Fluxgate'], grid = [1, 2], align = 'left')
update_dist = PushButton(Move_Box, text='Enter', grid = [1, 3],command = read.change_dist, align = 'left')

#Fit Buttons
Fit_box = Box(app, layout = 'grid', grid = [0, 9, 5, 1], border = True, align = 'left')
Fitting_Text = Text(Fit_box, text = 'For fitting data to equation', grid = [0,0], align = 'left')
Create_Fit = PushButton(Fit_box, command = read.fit_input, text = 'Create', grid = [1,0], align = 'left')
eq_text = Text(Fit_box, text = 'Equation f(x): ', grid = [0,1], align = 'left')
equation = TextBox(Fit_box, width = 20, grid = [1, 1], align = 'left')
par_text = Text(Fit_box, text = 'Type params, comma-space delimited (, )', grid = [0, 2], align = 'left')
params = TextBox(Fit_box, width = 20, grid = [1, 2], align = 'left')
axis = Text(Fit_box, text = 'Which axis to fit?', grid = [0, 3], align = 'left')
axis_choose = Combo(Fit_box, options = ['Bx-1', 'By-1', 'Bz-1', 'Bx-2', 'By-2', 'Bz-2'], grid = [1, 3], align = 'left')
save_text = Text(Fit_box, text = 'Saved Figure Name: ', grid = [0, 4], align = 'left')
name_fig = TextBox(Fit_box, width = 30, grid = [1,4], align = 'left')
#Save  buttons
Save_box = Box(app, layout = 'grid', grid = [0, 10, 5, 1], border = True)
fig_title = Text(Save_box, text = 'Run Name', grid = [0, 0])
f_title = TextBox(Save_box, width = 40, grid = [1, 0, 3, 1], align = 'left')
create = PushButton(Save_box, command = read.save, text = 'Create', grid = [4, 0])
term = PushButton(Save_box, command = read.terminate, text = 'Terminate', grid = [5, 0])
Experimenters = Text(Save_box, text = 'Who Ran the Experiment?', grid = [0, 1])
names = TextBox(Save_box, width = 20, grid = [1, 1], align = 'left')
Range = Text(Save_box, text = 'FG Range (\u03BC T): ', grid = [0, 2])
FG_RANGE = TextBox(Save_box, width = 7, grid = [1, 2], align = 'left')
Comment_Box = Text(Save_box, text = 'Coments: ', grid = [0, 3], align = 'left')
Comment = TextBox(Save_box, width = 40, grid = [1, 3], align = 'left')


#Closing the app
app.when_closed = read.close_app

# Make a special tkinter canvas that works with matplotlib
# and add it to app.tk (i.e. the tk widget hidden inside the guizero App)
canvas = FigureCanvasTkAgg(f, app.tk)
canvas.draw()
canvas.get_tk_widget().grid(row = 7, column = 0, columnspan = 6)
canvas._tkcanvas.grid(row = 8, column = 0, columnspan = 6)


app.display()
