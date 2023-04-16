# mu32ctrlboard.py control board python program for MegaMicro 
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
Control Megamicro device dataflow. 
Can work both on usb dataflow, websocket network stream or H5 file stream

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install sounddevice
    > pip install pyqt6 pyqtgraph

For dev purpose: 
    > pip install pyqt6-tools

To know your output sound device: 
    > python3 -m sounddevice
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 play program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


import pyqtgraph as pg
from PyQt6 import QtWidgets, uic, QtCore
from pyqtgraph import PlotWidget, plot
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.dockarea.Dock import Dock
import sys  # We need sys so that we can pass argv to QApplication
import argparse
import threading
import queue
import h5py
import numpy as np
import sounddevice as sd
from mu32.exception import MuException
from mu32.core import log, logging
from mu32.core_h5 import MuH5

DEBUG_MODE = False
DEFAULT_OUTPUT_DEVICE = 2   				# Audio Device
BLOCKSIZE = 2048					        # Number of stereo samples per block.

DEFAULT_WIDTH = 2000
DEFAULT_HEIGHT = 1000
DEFAULT_LEFT_PANEL_WIDTH = 150
DEFAULT_RIGHT_PANEL_WIDTH = DEFAULT_WIDTH - DEFAULT_LEFT_PANEL_WIDTH

log.setLevel( logging.INFO )

class MegaMicroControlBoard( QtWidgets.QMainWindow  ):

    __muH5: MuH5 = None
    __sd_stream: sd.OutputStream = None
    __sd_event: threading.Event = None

    _sd_device = DEFAULT_OUTPUT_DEVICE

    __gr_area: DockArea = None
    __gr_dock_left: Dock = None
    __gr_dock_right: Dock = None
    __gr_plot_widget: PlotWidget = None
    __gr_plot_widget_curve = None

    _gr_width = DEFAULT_WIDTH
    _gr_height = DEFAULT_HEIGHT
    _gr_dock_left_width = DEFAULT_LEFT_PANEL_WIDTH
    _gr_dock_right_width = DEFAULT_RIGHT_PANEL_WIDTH

    __h5_current_filename: str = ''
    __h5_current_file: h5py.File = None
    __h5_current_group: h5py.Group = None
    __h5_dataset_index: int = 0
    __h5_parameters: dict = {}

    _h5_duration: int = 0
    _h5_sampling_frequency: float = 0.
    _h5_mems: list = ()
    _h5_dataset_number: int = 0
    _h5_dataset_length: int = 0
    _h5_dataset_duration: float = 0.0

    __h5_playing: bool = False

    def __init__(self, *args, **kwargs):
        #super( MegaMicroControlBoard, self ).__init__( *args, **kwargs )
        super( MegaMicroControlBoard, self ).__init__()

        log.info( 'Starting MegaMicro controler Board' )
        self._init_graph( 'Python control board for MegaMicro' )
        self._create_dock_left()
        self._create_dock_right()

        if 'device' in kwargs and kwargs.get( 'device' ) != None:
            self._sd_device = kwargs.get( 'device' )
        
        log.info( f" .Set audio output device {self._sd_device}" )



    def _init_graph( self, title='Python control board for MegaMicro' ):

        ## Switch to using white background and black foreground
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'w')

        self.__gr_area = DockArea()
        self.setCentralWidget( self.__gr_area )
        self.resize( self._gr_width, self._gr_height )
        #self.setAutoFillBackground(True)
        self.setWindowTitle( title )
        #self.setDockOptions()
        log.info( f" .Graph initialized" )


    def _create_dock_left( self ):

        log.info( f" .Create left dock" )
        self.__gr_dock_left = Dock( "Fichiers H5", size=( self._gr_dock_left_width, 400 ), closable=False )
        self.__gr_area.addDock( self.__gr_dock_left, 'left')  

        """
        Left side layout Widget
        """
        w1 = pg.LayoutWidget()
        self.__gr_dock_left.addWidget( w1 )

        """
        Add H5 file ploting button
        """
        H5VisualizeBtn = QtWidgets.QPushButton('Select H5 file')
        H5VisualizeBtn.clicked.connect( self.onH5Visualize )
        w1.addWidget( H5VisualizeBtn, row=1, col=0 )

        """
        Add H5 file playing button
        """
        H5PlayBtn = QtWidgets.QPushButton('Play H5 file')
        H5PlayBtn.clicked.connect( self.onH5Play )
        w1.addWidget( H5PlayBtn, row=2, col=0 )

        """
        Add H5 file playing stop button
        """
        H5PlayStopBtn = QtWidgets.QPushButton('Stop playing H5 file')
        H5PlayStopBtn.clicked.connect( self.onH5PlayStop )
        w1.addWidget( H5PlayStopBtn, row=3, col=0 )

        """
        Add select signal button
        """
        H5SelectBtn = QtWidgets.QPushButton('Select signal')
        H5SelectBtn.clicked.connect( self.onSelect )
        w1.addWidget( H5SelectBtn, row=4, col=0 )
        
        """
        Add application exit() button
        """
        ExitBtn = QtWidgets.QPushButton('Quitter')
        ExitBtn.clicked.connect( self.onExit)
        w1.addWidget( ExitBtn, row=5, col=0 )


    def onSelect( self ):
        """
        Select file blocks
        """
        if self.__h5_current_file==None:
            log.warning( 'Cannot select: no H5 file loaded. Please load a H5 file before select parts of signal' )
            return
        
        signal = MuH5( self.__h5_current_filename ).signal
        print( 'signal = ', np.shape( signal ) )



    def _create_dock_right( self ):

        """
        Docke d2
        """
        log.info( f" .Create right dock" )
        self.__gr_dock_right = Dock( "Visuel", size=( self._gr_dock_right_width, 400 ), closable=True )
        self.__gr_area.addDock( self.__gr_dock_right, 'right', self.__gr_dock_left )    # place __gr_dock_right at right edge of dock area


    def onH5Play( self ):
        """
        Play H5 file
        """

        if self.__h5_current_file==None:
            log.warning( 'Cannot play: no H5 file loaded. Please load a H5 file before playing' )
            return

        """
        Set the plot figure on right widget
        """
        if self.__gr_dock_right != None:
            """
            Remove current dock if any and recreate one
            """
            self.__gr_dock_right.close()
            self.__gr_dock_right = Dock( "Visuel", size=( self._gr_dock_right_width, 400 ), closable=True )
            self.__gr_area.addDock( self.__gr_dock_right, 'right', self.__gr_dock_left ) 

        self.__gr_dock_right.hideTitleBar()
        self.__gr_plot_widget = pg.PlotWidget( title="H5 content" )
        self.__gr_plot_widget.enableAutoRange( 'xy', False )
        self.__gr_plot_widget.setLimits( yMin=-2, yMax=2 )
        self.__gr_plot_widget.setYRange( -2, 2 )
        self.__gr_plot_widget_curve = self.__gr_plot_widget.plot( pen='y' )
        self.__gr_dock_right.addWidget( self.__gr_plot_widget )

        """
        Set the audio stream
        """
        try:
            """
            Open the output audio stream
            """
            self.__sd_event = threading.Event()
            self.__sd_stream = sd.OutputStream(
                samplerate=self._h5_sampling_frequency,
                blocksize=BLOCKSIZE,
                device=self._sd_device, 
                channels=2, 
                dtype='float32',
                callback=self.onH5Play_callback_play,
                finished_callback=self.__sd_event.set
            )
        except Exception as e:
            log.warning( f"Output audio stream opening failed: {e}" )
            return
        except:
            log.critical( f"Unexpected error: {sys.exc_info()[0]}" )
            return           

        try:
            self.__sd_stream.start()
            self.__muH5 = MuH5( self.__h5_current_filename )
            self.__muH5.run( 
                mems=(3, 7),
                duration=0,
                sampling_frequency=self._h5_sampling_frequency,
                buffer_length=BLOCKSIZE,
                post_callback_fn=self.onH5Play_callback_end,
            )
