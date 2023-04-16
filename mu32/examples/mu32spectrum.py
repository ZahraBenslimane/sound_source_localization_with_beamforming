# mu32autotest.py python program example for MegaMicro Mu32 transceiver 
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
Run the Mu32 system during one second for getting and ploting signals spectrum comming from
4 activated microphones.

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 spectrum program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mu32.core import Mu32, logging, mu32log

mu32log.setLevel( logging.INFO )

MEMS=(0, 1, 2, 3)
MEMS_NUMBER = len( MEMS )
DURATION = 0
BUFFER_NUMBER = 4
BUFFER_LENGTH = 1024
SAMPLING_FREQUENCY = 22050

plt.ion()                                       # Turn the interactive mode on.
fig, axs = plt.subplots( MEMS_NUMBER )          # init figure with MEMS_NUMBVER subplots
fig.suptitle('Mems signals')

def main():

	parser = argparse.ArgumentParser()
	parser.parse_args()
	print( welcome_msg )

	try:
		mu32 = Mu32()
		mu32.run( 
			mems=MEMS,                          # activated mems
            duration=DURATION,
			sampling_frequency=SAMPLING_FREQUENCY,
			buffer_length=BUFFER_LENGTH,
			buffers_number=BUFFER_NUMBER,
			callback_fn=my_callback_fn
		)

	except Exception as e:
		print( str( e ) )


def my_callback_fn( mu32: Mu32, data ):
	"""
	Plot signals comming from the Mu32 receiver	
	"""

	pwfft = np.zeros( ( mu32.mems_number, int( mu32.buffer_length/2 )+1 ) )
	
	for i in range( mu32.mems_number ):
		pwfft[i,:] = np.square( np.abs( np.fft.rfft( data[i,:] ) ) )

	frequency = np.linspace( 0, mu32.sampling_frequency/2, np.size(pwfft, 1) )

	for s in range( MEMS_NUMBER ):
		X = pwfft[s,:]
		axs[s].plot( frequency, X )

	plt.show()
	plt.pause( 10**-10 )




if __name__ == "__main__":
	main()