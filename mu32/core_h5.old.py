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
import h5py

import numpy as np

from mu32.log import logging, mulog as log, mu32log		# mu32log for backward compatibility
from mu32.exception import MuException
from mu32.core_base import MegaMicro



H5_DEFAULT_SAMPLING_FREQUENCY = 50000
H5_DEFAULT_BUFFERS_NUMBER = 8
H5_DEFAULT_BUFFER_LENGTH = 512
H5_DEFAULT_DURATION = 1
H5_DEFAULT_ACTIVATED_MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
H5_DEFAULT_DATATYPE = 'int32'

H5_DEFAULT_BUFFERS_NUMBER 		= 8
H5_TRANSFER_DATAWORDS_SIZE		= 4
H5_TRANSFER_DATABYTES_SIZE		= H5_TRANSFER_DATAWORDS_SIZE * 8
H5_DEFAULT_BUFFER_LENGTH		= 512
H5_DEFAULT_DURATION				= 1

class MuH5( MegaMicro ):
	"""
	MuH5 is the base class for getting array signals stored in H5 files 
	"""
	def __init__( self, filename=None ):
		"""
		Set default values
		"""
		self._sampling_frequency = H5_DEFAULT_SAMPLING_FREQUENCY
		self._filename = filename
		self._buffer_length = H5_DEFAULT_BUFFER_LENGTH
		self._buffers_number = H5_DEFAULT_BUFFERS_NUMBER
		self._duration = H5_DEFAULT_DURATION
		self._transfers_count = int( ( H5_DEFAULT_DURATION * H5_DEFAULT_SAMPLING_FREQUENCY )//H5_DEFAULT_BUFFER_LENGTH )
		self._datatype = H5_DEFAULT_DATATYPE
		self._callback_fn = None
		self._transfer_index = 0
		self._recording = False

	def __del__( self ):
		log.info( '-'*20 )
		log.info('MuH5: end')

	def processRun():
		pass

	def run( self, sampling_frequency=H5_DEFAULT_SAMPLING_FREQUENCY, buffers_number=H5_DEFAULT_BUFFERS_NUMBER, buffer_length=H5_DEFAULT_BUFFER_LENGTH, duration=H5_DEFAULT_DURATION, datatype=H5_DEFAULT_DATATYPE, mems=H5_DEFAULT_ACTIVATED_MEMS, post_callback_fn=None, callback_fn=None ):
		"""
		Run is a generic acquisition method that get signals from the H5 file
		"""

		try:
			self._sampling_frequency = sampling_frequency
			self._buffer_length = buffer_length
			self._buffers_number = buffers_number
			self._duration = duration
			self._mems = mems
			self._mems_number = len( self._mems )
			self._transfers_count = int( ( self._duration * self._sampling_frequency ) // self._buffer_length )
			self._callback_fn = callback_fn

			"""
			Do some controls and print recording parameters
			"""
			log.info( 'MuH5: Start running H5 file reading...')
			log.info( '-'*20 )

			if datatype != 'int32' and datatype != 'float32':
				raise MuException( 'Unknown datatype [%s]' % datatype )
			self._datatype = datatype

			if sampling_frequency > 50000:
				log.warning( f"MuH5: desired sampling frequency [{sampling_frequency} Hz] is greater than the max admissible sampling frequency. Adjusted to 50kHz" )
			else:
				log.info( f"Mu32: sampling frequency: {self._sampling_frequency} Hz" )

			log.info( ' .desired recording duration: %d s' % self._duration )
			log.info( ' .minimal recording duration: %f s' % ( ( self._transfers_count*self._buffer_length ) / self._sampling_frequency ) )
			log.info( ' .datatype: %s' % self._datatype )
			log.info( ' .number of USB transfer buffers: %d' % self._buffers_number )
			log.info( ' .buffer length in samples number: %d (%f ms duration)' % ( self._buffer_length, self._buffer_length*1000/self._sampling_frequency ) )
			log.info( ' .minimal transfers count: %d' % self._transfers_count )
			log.info( ' .%d activated microphones' % self._mems_number )
			log.info( ' .activated microphones: %s' % str( self._mems ) )

			with H5Context( self._filename ) as context:

				handle = context.openH5()
				if handle is None:
					raise MuException( f"H5 file opening failed") 


			with h5py.File( self._filename , "r" ) as f:
				"""
				verify H5 file properties
				"""

				"""
				Allocate the list of transfer buffers
				"""
				transfer_list = []
				for _ in range( self.buffers_number ): 
					transfer = H5Transfer(
						length = self._mems_number * H5_TRANSFER_DATAWORDS_SIZE * self._buffer_length,
						callback = self.processRun
					)
					transfer.submit()
					transfer_list.append( transfer )

					"""
					Loop as long as there is at least one submitted transfer
					"""
					self._transfer_index = 0
					self._recording = True
					while any( x.isSubmitted() for x in transfer_list ):
						try:
							#Handle any pending event (blocking). See libusb1 documentation for details (there is a timeout, so it's not "really" blocking).
							#context.handleEvents()
							pass
						
						except KeyboardInterrupt:
							log.warning( 'MuH5: keyboard interruption...' )
							self._recording = False					
						except Exception as e:
							self._recording = False
							raise 



		except MuException as e:
			log.critical( str( e ) )
			raise
		except:
			log.critical( 'Unexpected error:', sys.exc_info()[0] )
			raise

class H5Context:
	def __init__( self, filename: str ):
		self.filename = filename

	def __enter__(self):
		pass

	def __exit__(self):
		pass
	
	def openH5( self ):


		self.file = h5py.File( self.filename, 'r' )
		return H5Handle( self._filename )
			self.filename = filename
		if not os.path.isfile( self._filename ):
			log.error( "MuH5: Fichier H5 introuvable: '{self._filename}'" )
			return None

class H5Handle:
	def __init__( self, filename ):
		


class H5Transfer:
	def __init__( self, length, callback, user_data ):
		self._length = length
		self._callback = callback
		self._user_data = user_data
		pass

	def submit():
		print( 'submit')

	def isSubmitted():
		return False