#            self.__h5_play_event.wait()  # Wait until playback is finished
#            self.__sd_stream.stop()
#            self.__sd_stream.close()
#            self.__sd_stream = None

            """
            with stream:
                self.__muH5 = MuH5( self.__h5_current_filename )
                self.__muH5.run( 
                    mems=(3, 7),
                    duration=10,
                    sampling_frequency=self._h5_sampling_frequency,
                    buffer_length=BLOCKSIZE,
                    post_callback_fn=self.onH5Play_callback_end,
                )
                self.__h5_play_event.wait()  # Wait until playback is finished
"""
        except MuException as e:
            log.warning( f"H5 input-output stream failed: {e}" )
            return
        except Exception as e:
            log.warning( f"Input-output stream failed: {e}" )
            return
        except:
            log.critical( f"Unexpected error: {sys.exc_info()[0]}" )
            return            


    def onH5PlayStop( self ):
        """
        Stop a current playing H5 file
        """
        if self.__muH5 != None and self.__muH5.is_alive():
            """
            Stop MuH5 if running
            Note that if an audio stream is running with, it will be also closed
            """
            self.__muH5.stop()
            self.__muH5.wait()
            self.__muH5 = None


        #index = self.__h5_dataset_index
        #self.__h5_playing = True
        #while self.__h5_playing and index < self._h5_dataset_number:
        #    dataset = np.array( self.__h5_current_file['muh5/' + str( self.__h5_dataset_index ) + '/sig'][:] )


    def onH5Play_callback_play( self, outdata, frames, time, status ):
        """
        Generate audio data in response to requests from the active stream. 
        When the stream is running, PortAudio calls this stream callback periodically. 
        It is responsible for processing and filling output buffer.
        """

        if status.output_underflow:
            print( 'Output underflow: increase blocksize?' )
            raise sd.CallbackAbort

        try:
            data = self.__muH5.signal_q.get() * self.__muH5.sensibility
        except queue.Empty as e:
            print(' Buffer is empty: increase buffersize?' )
            raise sd.CallbackAbort from e

        #datasound = data * self.__muH5.sensibility
        #datasound = datasound.astype( np.float32 ).T
        #outdata[:] = datasound
        outdata[:] = data.astype( np.float32 ).T

        self.__gr_plot_widget_curve.setData( data[0,:] )



    def onH5Play_callback_end( self, muH5: MuH5 ):
        """
        set event for stopping the audio playing loop
        """
        log.info( ' .stop playing audio' )
        self.__sd_stream.stop()
        self.__sd_stream.close()
        self.__sd_stream = None
        #self.__sd_event.set()


    def onH5Visualize( self ):
        """
        Upload H5 file
        """

        if self.__h5_current_filename != '' and self.__h5_current_file != None:
            """
            Close current H5 file if any
            """
            self.__h5_current_file.close()
            self.__h5_current_file = None
            self.__h5_current_group = None
            self.__h5_current_filename = ''

            """
            Close right widget
            !TO DO
            """
            pass

        #self.__h5_current_filename = QtWidgets.QFileDialog.getOpenFileName(None, "Open", "", "H5 Files (*.h5)")[0]
        [self.__h5_current_filename, _] = QtWidgets.QFileDialog.getOpenFileName(None, "", "", "*.h5")
        if self.__h5_current_filename != '':
            #self.lineEdit.setText(self.file_name[0])
            try:
                """
                get H5 parameters from H5 file
                """
                self.__h5_current_file = h5py.File( self.__h5_current_filename, 'r' )
                self.__h5_current_group = self.__h5_current_file['muh5']
                self.__h5_parameters = dict( zip( self.__h5_current_group.attrs.keys(), self.__h5_current_group.attrs.values() ) )

                self._h5_duration = self.__h5_parameters['duration']
                self._h5_dataset_number = self.__h5_parameters['dataset_number']
                self._h5_sampling_frequency = self.__h5_parameters['sampling_frequency']
                self._h5_mems = list( self.__h5_parameters['mems'] )
                self._h5_dataset_length = self.__h5_parameters['dataset_length']
                self._h5_dataset_duration = self.__h5_parameters['dataset_duration']

                log.info( f" .Loading H5 file {self.__h5_current_filename}" )
                log.info( f" .Duration: {self._h5_duration}" )
                log.info( f" .{self._h5_dataset_number} dataset(s) ({self._h5_dataset_duration}s duration and {self._h5_dataset_length} samples each)" )
                log.info( f" .Sampling frequency: {self._h5_sampling_frequency/1000}kHz" )
                log.info( f" .{len( self._h5_mems)} available mems: {self._h5_mems}" )

            except Exception as e:
                self.__h5_current_file.close()
                self.__h5_current_file = None
                self.__h5_current_group = None
                self.__h5_current_filename = ''
                log.error( f"{self.__h5_current_filename} H5 file upload failed: {e}" )
                return           

            """
            Init
            """
            if self.__gr_dock_right != None:
                """
                Remove current dock if any and recreate one
                """
                self.__gr_dock_right.close()
                self.__gr_dock_right = Dock( "Visuel", size=( self._gr_dock_right_width, 400 ), closable=True )
                self.__gr_area.addDock( self.__gr_dock_right, 'right', self.__gr_dock_left ) 

            self.__h5_dataset_index = 0
            dataset = np.array( self.__h5_current_file['muh5/' + str( self.__h5_dataset_index ) + '/sig'][:] )

            self.__gr_dock_right.hideTitleBar()
            widget = pg.PlotWidget( title="H5 content" )
            widget.plot( dataset[1,:] )
            self.__gr_dock_right.addWidget( widget )

            



    def onExit( self ):

        if self.__h5_current_filename != '' and self.__h5_current_file != None:
            """
            Close current H5 file if any
            """
            self.__h5_current_file.close()
            self.__h5_current_file = None
            self.__h5_current_group = None
            self.__h5_current_filename = ''

        if self.__muH5 != None:
            """
            Stop MuH5 if running
            Note that if an audio stream is running with, it will be also closed
            """
            if self.__muH5.is_alive():
                self.__muH5.stop()
                self.__muH5.wait()
            self.__muH5 = None

        if self.__sd_stream != None:
            """
            An audio stream seems running -> stop it:
            """
            self.__sd_stream.stop()
            self.__sd_stream.close()
            self.__sd_stream = None

        log.info( 'Exit from Megamicro controler board' )
        exit()




def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-d", "--device", help="set the audio output device (use 'python -m sounddevice' to get available devices)")
    device = None
    args = parser.parse_args()
    if args.device:
        device = int( args.device )
 
    try:
        app = QtWidgets.QApplication( sys.argv )
        mu32ctrlboard = MegaMicroControlBoard( device=device )
        mu32ctrlboard.show()
    except Exception as e:
        if DEBUG_MODE:
            raise e

    sys.exit( app.exec() )



if __name__ == '__main__':
    main()

