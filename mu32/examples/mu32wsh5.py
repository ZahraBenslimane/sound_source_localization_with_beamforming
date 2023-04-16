# mu32wsh5.py python program example for MegaMicro Mu32 receiver 
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
Set H5 file parameters on remote server

Documentation is available on https://beameo.io

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
from mu32.core import logging, Mu32ws, log

MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
DURATION = 10
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8002

log.setLevel( logging.INFO )

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-d", "--dest", help=f"set the server network ip address. Default is {DEFAULT_IP}" )
    parser.add_argument( "-p", "--port", help=f"set the server listening port. Default is {DEFAULT_PORT}" )
    args = parser.parse_args()
    dest = DEFAULT_IP
    port = DEFAULT_PORT
    if args.dest:
        dest = args.dest
    if args.port:
        port = args.port

    print( welcome_msg )

    try:
        mu32 = Mu32ws( remote_ip=dest, remote_port=port )
        mu32.h5( 
            command='h5ls',									
        )

        print( 'ls: ', mu32.response )

        print( 'h5pwd:', mu32.h5( command='h5pwd' ).response )
        print( 'h5cwd:', mu32.h5( command='h5cwd' ).response )
        #print( 'h5cd:', mu32.h5( command='h5cd', parameters={'path':'/Volumes/SSD4/Dépots/distalsense'} ).response )
        print( 'h5pwd:', mu32.h5( command='h5pwd' ).response )
        print( 'h5ls:', mu32.h5( command='h5ls' ).response )
        #print( 'h5get:', mu32.h5( command='h5get', parameters={'filename':'mu5h-20220617-233318.h5'} ).response )

        print( 'h5ls:', mu32.h5( command='*ls' ).response )
        print( 'h5get video:', mu32.h5( command='h5get', parameters={'filename':'muVideo-20220616-224448.mp4'} ).response )

    except Exception as e:
        print( 'aborting: ', e )

if __name__ == "__main__":
	main()
