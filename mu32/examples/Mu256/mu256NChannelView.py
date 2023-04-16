# mu256NChannelView.py python program example for MegaMicro Mu32 transceiver 
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
from mu32.core import Mu256, logging, mu32log


#MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
MEMS = range( 128 )              # MEMS = range(256)
DURATION = 0                    # 0 = infinite duration
BLOCKSIZE = 2048				# Number of samples per block.
BUFFER_NUMBER = 4				# USB transfer buffer number. should be at least equal to two
SAMPLING_FREQUENCY = 50000		# this is the max frequency
QUEUE_SIZE = 1                  # queue max size (if > 0: buffers comming when size is exceeded are lost (weak latency). If 0: no size. Latency can occure)


mu32log.setLevel( logging.INFO )


def main():

    parser = argparse.ArgumentParser()
    parser.parse_args()
    print( welcome_msg )

    """
    Init graph
    """
    curves = []
    win = init_graph( curves )

    """
    Init graph timer and set display callback function
    """
    timer = QtCore.QTimer()
    timer.timeout.connect( lambda: display( mu256, curves ) )

    """
    start Mu32 acquisition
    """
    try:
        mu256 = Mu256()
        mu256.run( 
            mems=MEMS,
            duration=DURATION,
            sampling_frequency=SAMPLING_FREQUENCY,
            buffer_length=BLOCKSIZE,
            buffers_number=BUFFER_NUMBER,
            callback_fn=None,
            post_callback_fn=None,
            queue_size = QUEUE_SIZE
        )

        timer.start( 10 )

        input( 'Press a key to stop...' )
        mu256.stop()
        mu256.wait()

    except Exception as e:
        print( 'aborting: ', e )



def display( mu256: Mu256, curves: list ):
	"""
	get last queued signal and plot it
	"""
	try:
		data = mu256.signal_q.get_nowait()
	except queue.Empty:
		return

	t = np.arange( np.size( data, 1 ) )/mu256.sampling_frequency
	for s in range( mu256.mems_number ):
		curves[s].setData( t, ( data[s,:] * mu256.sensibility ) + s - mu256.mems_number/2 )


def init_graph( curves: list ):
    """
    Init graph
    """
    mems_number = len( MEMS )
    win = pg.GraphicsLayoutWidget(show=True, title="Mu256 example: Plotting")
    win.resize(1000,1500)
    win.setWindowTitle('Mu32 example: Plotting')
    pg.setConfigOptions(antialias=True)
    graph = win.addPlot(title="Microphones")
    graph.setYRange(-mems_number/2,+mems_number/2, padding=0, update = False)
    for s in range( mems_number ):
        curves.append( graph.plot(pen='y' ) )

    return win



if __name__ == "__main__":
	main()

