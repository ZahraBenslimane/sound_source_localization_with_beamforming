# mu32wsscheduler.py python program example for MegaMicro Mu32 receiver 
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
Example of job scheduling on Mu32 server.
Schedule a job to be executed by Mu32 server, then list scheduled jobs, then remove from stack the first scheduled job

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
from pprint import pprint
from re import T
from time import sleep
from datetime import datetime, timedelta
import numpy as np
from mu32.core import logging, Mu32ws, log

MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
DURATION = 1
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8002
DEFAULT_START_TIME = 1
DEFAULT_DURATION = 3
DEFAULT_REPEAT_DELAY = 5

#log.setLevel( logging.INFO )

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-n", "--nip", help=f"set the server network ip address. Default is {DEFAULT_IP}" )
    parser.add_argument( "-p", "--port", help=f"set the server listening port. Default is {DEFAULT_PORT}" )
    parser.add_argument( "-t", "--start", help=f"set the start time in seconds. Default is {DEFAULT_START_TIME}" )
    parser.add_argument( "-d", "--duration", help=f"set the duration in seconds. Default is {DEFAULT_DURATION}s" )

    args = parser.parse_args()
    nip = DEFAULT_IP
    port = DEFAULT_PORT
    start_time = DEFAULT_START_TIME
    duration = DEFAULT_DURATION
    if args.nip:
        nip = args.nip
    if args.port:
        port = args.port
    if args.start:
        start_time = int( args.start )
    if args.duration:
        duration = int( args.duration )

    print( welcome_msg )

    start_datetime = datetime.now() + timedelta( seconds=start_time )
    try:

        """
        Schedule a job
        """
        mu32 = Mu32ws( remote_ip=nip, remote_port=port )
        mu32.scheduler( 
            command = 'prun',                                                   # the job to do
            start_datetime = start_datetime,                                    # starting time
            stop_datetime = start_datetime +  timedelta( seconds=duration ),    # starting time
            repeat_delay = DEFAULT_REPEAT_DELAY,
            parameters = {
                'mems': MEMS,                       # activated MEMs
                'sampling_frequency': 50000,        # sampling frequency
                'cv_monitoring': True
            }
        )
        print( 'server response: ', mu32.response )

        """
        List scheduled jobs
        """
        jobs = mu32.scheduler( command = 'lsjob' ).response
        pprint( jobs )

        """
        Wait for job execution
        """
        print( 'Waiting for job execution...' )
        sleep( start_time + duration ) 

        """
        Remove first job from stack
        """        
        task_id = jobs['response'][0]['task_id']
        print( f"Removing job [{task_id}]..." )

        mu32.scheduler( 
            command = 'rmjob',
            parameters = {'task_id': task_id}
        )
        print( 'server response for removing: ', mu32.response )
        
        """
        List new job's list after removing
        """
        jobs = mu32.scheduler( command = 'lsjob' ).response
        pprint( jobs )

	
    except Exception as e:
        print( 'aborting: ', e )
        raise






if __name__ == "__main__":
	main()