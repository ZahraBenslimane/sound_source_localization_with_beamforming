# mu32plot.py python program example for MegaMicro Mu32 transceiver 
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
Run the Mu32 system during one second for getting and ploting signals comming from
4 activated microphones  

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 plot program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mu32.core import Mu32, logging, mu32log

mu32log.setLevel( logging.INFO )

MEMS=(0, 1, 2, 3,)
MEMS_NUMBER = len( MEMS )
DURATION = 1


plt.ion()                                       		# Turn the interactive mode on.
fig, axs = plt.subplots( MEMS_NUMBER + 1 )        		# init figure with MEMS_NUMBER subplots + COUNTER ctrl signal
fig.suptitle('Mems signals')

signal = None


def main():

	parser = argparse.ArgumentParser()
	parser.parse_args()
	print( welcome_msg )

	try:
		mu32 = Mu32()
		mu32.run( 
			mems=MEMS,                          # activated mems
			counter_skip=False,					# get counter channel
            duration=DURATION,
			callback_fn=my_callback_fn,
			post_callback_fn=my_callback_end_function
		)
	except Exception as e:
		print( 'aborting: ', e )


def my_callback_fn( mu32: Mu32, data ):
	"""
	Plot signals comming from the Mu32 receiver
	"""
	global signal

	time = np.array( [t for t in range( mu32.buffer_length )] ) / mu32.sampling_frequency
	for s in range( mu32.channels_number ):
		axs[s].cla()
		axs[s].plot( time, data[s,:] )
	
	if signal is None:
		signal  = data
	else:
		signal = np.append( signal, data, axis=1 )

	plt.pause( 0.000001 )



def my_callback_end_function( mu32: Mu32 ):

	global signal

	time = np.array( range( np.size( signal, 1 ) ) )/mu32.sampling_frequency
	if mu32.channels_number > 1:
		"""
		draw multiplot
		"""
		fig, axs = plt.subplots( mu32.channels_number )
		fig.suptitle('Mems activity')
	
		for s in range( mu32.channels_number ):
			if s==0:
				# counter channel
				axs[s].plot( time, signal[s,:] )
			else:
				axs[s].plot( time, signal[s,:]*mu32.sensibility )
			axs[s].set( xlabel='time in seconds', ylabel='mic %d' % s )
	else:
		"""
		draw simple plot
		"""
		plt.plot( time, signal[0,:]*mu32.sensibility )
		plt.xlabel( 'time in seconds' )
		plt.ylabel( f"microphone {mu32.mems[0]}" )

	plt.show()
	input( "Pres a key..." )





if __name__ == "__main__":
	main()