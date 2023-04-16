# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import pyqtgraph as pg
from multiprocessing import Process, Manager, Queue
import sched, time, threading
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt
import queue
import threading
sys.path.append('./mu32')
from mu32.core import Mu32, Mu32Exception, mu32log
import multiprocessing as mp
import time

mu32log.setLevel( logging.INFO )

event = threading.Event()
signal_q = queue.Queue()

BLOCKSIZE = 2048				# Number of samples per block.
BUFFER_NUMBER = 4				# USB transfer buffer number. should be at least equal to two
SAMPLING_FREQUENCY = 50000		# this is the max frequency
MEMS = range(32)					# the two Mu32 antenna microphones used
MEMS_NUMBER = len( MEMS )
DURATION = 0					# Time re
# This function is responsible for displaying the data
# it is run in its own process to liberate main process
def display(name,q):
    app = QtWidgets.QApplication([])

    win = pg.GraphicsWindow(title="Basic plotting examples")
    win.resize(1000,600)
    win.setWindowTitle('pyqtgraph example: Plotting')
    
    graph = win.addPlot(title="Updating plot")
    graph.setYRange(-2**20,2**20, padding=0, update = False)
    curve = graph.plot(pen='y')

    x_np = []
    y_np = []

    def updateInProc(curve,q,x,y):
        item = q.get()
        x = item[0]
        y = item[1][:,0]
        curve.setData(x,y)

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: updateInProc(curve,q,x_np,y_np))
    timer.start(1)

    QtWidgets.QApplication.instance().exec_()

# This is function is responsible for reading some data (IO, serial port, etc)
# and forwarding it to the display
# it is run in a thread
def io(running,q):
    t = 0
    while running.is_set():
        s = mu32.signal_q.get().reshape( mu32.buffer_length, mu32.mems_number) 
        t = np.arange(len(s))
        q.put([t,s])
        time.sleep(0.0001)
    print("Done")

def callback_end( mu32: Mu32 ):
	"""
	set event for stopping the audio playing loop
	"""
	mu32log.info( ' .stop' )
	event.set()

if __name__ == '__main__':
    q = Queue()
    # Event for stopping the IO thread
    run = threading.Event()
    run.set()

    # Run io function in a thread
    t = threading.Thread(target=io, args=(run,q))
    t.start()


    # Start display process
    p = Process(target=display, args=('bob',q))
    p.start()

    try :
        mu32 = Mu32()
        mu32.run( 
                    mems=MEMS,							
                    duration=DURATION,
                    sampling_frequency=SAMPLING_FREQUENCY,
                    buffer_length=BLOCKSIZE,
                    buffers_number=BUFFER_NUMBER,
                    callback_fn=None,
                    post_callback_fn=callback_end
                )
    except Mu32Exception as e:
        print( 'aborting' )
    except ( KeyboardInterrupt, SystemExit ):
        print( 'Program was interrupted' )
    except TypeError as err:
        print( 'TypeError error:', err )
    except:
        print( 'Unexpected error:', sys.exc_info()[0] )



    input("See ? Main process immediately free ! Type any key to quit.")
    run.clear()
    print("Waiting for scheduler thread to join...")
    t.join()
    print("Waiting for graph window process to join...")
    p.join()
    print("Process joined successfully. C YA !")
