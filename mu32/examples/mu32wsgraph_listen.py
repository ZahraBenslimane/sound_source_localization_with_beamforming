# mu32wsgraph_listen.py python program example for MegaMicro Mu32 transceiver 
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
Connect to a Mu32 remote system for getting and ploting signals comming from it. 
Use pyqtgraph.

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install pyqt6 pyqtgraph
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 mu32wsgraph_watch program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
import numpy as np
import queue
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from mu32.core import logging, Mu32ws, log


MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
DURATION = 0
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 8002
H5_RECORDING = False

log.setLevel( logging.INFO )

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument( "-i", "--ip", help=f"set the server network ip address. Default is {DEFAULT_IP}" )
	parser.add_argument( "-p", "--port", help=f"set the server listening port. Default is {DEFAULT_PORT}" )
	parser.add_argument( "-D", "--duration", help=f"set the duration. Default is {DURATION}" )
	args = parser.parse_args()
	ip = DEFAULT_IP
	port = DEFAULT_PORT
	duration = DURATION
	if args.ip:
		ip = args.ip
	if args.port:
		port = args.port
	if args.duration:
		duration = int( args.duration )

	print( welcome_msg )
	print( f"IP server is set to {ip}:{port}" )

	"""
	Init graph
	"""
	win = pg.GraphicsLayoutWidget(show=True, title="Mu32 example: Plotting")
	win.resize(1000,600)
	win.setWindowTitle('Mu32 example: Plotting')
	pg.setConfigOptions(antialias=True)
	graph = win.addPlot(title="Microphones")
	graph.setYRange(-5,5, padding=0, update = False)
	curves = []
	for s in range( len( MEMS ) ):
		curves.append( graph.plot(pen='y' ) )

	timer = QtCore.QTimer()
	timer.timeout.connect( lambda: plot_on_the_fly( mu32, curves ) )	

	"""
	start Mu32 acquisition
	"""
	try:
		mu32 = Mu32ws( remote_ip=ip, remote_port=port )
		mu32.listen( 
			mems=MEMS,
			duration=duration,
			h5_recording=H5_RECORDING,
            counter=False,
            counter_skip=False
		)

		timer.start( 10 )

		input( "Press [Return] key to stop...\n" )
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
	for s in range( mu32.mems_number ):
		curves[s].setData( t, ( data[s,:] * mu32.sensibility ) + s - mu32.mems_number/2 )

	


if __name__ == "__main__":
	main()

