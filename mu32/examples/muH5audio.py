# muH5play.py python program example for MegaMicro Mu32 transceiver 
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
Play H5 file on audio port

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
from mu32.core import logging, log
from mu32.core_h5 import MuH5


log.setLevel( logging.INFO )

event = threading.Event()

OUTPUT_DEVICE = 2				# Audio Device
BLOCKSIZE = 512					# Number of stereo samples per block.
SAMPLING_FREQUENCY = 10000		# this is the max frequency
MEMS = (4, 7)					# the two Mu32 antenna microphones used
MEMS_NUMBER = len( MEMS )
DURATION = 0					# Time recording in seconds. 0 means infinite acquisition loop: use Ctrl C for stopping
DEFAULT_FILENAME = './'

muH5:MuH5 = None

def main():

    global muH5

    """
    run the Mu32 system during one second for getting and ploting signals comming from
    the 8 activated microphones  
    """
    print( welcome_msg )

    parser = argparse.ArgumentParser()
    parser.add_argument( "-f", "--filename", help=f"set the server H5 filename or directory to play. Default is {DEFAULT_FILENAME}" )
    parser.add_argument( "-d", "--device", help="set the audio output device (use 'python -m sounddevice' to get available devices)")
    filename = DEFAULT_FILENAME
    device = OUTPUT_DEVICE
    args = parser.parse_args()
    if args.device:
        device = int( args.device )
        print( f"output audio device set to {device}" )
    if args.filename:
        filename = args.filename           

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
            muH5 = MuH5( filename )
            muH5.run( 
                mems=MEMS,							
                duration=DURATION,
                sampling_frequency=SAMPLING_FREQUENCY,
                buffer_length=BLOCKSIZE,
                post_callback_fn=callback_end,
            )
            event.wait()  # Wait until playback is finished

    except Exception as e:
        print( 'error:', e )
    except:
        print( 'Unexpected error:', sys.exc_info()[0] )


def callback_play( outdata, frames, time, status ):
    """
    User-supplied function to generate audio data in response to requests from the active stream. 
    When the stream is running, PortAudio calls this stream callback periodically. 
    It is responsible for processing and filling output buffer.
    """
    global muH5

    if status.output_underflow:
        print( 'Output underflow: increase blocksize?' )
        raise sd.CallbackAbort

    try:
        data = muH5.signal_q.get() * muH5.sensibility
        data = data.astype( np.float32 ).T
    except queue.Empty as e:
        print(' Buffer is empty: increase buffersize?' )
        raise sd.CallbackAbort from e

    outdata[:] = data


def callback_end( muH5: MuH5 ):
	"""
	set event for stopping the audio playing loop
	"""
	log.info( ' .stop playing audio' )
	event.set()


if __name__ == "__main__":
	main()