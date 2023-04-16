# mu32power.py python program example for MegaMicro Mu32 transceiver 
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
8 activated microphones 

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 power program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import queue
import matplotlib.pyplot as plt
from mu32.core import Mu32, logging, mu32log

mu32log.setLevel( logging.INFO )

"""
Power signal queue
"""
power_q = queue.Queue()


def main():

	parser = argparse.ArgumentParser()
	parser.parse_args()
	print( welcome_msg )

	try:
		mu32 = Mu32()
		mu32.run( 
			mems=(0, 1, 2, 3),							# activated mems
			post_callback_fn=my_process_function, 		# the user defined data processing function
			callback_fn=my_callback_fn
		)
	except Exception as e:
		print( 'aborting: ', e )


def my_callback_fn( mu32: Mu32, data ):
	"""
	Compute energy (mean power) on transfered frame and push it in the queue
	"""	
	signal = data * mu32.sensibility
	mean_power = np.sum( signal**2, axis=1 ) / mu32.buffer_length

	power_q.put( mean_power )


def my_process_function( mu32: Mu32 ):

	"""
	get queued signals from Mu32
	"""
	q_size = power_q.qsize()
	power = power_q.get()
	while not power_q.empty():
		power = np.append( power, power_q.get() )
	power = np.reshape( power, (q_size, mu32.mems_number) ).T

	"""
	plot mems signals 
	"""
	fig, axs = plt.subplots( mu32.mems_number )
	fig.suptitle('Mems energy')
	time = np.array( range( np.size(power,1) ) ) / mu32.sampling_frequency
	
	for s in range( mu32.mems_number ):
		axs[s].plot( time, power[s,:] )
		axs[s].set( xlabel='time in seconds', ylabel='mic %d' % s )

	plt.show()



if __name__ == "__main__":
	main()