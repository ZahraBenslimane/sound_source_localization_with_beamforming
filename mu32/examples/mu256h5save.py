# mu256h5save.py python program example for MegaMicro Mu32 transceiver 
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
Run Mu32 receiver and save data to H5 file in MegaMicro format

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install h5py
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 save program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


import argparse
import sys
import numpy as np
import queue
import h5py
from mu32.core import Mu256, logging, mu32log, Mu32Exception


MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
ANALOGICS = (0,)
DURATION = 1
OUTPUT = './'

mu32log.setLevel( logging.INFO )

signal_q = queue.Queue()

def main():
    """
    run the Mu32 system during one second for getting signals comming from
    the 8 activated microphones  
    """

    parser = argparse.ArgumentParser()
    parser.add_argument( "-o", "--output", help=f"set the server H5 output directory. Default is {OUTPUT}" )
    parser.add_argument( "-d", "--duration", help=f"set the duration in seconds. Default is {DURATION}s" )

    args = parser.parse_args()
    output = OUTPUT
    duration = DURATION
    if args.output:
        output = args.output
    if args.duration:
        duration = int( args.duration )

    print( welcome_msg )


    try:
        mu = Mu256()
        mu.run(
            mems=MEMS,                # activated mems
            analogs=ANALOGICS,        # activated analogic channels
            duration=duration,        # recording time
            h5_recording=True,        # H5 recording
            h5_rootdir=output,        # directory where to save file
            counter_skip=False
        )

        if duration == 0:
            input( 'Press the [Return] key for quitting...' )
        
        mu.stop()
        mu.wait()


    except Exception as e:
        print( str (e ) )



if __name__ == "__main__":
	main()