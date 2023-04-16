# mu32save.py python program example for MegaMicro Mu32 transceiver 
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
from mu32.core import Mu32, logging, mu32log, Mu32Exception

MEMS                = (0, 7)
H5_FILENAME         = 'mytestfile.hdf5'


mu32log.setLevel( logging.INFO )

signal_q = queue.Queue()

def main():
    """
    run the Mu32 system during one second for getting signals comming from
    the 8 activated microphones  
    """

    parser = argparse.ArgumentParser()
    parser.parse_args()
    print( welcome_msg )

    try:
        mu32 = Mu32()
        mu32.run(
            post_callback_fn=my_h5saving_function,  # the user H5 saving function
            mems=MEMS,                              # activated mems
            duration=1                              # recording time
        )

    except Exception as e:
        print( str (e ) )


def my_h5saving_function( mu32: Mu32 ):
    """
    get queued signals from Mu32
    """
    q_size = mu32.signal_q.qsize()
    if q_size== 0:
        raise Exception( 'No received data !' )
    signal = mu32.signal_q.get()
    while not mu32.signal_q.empty():
        signal = np.append( signal, mu32.signal_q.get(), axis=1 )

    """
    Open hdf5 file, write data and add some usefull attributes
    """
    with h5py.File( H5_FILENAME, "w" ) as f:
        # craeta the data set:
#        dataset = f.create_dataset( "mydataset", ( mu32.buffer_length * q_size, mu32.mems_number ), dtype='int32' )
        dataset = f.create_dataset( "mydataset", ( mu32.mems_number, np.size(signal, 1) ), dtype='int32' )

        # write data:
        dataset[:] = signal

        # write attributes:
        dataset.attrs['sampling_frequency'] = mu32.sampling_frequency
        dataset.attrs['microphones_number'] = mu32.mems_number


if __name__ == "__main__":
	main()