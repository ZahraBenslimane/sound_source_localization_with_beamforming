# muH5play.py python program example for MegaMicro Mu32 receiver 
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
Read H5 files with MuH5 class object

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
import queue
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from mu32.core import logging, log
from mu32.core_h5 import MuH5

MEMS = (4, 7)
DURATION = 1
DEFAULT_FILENAME = './'
DEFAULT_START_TIME = 0
DEFAULT_DURATION = 1
COUNTER_SKIP = True

log.setLevel( logging.INFO )

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-f", "--filename", help=f"set the server H5 filename or directory to play. Default is {DEFAULT_FILENAME}" )
    parser.add_argument( "-t", "--start", help=f"set the start time in seconds. Default is {DEFAULT_START_TIME}" )
    parser.add_argument( "-d", "--duration", help=f"set the duration in seconds. Default is {DEFAULT_DURATION}s" )

    args = parser.parse_args()
    filename = DEFAULT_FILENAME
    start_time = DEFAULT_START_TIME
    duration = DEFAULT_DURATION
    if args.filename:
        filename = args.filename
    if args.start:
        start_time = args.start
    if args.duration:
        duration = int( args.duration )

    print( welcome_msg )

    """
    Init graph
    """
    win = pg.GraphicsLayoutWidget(show=True, title="MuH5 example: Plotting")
    win.resize(1000,600)
    win.setWindowTitle('MuH5 example: Plotting')
    pg.setConfigOptions(antialias=True)
    graph = win.addPlot(title="Microphones")
    graph.setYRange(-5,5, padding=0, update = False)
    curves = []
    for s in range( len( MEMS ) + int( not COUNTER_SKIP ) ):
        curves.append( graph.plot(pen='y' ) )

    timer = QtCore.QTimer()
    timer.timeout.connect( lambda: plot_on_the_fly( muH5, curves ) )	

    try:
        muH5 = MuH5( filename )
        parameters = muH5.parameters

        print( 'Available mems are: ', parameters[filename]['mems'] )
        print( 'Duration (s): ', parameters[filename]['duration'] )
        print( 'Sampling frequency is (Hz): ', parameters[filename]['sampling_frequency'] )

        muH5.run( 
            mems=MEMS,                      # activated MEMs
            duration=duration,              # ask for DURATION seconds acquisition
            counter_skip=COUNTER_SKIP
        )

        timer.start( 10 )

        if duration == 0:
            input( 'Press [Return] key to stop...' )
            muH5.stop()

        muH5.wait()

    except Exception as e:
        print( 'aborting: ', e )
        raise


def plot_on_the_fly( mu32, curves ):
	"""
	get last queued signal and plot it
	"""
	try:
		data = mu32.signal_q.get_nowait()
	except queue.Empty:
		return

	t = np.arange( np.size( data, 1 ) )/mu32.sampling_frequency
	for s in range( mu32.mems_number + int( not COUNTER_SKIP ) ):
		curves[s].setData( t, ( data[s,:] * mu32.sensibility ) + s - mu32.channels_number/2 )



if __name__ == "__main__":
	main()