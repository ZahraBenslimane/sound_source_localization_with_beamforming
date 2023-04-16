# muH5check.py python program example for MegaMicro Mu32 transceiver 
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
Check H5 file

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
from mu32.core import logging, log
from mu32.core_h5 import MuH5


#log.setLevel( logging.INFO )

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
    filename = DEFAULT_FILENAME
    args = parser.parse_args()
    if args.filename:
        filename = args.filename           

    print('Starting H5 check ...')
    try:
        muH5 = MuH5( filename )
        muH5.run()

    except Exception as e:
        print( 'error:', e )
    except:
        print( 'Unexpected error:', sys.exc_info()[0] )


if __name__ == "__main__":
	main()