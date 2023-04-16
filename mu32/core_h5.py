# mu32.core_h5.py python program interface for MegaMicro Mu32 receiver 
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

from operator import index
import os
import sys
import h5py
import threading
import json
import numpy as np
import queue
from time import sleep, time

from mu32.log import logging, mulog as log, DEBUG_MODE, mu32log		# mu32log for backward compatibility
from mu32.exception import Mu32Exception, MuException
from mu32.core_base import MegaMicro, MU_TRANSFER_DATAWORDS_SIZE, MU_BEAM_MEMS_NUMBER


DEFAULT_H5_PLAY_FILENAME			= './'
PROCESSING_DELAY_RATE				= 2/10							# computing delay rate relative to transfer buffer duration

#log.setLevel( logging.INFO )

class MuH5( MegaMicro ):
	"""
	MuH5 is the base class for getting array signals stored in H5 files 
	"""
	_h5_files= list()
	_h5_current_file = None
	_h5_current_filename = ''
	_h5_parameters = None
	_h5_playing = False
	_h5_dataset_index = 0
	_h5_dataset_index_ptr = 0
	_h5_start_time = 0
	_h5_run_kwargs = None
	_h5_ctrl_thread = None
	_h5_ctrl_thread_exception: MuException = None
	_h5_loop = False

	@property
	def h5_files( self ):
		return self._h5_files

	@property
	def parameters( self ):
		parameters = dict()
		if len( self._h5_files ) > 0:
			for index, filename in enumerate( self._h5_files ):
				with h5py.File( filename, 'r' ) as file:
					if 'muh5' in file:
						group = file['muh5']
						parameters.update( {filename:  
							dict( zip( group.attrs.keys(), group.attrs.values() ) )
						} )
					else:
						"""
						It seems not to be a MegaMicro H5 compatible file
						"""
						continue						

		return parameters

	@property
	def signal( self ):
		"""
		Return full signal
		"""
		signal = np.array()
		if len( self._h5_files ) == 0:
			""" No H5 file """
			return signal

		""" get only first """
		filename = self._h5_files[0]
		with h5py.File( filename, 'r' ) as file:
			if not 'muh5' in file:
				""" It seems not to be a MegaMicro H5 compatible file """
				return signal

			group = file['muh5']
			parameters = dict( zip( group.attrs.keys(), group.attrs.values() ) )
			for dataset_index in range( parameters['dataset_number'] ):
				dataset = file['muh5/' + str( dataset_index ) + '/sig']
				signal = np.append( signal, np.array( dataset[:] ) )

		return signal


	def __init__( self, filename=DEFAULT_H5_PLAY_FILENAME ):

		self._system = 'MuH5'
		super().__init__( 
			usb_vendor_id=0x00, 
			usb_vendor_product=0x00,
			usb_bus_address = 0x00,
			pluggable_beams_number = 0
		)

		"""
		Get H5 file or directory.
		"""
		self._h5_files= list()
		if os.path.isdir( filename ):
			for file in os.listdir( filename ):
				if file.endswith( '.h5' ):
					self._h5_files.append( file )
		elif os.path.exists( filename ):
			self._h5_files.append( filename )
		else:
			log.error( f"Unable to create object MuH5: file `{filename}` doesn't exist" )
			raise MuException( f"Unable to create object MuH5: file `{filename}` doesn't exist" )


	def __del__( self ):
		log.info('MuH5: end')
		log.info( '-'*20 )

	def check_usb( self, verbose=True ):
		pass

	def processRun():
		pass

	def run_setargs( self, kwargs ):
		"""
		Set base arguments. if no argument given, the run_setargs() set the MegaMicro.autotest() method as post callback
		"""
		super().run_setargs( kwargs )

		"""
		Set specific arguments for playing H5 files
		"""
		h5_play_filename = None
		h5_start_time = 0
		h5_loop = False

		if 'parameters' in kwargs:
			parameters = kwargs['parameters']
			if 'h5_play_filename' in parameters:
				h5_play_filename = parameters['h5_play_filename']
			if 'h5_start_time' in parameters and parameters['h5_start_time'] is not None:
				h5_start_time = parameters['h5_start_time']
			if 'h5_loop' in parameters and parameters['h5_loop'] is not None:
				h5_loop = parameters['h5_loop']	

		"""
		Check parameters given as args
		"""
		if 'h5_play_filename' in kwargs: h5_play_filename = kwargs['h5_play_filename']
		if 'h5_start_time' in kwargs: h5_start_time = kwargs['h5_start_time']
		if 'h5_loop' in kwargs: h5_loop = kwargs['h5_loop']

		if h5_play_filename is not None:
			"""
			A new playing file or directory is given as argument -> change default or initial one:
			"""
			files = list()
			if os.path.isdir( h5_play_filename ):
				for file in os.listdir( h5_play_filename ):
					if file.endswith( '.h5' ):
						files.append( file )
			elif os.path.exists( h5_play_filename ):
				files.append( h5_play_filename )
			else:
				log.error( f"Unable to run: file or directory `{h5_play_filename}` doesn't exist" )
				raise MuException( f"Unable to run: file or directory `{h5_play_filename}` doesn't exist" )			

			if files:
				self._h5_files = files

		self._h5_start_time = h5_start_time
		self._h5_loop = h5_loop



	def run( self, **kwargs ):
		if len( self._h5_files ) == 0:
			log.error( f"No H5 file: unable to run. Aborting run service..." )
			raise MuException( f"No H5 file: unable to run. Aborting run service..." )

		self._h5_run_kwargs = kwargs

		"""
		Start control thread.
		Ctrl_thread() run and control the transfer process thread and manage H5 files
		"""
		log.info( f" .Processing transfer...")

		if self._block:
			"""
			Blocking mode: no thread
			"""
			self.ctrl_thread()
		else: 
			self._h5_ctrl_thread = threading.Thread( target= self.ctrl_thread )
			self._h5_ctrl_thread.start()


	def ctrl_thread( self ):

		while True:
			"""
			Infinite reading loop according the self._h5_loop parameter
			"""
			for index, h5_file in enumerate( self._h5_files ):
				self._h5_current_filename = h5_file
				if index > 0:
					"""
					Reset starting time for next files
					"""
					self._h5_start_time = 0

				"""
				Loop on all available H5 files
				"""
				try:
					self.transfer_loop()
				except MuException as e:
					log.critical( str( e ), exc_info=DEBUG_MODE )
					self._h5_ctrl_thread_exception = e
				except Exception as e:
					log.critical( f"Unexpected error:{e}", exc_info=DEBUG_MODE )
					self._h5_ctrl_thread_exception = e
				except :
					log.critical( f"Unexpected unknown system error", exc_info=DEBUG_MODE )

			if not self._h5_loop:
				break

		log.info( f" .End of control thread" )



	def _process_transfert( self, data: np.ndarray ):
		"""
		Manage extracted data according user parameters
		"""
		if self._callback_fn != None:
			"""
			Call user callback processing function if any
			"""
			try:
				self._callback_fn( self, data )
			except KeyboardInterrupt as e:
				log.info( ' .keyboard interrupt...' )
				self._h5_playing = False
			except Exception as e:
				log.critical( f"Unexpected error {e}. Aborting..." )
				self._h5_playing = False
		else:
			if self._queue_size > 0 and self._signal_q.qsize() >= self._queue_size:
				"""
				Queue size is limited and filled -> delete older element before queuing new:  
				"""
				self._signal_q.get()
			"""
			Save to queue 
			"""
			self._signal_q.put( data )



	def transfer_loop( self ):
		"""
		! Note that continuity between files is not managed
		"""
		with h5py.File( self._h5_current_filename, 'r' ) as self._h5_current_file:	
			"""
			Control whether H5 file is a MuH5 file
			"""
			if not self._h5_current_file['muh5']:
				raise Mu32Exception( f"{self._h5_current_filename} seems not to be a MuH5 file: unrecognized format" )

			"""
			get parameters values on H5 file
			"""
			group = self._h5_current_file['muh5']
			self._h5_parameters = dict( zip( group.attrs.keys(), group.attrs.values() ) )

			self.run_setargs( self._h5_run_kwargs )

			"""
			Perform controls on requested parameter values: see if they are in accordance with H5 file parameters
			"""
			if self._sampling_frequency != self._h5_parameters['sampling_frequency']:
				log.warning( f"Requested sampling frequency of {self._sampling_frequency}Hz does not match recording one at {self._h5_parameters['sampling_frequency']}Hz: force to {self._h5_parameters['sampling_frequency']}Hz" )
				self._sampling_frequency = self._h5_parameters['sampling_frequency']
				#raise MuException( f"MuH5: no available under/over sampling algorithm: requested sampling frequency of {self._sampling_frequency}Hz do not match recording one at {self._h5_parameters['sampling_frequency']}Hz" )

			if self._counter and not self._counter_skip and ( not self._h5_parameters['counter'] or ( self._h5_parameters['counter'] and self._h5_parameters['counter_skip'] ) ):
				raise MuException( f"MuH5: Counter is requested but not available on H5 data" )

			self._available_mems = list( self._h5_parameters['mems'] )
			self._pluggable_beams_number = int( len( self._available_mems ) / MU_BEAM_MEMS_NUMBER )	
			if self._mems_number == 0:
				"""
				Check activated MEMs. 
				Beware that with MuH5, default activated MEMs (when not set by user) is 0 since we do not know the receiver type (Mu32, 256, 1024...)
				So if MEMs number is 0 -> set to available MEMs from H5 file
				"""
				self._mems = list( self._h5_parameters['mems'] )
				self._mems_number = len( self._mems )

			activated_mems = np.array( self._mems )
			mask = np.logical_not( np.isin( activated_mems , self._h5_parameters['mems'] ) )
			if len( activated_mems[mask] ) > 0:
				"""
				Some activated MEMs are not available in the H5 file -> abort
				We could react differently by adapting but reponse would not respect user request.  
				"""
				raise MuException( f"Some activated microphones ({activated_mems[mask]}) are not available on H5 file {self._h5_current_filename}. Available MEMs are: {self._h5_parameters['mems']} ")

			if 'analogs' in self._h5_parameters:
				self._available_analogs = list( self._h5_parameters['analogs'] )
				activated_analogs = np.array( self._analogs )
				mask_analogs = np.logical_not( np.isin( activated_analogs , self._h5_parameters['analogs'] ) )
				if len( activated_analogs[mask_analogs] ) > 0:
					"""
					Some activated analog channels are not available in the H5 file -> abort
					Abort for same reasons as for MEMs.
					"""
					raise MuException( f"Some activated analogics ({activated_analogs[mask_analogs]}) are not available on H5 file {self._h5_current_filename}. Available analogs channels are: {self._h5_parameters['analogs']} ")
			else:
				self._available_analogs = None
				if len( self._analogs ) > 0:
					"""
					Analog channels are not available in the H5 file but some are selected -> abort
					Abort for same reasons as for MEMs.
					"""
					raise MuException( f"There are no analogics channels avalable on H5 file {self._h5_current_filename}. Please do not select them (selected are: {self._analogs})")


			"""
			Start playing
			"""
			log.info( f" .Reading H5 file {self._h5_current_filename}")
			log.info( f" .{self._h5_parameters['duration']}s ({(self._h5_parameters['duration']/60):.02}min) of data in {self._h5_current_filename} H5 file" )
			log.info( f" .starting time: {self._h5_start_time}s" )
			log.info( f" .available mems: {self._available_mems}" )
			log.info( f" .whether counter available: {self._h5_parameters['counter'] and not self._h5_parameters['counter_skip']}" )
			log.info( f" .desired recording duration: {self._duration} s" )
			log.info( f" .minimal recording duration: {( self._transfers_count*self._buffer_length ) / self._sampling_frequency} s" )
			log.info( f" .{self._mems_number} activated microphones" )
			log.info( f" .activated microphones: {self._mems}" )
			log.info( f" .{self._analogs_number} activated analogic channels" )
			log.info( f" .available analogic channels: {self._available_analogs}" )
			log.info( f" .activated analogic channels: {self._analogs }" )
			log.info( f" .whether counter is activated: {self._counter}" )
			log.info( f" .whether status is activated: {self._status}" )
			log.info( f" .total channels number is {self._channels_number}" )
			log.info( f" .datatype: {self._datatype}" )
			log.info( f" .number of USB transfer buffers: {self._buffers_number}" )
			log.info( f" .buffer length in samples number: {self._buffer_length} ({self._buffer_length*1000/self._sampling_frequency} ms duration)" )			
			log.info( f" .buffer length in 32 bits words number: {self._buffer_length}x{self._channels_number}={self._buffer_words_length} ({self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE} bytes)" )
			log.info( f" .buffer duration in seconds: {self._buffer_duration}" )
			log.info( f" .minimal transfers count: {self._transfers_count}" )
			log.info( f" .multi-threading execution mode: {not self._block}" )
			log.info( f" .starting time: {self._h5_start_time * self._h5_parameters['duration'] / 100}s ({self._h5_start_time}% of file)" )
			log.info( f" .reading loop: {self._h5_loop}" )


			if self._callback_fn != None:
				log.info( f" .user callback function `{self._callback_fn}` set" )
			elif self._queue_size > 0:
				log.info( f" .no user callback function provided: queueing buffers (queue size is {self._queue_size}: some data may be lost!) " )
			else:
				log.info( f" .no user callback function provided: queueing buffers" )

			if self._post_callback_fn != None:
				log.info( f" .user post callback function `{self._post_callback_fn}` set" )
			else:
				log.info( f" .no user post callback function provided" )


			"""
			Parameters
			----------
			* _h5_dataset_index: current dataset
			* _h5_dataset_index_ptr: current index in current dataset 
			* _counter_state: transfer buffer counting
			"""
			self._transfer_index = 0
			self._h5_playing = True
			start_time = self._h5_start_time * self._h5_parameters['duration'] / 100

			if start_time > 0:
				"""
				Start from requested starting time
				"""
				if start_time > self._h5_parameters['duration']:
					log.errort( f"Cannot read file at {start_time}s star time. File duration ({self._h5_parameters['duration']}) is too short" )
					raise MuException( f"Cannot read file at {start_time}s star time. File duration ({self._h5_parameters['duration']}) is too short" )

				self._h5_dataset_index = int( ( start_time * self._sampling_frequency ) // self._h5_parameters['dataset_length'] )
				self._h5_dataset_index_ptr = int( ( start_time * self._sampling_frequency ) % self._h5_parameters['dataset_length'] )
			else:
				"""
				Start from beginning
				"""
				self._h5_dataset_index = 0
				self._h5_dataset_index_ptr = 0

			dataset = self._h5_current_file['muh5/' + str( self._h5_dataset_index ) + '/sig']

			"""
			Set the mask for mems and analogs selecting
			* mask: the binary mask for selecting channels to get
			* masking: True if somme channels are masked, False for complete copy
			* channels_number: selected microphones + counter if available and selected + selected analogs
			"""
			mask = list( np.isin( self._available_mems, self._mems ) )
			if self._h5_parameters['counter'] and not self._h5_parameters['counter_skip']:
				"""
				H5 has counter
				"""
				if self._counter_skip:
					"""
					User want to skip it
					"""
					mask = [False] + mask
				else:
					mask = [True] + mask

			if self._available_analogs != None:
				mask = mask + list( np.isin( self._available_analogs, self._analogs ) )

			channels_number = sum(mask)
			masking = channels_number != len(mask)

			if masking:
				transfer_buffer = np.array( dataset[:] )[mask,:]
			else:
				transfer_buffer = np.array( dataset[:] )

			time_start = time()
			initial_time = time_start
			processing_delay = self._buffer_duration * PROCESSING_DELAY_RATE
			while self._h5_playing == True:

				if self._h5_dataset_index_ptr + self._buffer_length <= self._h5_parameters['dataset_length']:
					"""
					There is enough data in current dataset: process to transfert
					"""
					if ( time() - time_start ) < self._buffer_duration - processing_delay:
						sleep( self._buffer_duration-time()+time_start-processing_delay )
					time_start = time()
					self._process_transfert( transfer_buffer[:,self._h5_dataset_index_ptr:self._h5_dataset_index_ptr+self._buffer_length] )
					self._h5_dataset_index_ptr += self._buffer_length
					
				else:
					"""
					No enough data in current dataset: open next dataset
					"""
					if self._h5_dataset_index < self._h5_parameters['dataset_number']:
						"""
						Next dataset exists: get last data of current dataset, open next and complete buffer
						"""
						current_dataset_last_samples_number = self._h5_parameters['dataset_length'] - self._h5_dataset_index_ptr
						buffer = transfer_buffer[:,self._h5_dataset_index_ptr:self._h5_dataset_index_ptr+self._h5_parameters['dataset_length']]
						dataset = self._h5_current_file['muh5/' + str( self._h5_dataset_index ) + '/sig']
						if masking:
							transfer_buffer = np.array( dataset[:] )[mask,:]
						else:
							transfer_buffer = np.array( dataset[:] )

						new_dataset_first_samples_number = self._buffer_length - current_dataset_last_samples_number
						buffer = np.append( buffer, transfer_buffer[:,:new_dataset_first_samples_number], axis=1 )

						"""
						Transfer buffer
						"""
						if ( time() - time_start ) < self._buffer_duration - processing_delay:
							sleep( self._buffer_duration-time()+time_start - processing_delay )
						time_start = time()
						self._process_transfert( buffer )

						self._h5_dataset_index_ptr = new_dataset_first_samples_number
						self._h5_dataset_index += 1
						log.info( f" .new dataset: [{self._h5_dataset_index}]" )
					else:
						"""
						No more dataset: save current buffer and stop playing
						"""
						buffer = transfer_buffer[:,self._h5_dataset_index_ptr:self._h5_parameters['dataset_length']]
						buffer = np.append( buffer, np.zeros( (channels_number, self._buffer_length - self._h5_parameters['dataset_length'] + self._h5_dataset_index_ptr), dtype=np.int32), axis=1 )
						
						"""
						Transfer buffer
						"""
						if time() - time_start < self._buffer_duration - processing_delay:
							sleep( self._buffer_duration-time()+time_start - processing_delay )
						time_start = time()
						self._process_transfert( buffer )

						self._h5_playing = False
						log.info( f" .no more dataset: stop playing" )

				self._transfer_index += 1
				if self._transfers_count != 0 and  self._transfer_index >= self._transfers_count:
					self._h5_playing = False

			"""
			Compute elasped time
			"""
			elapsed_time = time()-initial_time

			"""
			Call the final callback user function if any 
			"""
			if self._post_callback_fn != None:
				self._post_callback_fn( self )
			
			if self._duration == 0:
				log.info( f" .Elapsed time: {elapsed_time}s (H5 file duration was: {self._h5_parameters['duration']}s)")
			else:
				log.info( f" .Elapsed time: {elapsed_time}s (expected duration was: {self._duration}s)")


	def wait( self ):
		"""
		wait for thread termination (blocking call)
		"""
		if self._block:
			log.warning( "wait() should not be used in blocking mode" )
			return

		self._h5_ctrl_thread.join()
		if self._h5_ctrl_thread_exception:
			raise self._h5_ctrl_thread_exception


	def is_alive( self ):
		"""
		chack if thread is always running (non blocking call)
		"""
		if self._block:
			log.warning( "is_alive() should not be used in blocking mode" )
			return
		
		return self._h5_ctrl_thread.is_alive()


	def stop( self ):
		"""
		Stop the transfer loop
		"""
		self._h5_playing = False


	def autotest( self, mu ):
		""" 
		Post processing callback function for autotest the MuH5 file
		Call MegaMicro autotest function and add some H5 complements
		"""
		super().autotest( mu )

		print( f"From H5 file: {self._h5_current_filename }")
		"""
		Control whether H5 file is a MuH5 file (it should...)
		"""
		if not self._h5_current_file['muh5']:
			raise Mu32Exception( f"{self._h5_current_filename} seems not to be a MuH5 file: unrecognized format" )

		"""
		get parameters values on H5 file
		"""
		group = self._h5_current_file['muh5']
		h5_parameters = dict( zip( group.attrs.keys(), group.attrs.values() ) )

		print( '-'*20 )
		print( f" .Date: {h5_parameters['date']}" )
		print( f" .Duration: {h5_parameters['duration']}s ({(h5_parameters['duration']/60):.02}min) of data" )
		print( f" .Dataset number: {h5_parameters['dataset_number']}" )
		print( f" .Dataset length: {h5_parameters['dataset_length']} samples" )
		print( f" .Dataset duration: {h5_parameters['dataset_duration']}s" )		
		print( f" .Channels number: {h5_parameters['channels_number']} channels" )
		print( f" .Sampling frequency: {h5_parameters['sampling_frequency']}" )
		print( f" .Data type: {h5_parameters['datatype']}" )
		print( f" .Recorded mems: {h5_parameters['mems']} ({h5_parameters['mems_number']} mems)" )
		print( f" .Recorded analog channels: {h5_parameters['analogs']} ({h5_parameters['analogs_number']} channels)" )
		print( f" .Counter: {h5_parameters['counter']}" )
		print( f" .Counter skip: {h5_parameters['counter_skip']}" )
		print( f" .Data compression: {h5_parameters['compression']}" )
		print( '-'*20 )


def main():

	#muH5 = MuH5( 'mu5h-20220507-224200.h5' )
	muH5 = MuH5( 'mu5h-20220507-224200.h5' )
	
	muH5.run(
		duration=2
	)

if __name__ == "__main__":
	main()
