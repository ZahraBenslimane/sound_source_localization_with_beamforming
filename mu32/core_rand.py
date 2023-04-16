# mu32.core_h5.py python program interface for MegaMicro Mu32 transceiver 
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
Mu32 documentation is available on https://distalsense.io
See documentation on usb device programming with libusb on https://pypi.org/project/libusb1/1.3.0/#documentation
Examples are available on https://github.com/vpelletier/python-libusb1

Please, note that the following packages should be installed before using this program:
	> pip install h5py
"""
import os
import sys
import time
import threading
import numpy as np
from . import core
from .log import mu32log as log
from .exception import MuException


class Mu32rand( core.Mu32 ):

    def __init__( self ):
        super().__init__()

    def check_usb( self, vendor_id, vendor_pr, verbose=True ):
        pass

    def run( 
        self, 
        sampling_frequency=core.MU_DEFAULT_SAMPLING_FREQUENCY, 
        buffers_number=core.MU_DEFAULT_BUFFERS_NUMBER, 
        buffer_length=core.MU_DEFAULT_BUFFER_LENGTH, 
        duration=core.MU_DEFAULT_DURATION, 
        datatype=core.MU_DEFAULT_DATATYPE, 
        mems=core.MU_DEFAULT_ACTIVATED_MEMS,
        analogs = core.MU_DEFAULT_ACTIVATED_ANALOG,
        counter = core.MU_DEFAULT_ACTIVATED_COUNTER,
        counter_skip = core.MU_DEFAULT_COUNTER_SKIPPING,
        status = core.MU_DEFAULT_ACTIVATED_STATUS,
        post_callback_fn=None, 
        callback_fn = None,
        block = core.MU_DEFAULT_BLOCK_FLAG
    ):

        try:
            self._clockdiv = max( int( 500000 / sampling_frequency ) - 1, 9 )
            self._sampling_frequency = 500000 / ( self._clockdiv + 1 )
            self._buffer_length = buffer_length
            self._buffers_number = buffers_number
            self._duration = duration
            self._mems = mems
            self._mems_number = len( self._mems )
            self._analogs = analogs
            self._analogs_number = len( self._analogs )
            self._counter = counter
            self._counter_skip = counter_skip
            self._status = status
            self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
            self._buffer_words_length = self._channels_number*self._buffer_length
            self._transfers_count = int( ( self._duration * self._sampling_frequency ) // self._buffer_length )
            self._post_callback_fn = post_callback_fn
            self._callback_fn = callback_fn
            self._block = block

            """
            Do some controls and print recording parameters
            """
            if self._analogs_number > 0:
                log.warning( f"Mu32: {self._analogs_number} analogs channels were activated while they are not supported on Mu32 device -> unselecting")
                self._analogs = []
                self._analogs_number = 0
                self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
                self._buffer_words_length = self._channels_number*self._buffer_length

            log.info( 'Mu32: Start running ...')
            log.info( '-'*20 )

            if datatype != 'int32' and datatype != 'float32':
                raise MuException( 'Unknown datatype [%s]' % datatype )
            self._datatype = datatype

            if sampling_frequency > 50000:
                log.warning( 'Mu32: desired sampling frequency [%s Hz] is greater than the max admissible sampling frequency. Adjusted to 50kHz' % sampling_frequency )
            else:
                log.info( 'Mu32: sampling frequency: %d Hz' % self._sampling_frequency )

            if self._counter_skip and not self._counter:
                log.warning( 'Mu32: cannot skip counter in the absence of counter (counter flag is off)' )

            self._recording = True
            if self._block:
                self.transfer_loop()
            else: 
                self._transfer_thread = threading.Thread( target= self.transfer_loop )
                self._transfer_thread.start()

        except MuException as e:
            log.critical( str( e ) )
            raise
        except Exception as e:
            log.critical( f"Unexpected error:{e}" )
            raise

    def transfer_loop( self ):

        log.info( f" .desired recording duration: {self._duration} s" )
        log.info( f" .minimal recording duration: {( self._transfers_count*self._buffer_length ) / self._sampling_frequency} s" )
        log.info( f" .{self._mems_number} activated microphones" )
        log.info( f" .activated microphones: {self._mems}" )
        log.info( f" .{self._analogs_number} activated analogic channels" )
        log.info( f" .activated analogic channels: {self._analogs }" )
        log.info( f" .whether counter is activated: {self._counter}" )
        log.info( f" .whether status is activated: {self._status}" )
        log.info( f" .total channels number is {self._channels_number}" )
        log.info( f" .datatype: {self._datatype}" )
        log.info( f" .number of USB transfer buffers: {self._buffers_number}" )
        log.info( f" .buffer length in samples number: {self._buffer_length} ({self._buffer_length*1000/self._sampling_frequency} ms duration)" )			
        log.info( f" .buffer length in 32 bits words number: {self._buffer_length}x{self._channels_number}={self._buffer_words_length} ({self._buffer_words_length*core.MU_TRANSFER_DATAWORDS_SIZE} bytes)" )
        log.info( f" .minimal transfers count: {self._transfers_count}" )
        log.info( f" .multi-threading execution mode: {not self._block}" )

        log.info( ' .end of acquisition' )
        log.info( ' .data post processing...' )

        transfer_duration = self._buffer_length/self.sampling_frequency 
        while self._recording:
            counter = np.arange( self._buffer_length ) + self._transfer_index * self._buffer_length
            data = np.append( [counter], np.random.rand( self._channels_number, self._buffer_length )*2 - 1, axis=0 )
            
            if self._counter and self._counter_skip:
                """
                Remove counter signal
                """
                data = data[1:,:]


            """
            Call user callback processing function if any.
            Otherwise push data in the object signal queue
            """
            if self._callback_fn != None:
                try:
                    self._callback_fn( self, data )
                except KeyboardInterrupt as e:
                    log.info( ' .keyboard interrupt...' )
                    self._recording = False
                except Exception as e:
                    log.critical( f"Mu32: unexpected error {e}. Aborting..." )
                    self._recording = False
            else:
                self._signal_q.put( data )


            """
            Control duration and stop acquisition if the transfer count is reach
            _transfers_count set to 0 means the acquisition is infinite loop
            """
            self._transfer_index += 1
            if self._transfers_count != 0 and  self._transfer_index > self._transfers_count:
                self._recording = False

            time.sleep( transfer_duration )

        """
        Call the final callback user function if any 
        """
        if self._post_callback_fn != None:
            self._post_callback_fn( self )