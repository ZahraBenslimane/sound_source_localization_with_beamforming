# mu32doa.py python DOA Delay and Sum program example for MegaMicro Mu32 transceiver 
#
# Copyright (c) 2022 Distalsense
# Author: bruno.gas@distalsense.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 Direction Of Arrival (DOA) program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mu32.core import Mu32, mu32log, logging, Mu32Exception
from mu32 import beamformer 

BUFFER_NUMBER = 4				# USB tarnsfer buffer number. should be at least equal to two
SAMPLING_FREQUENCY = 50000		# this is the max frequency
MEMS = (0, 1, 2, 3, 4, 5, 6, 7) # the two Mu32 antenna microphones used
MEMS_NUMBER = len( MEMS )
INTER_MICS = 0.045				# distance between microphones in meters
DURATION = 0					# Time recording in seconds. 0 means infinite acquisition loop: use Ctrl C for stopping
BUFFER_LENGTH = 512				# USB tranfert buffer samples count. Corresponding duration should be greater than BFWIN_DURATON  
BUFFERS_NUMBER = 4				# Number of USB buffer transfert
BEAMS_NUMBER = 8				# Preformed beams number 
BFWIN_DURATION = 0.01			# Time length for RTFD computing windows 
GAIN = 5						# Amplification gain on power for plotting

mu32log.setLevel( logging.INFO )

G: any							# preformed beams
bars: any						# graph object for polar bar plotting


def main():
	"""
	run the Mu32 and compute DOA in realtime and plot beam's mean energy on a polar bar graph.
	"""
	
	global G, bars

	parser = argparse.ArgumentParser()
	parser.parse_args()
	print( welcome_msg )

	# init beamformer
	antenna=[[0, 0, 0], MEMS_NUMBER, 0, INTER_MICS]
	G = beamformer.das_former( antenna, BEAMS_NUMBER, sf=SAMPLING_FREQUENCY, bfwin_duration=BFWIN_DURATION )

	bars = init_graph()
	input("Press a key to start...")

	try:
		mu32 = Mu32()
		mu32.run( 
			callback_fn=callback_bfm, 	# the user defined data processing function
			mems=MEMS,					# activated mems	
			duration = DURATION,
			buffer_length = BUFFER_LENGTH,
			buffers_number = BUFFERS_NUMBER,
			block=True,
		)
	except Mu32Exception as e:
		print( 'aborting' )
	except ( KeyboardInterrupt, SystemExit ):	
		print( 'Program was interrupted' )
	except:
		print( 'Unexpected error:', sys.exc_info()[0] )


def callback_bfm( mu32: Mu32, data: np.ndarray ):
	"""
	user callback function for data beamforming:
	"""
	global bars, G

	powers, beams_number = beamformer.das_doa( 
		G,
		data * mu32.sensibility,
		sf=SAMPLING_FREQUENCY, 
		bfwin_duration=BFWIN_DURATION 
	)

	"""
	Plot first energy frame for each beam 
	"""
	for power, bar in zip( powers[:,0], bars ):
		bar.set_height( power * GAIN )
	plt.pause( 1e-10 )


def init_graph():
	"""
	Initialize polar bar graph 
	"""

	plt.ion()
	fig = plt.figure( 1, clear = True )
	axes_coords = [0., 0., 1., 1.]
	ax_polar = fig.add_axes(axes_coords, projection = 'polar', label='ax_polar')
	ax_polar.set_ylim(0, 1)
	ax_polar.set_xlim(0, np.pi)
	radii = np.zeros( ( BEAMS_NUMBER, ) )
	width = np.pi/BEAMS_NUMBER*np.ones( ( BEAMS_NUMBER, ) )
	bars = ax_polar.bar( np.linspace(0, np.pi, BEAMS_NUMBER), radii, width=width, bottom=0.0, alpha = 1, facecolor='r', edgecolor='k')

	return bars


if __name__ == "__main__":
	main()