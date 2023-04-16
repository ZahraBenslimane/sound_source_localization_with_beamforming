# mu32wav.py python program example for MegaMicro Mu32 transceiver 
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
Run the Mu32 system during some seconds and records signals comming from
2 activated microphones.

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
    > pip install matplotlib
    > pip install sounddevice
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 wav program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import wave
import sounddevice as sd
import matplotlib.pyplot as plt
from mu32.core import Mu32, logging, mu32log

MEMS = (0, 7)
DURATION = 1
WAV_FILENAME = 'test.wav'

mu32log.setLevel( logging.INFO )

def main():

    parser = argparse.ArgumentParser()
    parser.parse_args()
    print( welcome_msg )
    
    try:
        mu32 = Mu32()
        mu32.run(
		    post_callback_fn=my_callback_end_function, 	# the user defined data processing function
		    mems=MEMS,                                # activated mems
            duration=DURATION                         # recording time
        )
    except Exception as e:
        print( str( e ) )


def my_callback_end_function( mu32: Mu32 ):
    """
    get queued signals from Mu32 and save them in wavfile
    """
    
    with  wave.open( WAV_FILENAME, mode='wb' ) as wavfile:
        wavfile.setnchannels(2)
        wavfile.setsampwidth(2)
        wavfile.setframerate( mu32.sampling_frequency )

        while not mu32.signal_q.empty():
            signal = mu32.signal_q.get() >> 4
            wavfile.writeframesraw( np.int16( np.reshape( signal, np.size( signal ), order='F' ) ) )    

if __name__ == "__main__":
	main()