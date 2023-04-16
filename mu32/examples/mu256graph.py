# mu256graph.py python program example for MegaMicro Mu32 transceiver 
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
Run the Mu32 system during one second for getting and ploting signals comming from
8 activated microphones. Use pyqtgraph.

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install pyqt6 pyqtgraph
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
#from mu32.core import Mu32, Mu256, logging, mu32log
from mu32.core import Mu256, logging, log


MEMS = [i for i in range(8)]
ANALOGS = (0,)
#ANALOGS = ()

DURATION = 5
BUFFER_LENGTH = 512
BUFFERS_NUMBER = 8
SAMPLING_FREQUENCY = 50000

log.setLevel( logging.INFO )

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument( "-d", "--duration", help=f"set the recording duration. Default is {DURATION}" )
	parser.add_argument( "-l", "--buffer_length", help=f"set the buffer length. Default is {BUFFER_LENGTH}" )
	parser.add_argument( "-c", "--buffers_number", help=f"set the buffers number (>=2). Default is {BUFFERS_NUMBER}" )
	parser.add_argument( "-s", "--sampling_frequency", help=f"set the sampling frequency. Default is {SAMPLING_FREQUENCY}" )
	args = parser.parse_args()
	duration = DURATION
	buffer_length = BUFFER_LENGTH
	buffers_number = BUFFERS_NUMBER
	sampling_frequency = SAMPLING_FREQUENCY
	if args.duration:
		duration = int( args.duration )
	if args.buffer_length:
		buffer_length = int( args.buffer_length )
	if args.buffers_number:
		buffers_number = int( args.buffers_number )
	if args.sampling_frequency:
		sampling_frequency = int( args.sampling_frequency )


	print( welcome_msg )



	"""
	Init graph
	"""
	win = pg.GraphicsLayoutWidget(show=True, title="Mu32 example: Plotting")
	win.resize(1000,900)
	win.setWindowTitle('Mu32 example: Plotting')
	pg.setConfigOptions(antialias=True)
	graph = win.addPlot(title="Microphones")
	graph.setYRange(-5,5, padding=0, update = False)
	curves = []
	for s in range( len( MEMS ) + 2 ):
		curves.append( graph.plot(pen='y' ) )

	timer = QtCore.QTimer()
	timer.timeout.connect( lambda: plot_on_the_fly( mu32, curves ) )	

	"""
	start Mu32 acquisition
	"""
	try:
		mu32 = Mu256()
		mu32.run( 
			mems=MEMS,									# activated mems
			duration=duration,
            analogs=ANALOGS,
			counter_skip = False,
			buffer_length=buffer_length,
			buffers_number=buffers_number,
			sampling_frequency=sampling_frequency,
			start_trig = True,                           # external trig signal flag
            status = True
		)

		timer.start( 10 )

		input( 'Press a key to stop...' )
		mu32.stop()

	except Exception as e:
		print( 'aborting: ', e )



def plot_on_the_fly( mu32, curves ):
    """
    get last queued signal and plot it
    """
    try:
        data = mu32.signal_q.get_nowait()
    except queue.Empty:
        return

    t = np.arange( np.size( data, 1 ) )/mu32.sampling_frequency
    for s in range( mu32.channels_number ):
        curves[s].setData( t, ( data[s,:] * mu32.sensibility ) + s - mu32.channels_number/2 )

	


if __name__ == "__main__":
	main()

