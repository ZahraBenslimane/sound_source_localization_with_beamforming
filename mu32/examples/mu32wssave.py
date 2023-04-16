# mu32wssave.py python program example for MegaMicro Mu32 receiver 
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
Run the Mu32 remote receiver during some seconds and ask server to save data in H5 file

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
import matplotlib.pyplot as plt
from mu32.core import logging, Mu32ws, log

#MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
MEMS = list( range(32) )
DURATION = 20
#DEFAULT_IP = '127.0.0.1'
DEFAULT_IP = '192.168.0.44'
DEFAULT_PORT = 8002

log.setLevel( logging.INFO )

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument( "-n", "--dest", help=f"set the server network ip address. Default is {DEFAULT_IP}" )
	parser.add_argument( "-p", "--port", help=f"set the server listening port. Default is {DEFAULT_PORT}" )
	parser.add_argument( "-d", "--duration", help=f"set the recording duration Default is {DURATION}" )
	args = parser.parse_args()
	dest = DEFAULT_IP
	port = DEFAULT_PORT
	duration = DURATION
	if args.dest:
		dest = args.dest
	if args.port:
		port = args.port
	if args.duration:
		duration = int( args.duration )

	print( welcome_msg )

	try:
		mu32 = Mu32ws( remote_ip=dest, remote_port=port )
		mu32.run( 
			mems=MEMS,									
			duration=duration,
            h5_recording=True,              # perform data H5 recording
			#h5_rootdir = '/Volumes/SSD4/Dépots/distalsense/Mu32',
            h5_pass_through=True,           # ask the server to perform H5 recording
			cv_monitoring=True,       		# do video monitoring
			cv_device=0,	         		# device where to found camera 
			cv_file_duration=10
		)

		mu32.wait()
	
	except Exception as e:
		print( 'aborting: ', e )

if __name__ == "__main__":
	main()

