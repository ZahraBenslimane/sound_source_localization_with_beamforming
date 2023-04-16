# mu32play.py python program example for MegaMicro Mu32 transceiver 
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
	> pip install sounddevice

The default output device used (OUTPUT_DEVICE) is the device number 2. 
But it can be the one you want. You can obtain the device list by typing :
	python3 -m sounddevice
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 play program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
from mu32.core import Mu32, logging, mu32log, Mu32Exception

mu32log.setLevel( logging.INFO )

event = threading.Event()
signal_q = queue.Queue()

OUTPUT_DEVICE = 2				# Audio Device
BLOCKSIZE = 256					# Number of stereo samples per block.
BUFFER_NUMBER = 4				# USB tarnsfer buffer number. should be at least equal to two
SAMPLING_FREQUENCY = 50000		# this is the max frequency
MEMS = (0, 7)					# the two Mu32 antenna microphones used
MEMS_NUMBER = len( MEMS )
DURATION = 0					# Time recording in seconds. 0 means infinite acquisition loop: use Ctrl C for stopping


def main():
	"""
	run the Mu32 system during one second for getting and ploting signals comming from
	the 8 activated microphones  
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument( "-d", "--device", help="set the audio output device (use 'python -m sounddevice' to get available devices)")
	args = parser.parse_args()
	if args.device:
		device = args.device
		print( f"output audio device set to {device}" )
	else:
		device = int( OUTPUT_DEVICE )

	print( welcome_msg )

	try:
		stream = sd.OutputStream(
			samplerate=SAMPLING_FREQUENCY,
			blocksize=BLOCKSIZE,
			device=device, 
			channels=MEMS_NUMBER, 
			dtype='float32',
			callback=callback_play,
			finished_callback=event.set
		)
	except Exception as e:
		print( 'Unexpected error:', sys.exc_info()[0] )
		print( e )
		exit()

	print('Starting Playback ...')
	try:
		with stream:
			mu32 = Mu32()
			mu32.run( 
				mems=MEMS,							
	            duration=DURATION,
				sampling_frequency=SAMPLING_FREQUENCY,
				buffer_length=BLOCKSIZE,
				buffers_number=BUFFER_NUMBER,
				callback_fn=callback_read,
				post_callback_fn=callback_end,
				block=True
			)
			event.wait()  # Wait until playback is finished
	except Mu32Exception as e:
		print( 'aborting: ', e )
	except ( KeyboardInterrupt, SystemExit ):	
		print( 'Program was interrupted' )
	except TypeError as err:
		print( 'TypeError error:', err )
	except:
		print( 'Unexpected error:', sys.exc_info()[0] )


def callback_read( mu32: Mu32, data: np.ndarray ):
	"""
	user callback function for data processing:
	convert data from 24 to 16 bits format and put it in the external queue
	"""
	global signal_q
	data *= mu32.sensibility
	signal_q.put( data.astype( np.float32 ) )

def callback_play( outdata, frames, time, status ):
	"""
	callback function for playing signal:
	get the signal from queue and send it to the audio device
	"""
	outdata[:] = signal_q.get().T

def callback_play_safe( outdata, frames, time, status ):
	"""
	callback function for playing signals with some additional controls
	"""
	if status.output_underflow:
		print( 'Output underflow: increase blocksize?' )
		raise sd.CallbackAbort

	try:
		data = signal_q.get().T
	except queue.Empty as e:
		print(' Buffer is empty: increase buffersize?' )
		raise sd.CallbackAbort from e

	if len( data ) < len( outdata ):
		outdata[:len(data)] = data
		outdata[len( data ):].fill(0)
		raise sd.CallbackStop
	else:
		outdata[:] = data


def callback_end( mu32: Mu32 ):
	"""
	set event for stopping the audio playing loop
	"""
	mu32log.info( ' .stop playing audio' )
	event.set()


if __name__ == "__main__":
	main()