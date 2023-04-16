# mu32run.py python program example for MegaMicro Mu32 receiver 
#
# Copyright (c) 2022 DistalSense
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

welcome_msg = '-'*20 + '\n' + 'Mu32 run program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mu32.core import Mu32, logging, log

MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
DURATION = 10

log.setLevel( logging.INFO )

def main():

	parser = argparse.ArgumentParser()
	parser.parse_args()
	print( welcome_msg )

	try:
		mu32 = Mu32()
		mu32.run( 
			mems=MEMS,									# activated mems
			duration=DURATION,
		)

		mu32.wait()
		draw_mems_signals( mu32 )

	except Exception as e:
		print( 'aborting: ', e )



def draw_mems_signals( mu32: Mu32 ):
	
	"""
	get queued signals from Mu32
	"""
	signal = mu32.signal_q.get()
	while not mu32.signal_q.empty():
		signal = np.append( signal, mu32.signal_q.get(), axis=1 )

	"""
	plot mems signals (multiplot or silple plot)
	"""
	time = np.array( range( np.size(signal,1) ) )/mu32.sampling_frequency
	if mu32.mems_number > 1:
		fig, axs = plt.subplots( mu32.mems_number )
		fig.suptitle('Mems activity')	
		for s in range( mu32.mems_number ):
			axs[s].plot( time, signal[s,:] * mu32.sensibility )
			axs[s].set( xlabel='time in seconds', ylabel='mic %d' % s )
	else:
		plt.plot( time, signal[0,:] )
		plt.xlabel( 'time in seconds' )
		plt.ylabel( f"microphone {mu32.mems[0]}" )

	plt.show()




if __name__ == "__main__":
	main()
