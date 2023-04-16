# mu256run.py python program example for MegaMicro Mu32 receiver 
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
Run the Mu256 system during one second for getting and ploting signals comming from
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
from mu32.core import Mu256, logging, log

MEMS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
#MEMS = (0, 1, 2, 3)
ANALOGS = (0,)
#ANALOGS = ()

DURATION = 5
BUFFER_LENGTH = 512
BUFFERS_NUMBER = 8
SAMPLING_FREQUENCY = 50000

log.setLevel( logging.INFO )

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument( "-d", "--duration", help=f"set the recording duration. Default is {DURATION}" )
	parser.add_argument( "-l", "--buffer_length", help=f"set the buffer length. Default is {BUFFER_LENGTH}" )
	parser.add_argument( "-c", "--buffers_number", help=f"set the buffers number (>=2). Default is {BUFFERS_NUMBER}" )
	parser.add_argument( "-s", "--sampling_frequency", help=f"set the sampling frequency. Default is {SAMPLING_FREQUENCY}" )
	args = parser.parse_args()
	duration = DURATION
	buffer_length = BUFFER_LENGTH
	buffers_number = BUFFERS_NUMBER
	sampling_frequency = SAMPLING_FREQUENCY
	if args.duration:
		duration = int( args.duration )
	if args.buffer_length:
		buffer_length = int( args.buffer_length )
	if args.buffers_number:
		buffers_number = int( args.buffers_number )
	if args.sampling_frequency:
		sampling_frequency = int( args.sampling_frequency )

	print( welcome_msg )


	try:
		mu = Mu256()
		mu.run( 
			mems=MEMS,									# activated mems
			duration=duration,
            analogs=ANALOGS,
			counter_skip = False,
			buffer_length=buffer_length,
			buffers_number=buffers_number,
			sampling_frequency=sampling_frequency,
			start_trig = True                           # external trig signal flag
		)

		mu.wait()
		draw_mems_signals( mu )

	except Exception as e:
		print( 'aborting: ', e )



def draw_mems_signals( mu: Mu256 ):
	
    """
    get queued signals from Mu256
    """
    signal = mu.signal_q.get()
    while not mu.signal_q.empty():
        signal = np.append( signal, mu.signal_q.get(), axis=1 )

    print( 'mems_number=', mu.mems_number )
    print( 'channels_number=', mu.channels_number )
    print( 'analog_number=', mu.analogs_number )

    channels_number = mu.channels_number

    """
    plot mems signals (multiplot or simple plot)
    """
    time = np.array( range( np.size(signal,1) ) )/mu.sampling_frequency
    if channels_number > 1:
        fig, axs = plt.subplots( channels_number )
        fig.suptitle('Mems activity')	
        for s in range( channels_number ):
            axs[s].plot( time, signal[s,:] * mu.sensibility )
            axs[s].set( xlabel='time in seconds', ylabel='mic %d' % s )
            if s==channels_number-1:
                axs[s].plot( time, signal[s,:] )
    else:
        plt.plot( time, signal[0,:] )
        plt.xlabel( 'time in seconds' )
        plt.ylabel( f"microphone {mu.mems[0]}" )

    plt.show()




if __name__ == "__main__":
	main()