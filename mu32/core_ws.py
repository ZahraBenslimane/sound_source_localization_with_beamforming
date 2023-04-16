# mu32.core.py python program interface for MegaMicro Mu32 remote receiver 
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
See documentation on usb websocket python programming on https://websockets.readthedocs.io/en/stable/index.html

Please, note that the following packages should be installed before using this program:
	> pip install websockets
"""
"""
see getting file on https://stackoverflow.com/questions/9382045/send-a-file-through-sockets-in-python

client code:

import socket
import time

TCP_IP = 'localhost'
TCP_PORT = 9001
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
recived_f = 'imgt_thread'+str(time.time()).split('.')[0]+'.jpeg'
with open(recived_f, 'wb') as f:
    print('file opened')
    while True:
        #print('receiving data...')
        data = s.recv(BUFFER_SIZE)
        print('data=%s', (data))
        if not data:
            f.close()
            print('file close()')
            break
        # write data to a file
        f.write(data)

print('Successfully get the file')
s.close()
print('connection closed')
"""


import time
import threading
import json
import asyncio
import websockets
import numpy as np
from datetime import datetime, timedelta

from mu32.core import MegaMicro, log
from mu32.core_base import MU_TRANSFER_DATAWORDS_SIZE, DEFAULT_SAMPLING_FREQUENCY, DEFAULT_ACTIVATED_MEMS
from mu32.exception import MuException

"""
Default conecting properties
"""
DEFAULT_REMOTE_ADDRESS = 			'127.0.0.1'					# remote receiver network address
DEFAULT_REMOTE_PORT = 				8002						# remote receiver network port
DEFAULT_H5_PASS_THROUGH = 			False						# whether server performs H5 saving or client 
DEFAULT_SYSTEM = 					'Mu32'						# remote system type
DEFAULT_PLAY_FILENAME = 			'./'						# directory or fine for H5 playing
DEFAULT_START_TIME = 				0							# starting time in H5 file playing in seconds
DEFAULT_STREAM_SKIP = 				False						# stop incomming network stream if True

class MegaMicroWS( MegaMicro ):
	"""
	MegaMicroWS is a generic websocket interface to MegaMicro receiver designed for handling Mu32 to Mu1024 and MuH5 remote systems
	"""
	__server_response = ''
	__sched_parameters = {}
	__h5_parameters = {}

	_h5_pass_through = DEFAULT_H5_PASS_THROUGH	
	_h5_start_time = DEFAULT_START_TIME	
	_h5_play_filename = DEFAULT_PLAY_FILENAME
	_stream_skip = DEFAULT_STREAM_SKIP

	@property
	def response( self ):
		return self.__server_response

	def __init__( self, remote_ip=DEFAULT_REMOTE_ADDRESS, remote_port=DEFAULT_REMOTE_PORT ):
		"""
		class base receiver properties are note used since system is remote -> set to 0x00
		"""
		super().__init__(
			usb_vendor_id=0x00, 
			usb_vendor_product=0x00,
			usb_bus_address=0x00,
			pluggable_beams_number=0x00
		)

		"""
		Set default values			
		"""
		self._server_address = remote_ip
		self._server_port = remote_port
		self._system = DEFAULT_SYSTEM

	def __del__( self ):
		log.info(' .MegaMicroWS: destroyed')


	def h5( self, command, parameters=None ):
		"""
		The h5 manager let you manage H5 files on the server 
		
		:param command: the requested job (run, doa, ...)
		:type command: str
		:param parameters: MegaMicro parameters
		:type parameters: dict
		:return: the object
		:rtype: MegaMicroWS Object
		"""

		log.info( f"Send {command} command to server H5 manager..." )

		self.__h5_parameters = {'command': command }
		if parameters is not None:
			self.__h5_parameters.update( parameters )
		asyncio.run( self._h5_send() )

		return self


	async def _h5_send( self ):
		"""
		Send a H5 file manager command to server
		"""
		try:
			if self.__h5_parameters['command'] == 'h5get':
				"""
				Getting file require special transaction with server
				"""
				async with websockets.connect( 'ws://' + self._server_address + ':' + str( self._server_port ) ) as websocket:
					"""
					Send the request
					"""
					await websocket.send( json.dumps( {
						'request': 'h5handler',
						'parameters': self.__h5_parameters
					} ) )
					response = json.loads( await websocket.recv() )
					
					if response['type'] == 'response' and response['response'] == 'START':
						"""
						get file
						"""
						with open( self.__h5_parameters['filename'], 'wb') as file:
							while True:
								data = await websocket.recv()
								if isinstance( data, str ):
									"""
									No more data to upload: end of transfert
									"""
									response = json.loads( data )
									if response['type'] == 'response' and response['response'] == 'STOP':
										"""
										No more data to upload: end of transfert
										"""
										#websocket.close()
										self.__server_response = response
										break
									else:
										"""
										Unespected response from server
										"""
										#websocket.close()
										self.__server_response = {
											'type': 'error',
											'error': 'Unespected response from server',
											'message': f"Type response was {response['type']}. Local file may be corrupted",
											'response': response['response']
										}
										log.warning( f"Unespected response from server" )
										break
								else:
									file.write( data )

					elif response['type'] == 'error':
						self.__server_response = response
						log.warning( f"Request failed with error response from server" )
					else:
						self.__server_response = response
						log.warning( f"Request failed with unespected response from serveur (type={response['type']}, response={response['response']})" )
			else:
				"""
				More conventional commands
				"""
				async with websockets.connect( 'ws://' + self._server_address + ':' + str( self._server_port ) ) as websocket:
					request = json.dumps( {
						'request': 'h5handler',
						'parameters': self.__h5_parameters
					} )
					await websocket.send( request )
					self.__server_response = json.loads( await websocket.recv() )

		except websockets.ConnectionClosedOK as e:
			self.__server_response = {
				'type': 'response',
				'error': 'Connexion closed by server (Unexpected)',
				'message': f"{e}",
				'response': ''
			}
			log.warning( f" .Connexion closed by peer" )
		except websockets.ConnectionClosedError as e:
			self.__server_response = {
				'type': 'error',
				'error': 'Connexion closed by server',
				'message': e,
				'response': ''
			}			
			log.warning( f" .Connexion closed by server with error: {e}" )
		except Exception as e:
			self.__server_response = {
				'type': 'error',
				'error': 'Unknown error',
				'message': e,
				'response': ''
			}			
			log.warning( f" .Getfile request failed: {e}" )			


	def scheduler( self, command, start_datetime: datetime=None, stop_datetime: datetime=None, repeat_delay=None, parameters=None ):
		"""
		The scheduler send jobs to be scheduled by the remote server.
		Note that the scheduling activity is not handled by the client but only by the server.
		As such the scheduling order is send and then the function exit after got the server response.

		:param command: the requested job (run, doa, ...)
		:type command: str
		:param start_datetime: Optionnal task starting time. Default is now
		:type start_datetime: datetime
		:param stop_datetime: Optionnal task stop time. Default defined for one second duration
		:type start_datetime: datetime
		:param repeat_delay: Optionnal task repeting delay. Default defined for two seconds
		:type repeat_delay: float
		:param parameters: MegaMicro parameters
		:type parameters: dict
		:return: the object
		:rtype: MegaMicroWS Object
		"""
		if command == 'run':
			log.info( f"Scheduling run command..." )
			self.__server_response = 'OK'
			
			if start_datetime is None:
				start_datetime = datetime.now()
			start_timestamp = start_datetime.timestamp()

			if stop_datetime is None:
				stop_timestamp = start_timestamp + timedelta( seconds=1 )
			else:
				stop_timestamp = stop_datetime.timestamp()

			if parameters is None:
				parameters = {
					'sampling_frequency': DEFAULT_SAMPLING_FREQUENCY,
					'mems': DEFAULT_ACTIVATED_MEMS
				}

			parameters.update( {
				'command': command,
				'sched_start_time':  start_timestamp,
				'sched_stop_time':  stop_timestamp
			} )

			self.__sched_parameters = parameters
			asyncio.run( self.scheduler_send() )

		elif command == 'prun':
			log.info( f"Scheduling permnanent run command..." )
			self.__server_response = 'OK'
			
			if start_datetime is None:
				start_datetime = datetime.now()
			start_timestamp = start_datetime.timestamp()

			if stop_datetime is None:
				stop_timestamp = start_timestamp + timedelta( seconds=1 )
			else:
				stop_timestamp = stop_datetime.timestamp()

			if repeat_delay == None:
				repeat_delay = 2

			if parameters is None:
				parameters = {
					'sampling_frequency': DEFAULT_SAMPLING_FREQUENCY,
					'mems': DEFAULT_ACTIVATED_MEMS
				}

			parameters.update( {
				'command': command,
				'sched_start_time':  start_timestamp,
				'sched_stop_time':  stop_timestamp,
				'sched_repeat_time': repeat_delay
			} )

			self.__sched_parameters = parameters
			asyncio.run( self.scheduler_send() )



		else:
			log.info( f"Send {command} command to server scheduler..." )

			self.__sched_parameters = {'command': command }
			if parameters is not None:
				self.__sched_parameters.update( parameters )
			asyncio.run( self.scheduler_send() )

		return self


	async def scheduler_send( self ):

		try:
			async with websockets.connect( 'ws://' + self._server_address + ':' + str( self._server_port ) ) as websocket:
				request = json.dumps( {
					'request': 'scheduler',
					'parameters': self.__sched_parameters
				} )
				await websocket.send( request )
				self.__server_response = json.loads( await websocket.recv() )

		except websockets.ConnectionClosedOK:
			log.info( f" .Connexion closed by peer" )
		except websockets.ConnectionClosedError as e:
			log.info( f" .Connexion closed by peer with error: {e}" )
		except Exception as e:
			raise e


	def run( self, **kwargs):
		self.run_setargs( kwargs )

		if kwargs.get('parameters') is None: parameters=None
		else: parameters=kwargs.get('parameters')
		if kwargs.get('system') is None: system=None
		else: system=kwargs.get('system')
		if kwargs.get('h5_play_filename') is None: h5_play_filename=None
		else: h5_play_filename=kwargs.get('h5_play_filename')
		if kwargs.get('h5_start_time') is None: h5_start_time=None
		else: h5_start_time=kwargs.get('h5_start_time')
		if kwargs.get('h5_pass_through') is None: h5_pass_through=DEFAULT_H5_PASS_THROUGH
		else: h5_pass_through=kwargs.get('h5_pass_through')
		if kwargs.get('stream_skip') is None: stream_skip=DEFAULT_STREAM_SKIP
		else: stream_skip=kwargs.get('stream_skip')

		if parameters is not None:
			if 'system' in parameters:
				system = parameters.get( 'system' )
			if 'h5_start_time' in parameters:
				h5_start_time = parameters.get( 'h5_start_time' )
			if 'h5_play_filename' in parameters:
				h5_play_filename = parameters.get( 'h5_play_filename' )
			if 'h5_pass_through' in parameters:
				h5_pass_through = parameters.get( 'h5_pass_through' )	
			if 'stream_skip' in parameters:
				stream_skip = parameters.get( 'stream_skip' )

		self._system = system	
		self._h5_start_time = h5_start_time	
		self._h5_play_filename = h5_play_filename	
		self._h5_pass_through = h5_pass_through	
		self._stream_skip = stream_skip

		try:
			"""
			Do some controls and print recording parameters
			"""
			if self._analogs_number > 0:
				log.warning( f"{self._analogs_number} analogs channels were activated while they are not supported on Mu32 device -> unselecting")
				self._analogs = []
				self._analogs_number = 0
				self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
				self._buffer_words_length = self._channels_number*self._buffer_length

			log.info( 'Mu32ws: Start running recording...')
			log.info( '-'*20 )
			log.info( ' .sampling frequency: %d Hz' % self._sampling_frequency )

			if self._block == True:
				log.warning( 'Mu32ws: blocking mode is not available in remote mode (set to False)' )
				self._block = False

			self._transfer_thread = threading.Thread( target= self.transfer_loop_thread )
			self._transfer_thread.start()

		except MuException as e:
			log.critical( str( e ) )
			raise
		except Exception as e:
			log.critical( f"Unexpected error:{e}" )
			raise


	def listen( self, **kwargs):
		self.run_setargs( kwargs )

		if kwargs.get('parameters') is None: parameters=None
		else: parameters=kwargs.get('parameters')
		if kwargs.get('system') is None: system=None
		else: system=kwargs.get('system')
		if kwargs.get('h5_play_filename') is None: h5_play_filename=None
		else: h5_play_filename=kwargs.get('h5_play_filename')
		if kwargs.get('h5_start_time') is None: h5_start_time=None
		else: h5_start_time=kwargs.get('h5_start_time')
		if kwargs.get('h5_pass_through') is None: h5_pass_through=DEFAULT_H5_PASS_THROUGH
		else: h5_pass_through=kwargs.get('h5_pass_through')


		if parameters is not None:
			if 'system' in parameters:
				system = parameters.get( 'system' )
			if 'h5_start_time' in parameters:
				h5_start_time = parameters.get( 'h5_start_time' )
			if 'h5_play_filename' in parameters:
				h5_play_filename = parameters.get( 'h5_play_filename' )
			if 'h5_pass_through' in parameters:
				h5_pass_through = parameters.get( 'h5_pass_through' )
				

		self._system = system	
		self._h5_start_time = h5_start_time	
		self._h5_play_filename = h5_play_filename	
		self._h5_pass_through = h5_pass_through	

		try:
			"""
			Do some controls and print recording parameters
			"""
			if self._analogs_number > 0:
				log.warning( f"{self._analogs_number} analogs channels were activated while they are not supported on Mu32 device -> unselecting")
				self._analogs = []
				self._analogs_number = 0
				self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
				self._buffer_words_length = self._channels_number*self._buffer_length

			"""
			Channels number depends on local parameters only. Not on server ones (the ones that can differ with counter setting)
			"""
			#self._channels_number = self._mems_number + self._analogs_number + self._status + ( 1 if self._counter and not self._counter_skip else 0 )
			#self._channels_number = self._mems_number + self._analogs_number + self._status + self._counter

			if self._block == True:
				log.warning( 'Mu32ws: blocking mode is not available in remote mode (set to False)' )
				self._block = False

			log.info( 'Mu32ws: Start listening...')
			log.info( '-'*20 )

			self._transfer_thread = threading.Thread( target= self.transfer_listenloop_thread )
			self._transfer_thread.start()

		except MuException as e:
			log.critical( str( e ) )
			raise
		except Exception as e:
			log.critical( f"Unexpected error:{e}" )
			raise


	def wait( self ):
		if self._block:
			log.warning( "Mu32ws: mu32ws.wait() should not be used in blocking mode" )
			return

		self._transfer_thread.join()

		if self._transfer_thread_exception:
			raise self._transfer_thread_exception

	def is_alive( self ):
		if self._block:
			log.warning( "Mu32ws: mu32ws.is_alive() should not be used in blocking mode" )
			return
		
		return self._transfer_thread.is_alive()

	def stop( self ):
		"""
		Stop the transfer loop
		"""
		self._recording = False

	def transfer_loop_thread( self ):
		asyncio.run( self.transfer_loop() )

	def transfer_listenloop_thread( self ):
		asyncio.run( self.listen_loop() )

	async def listen_loop( self ):

		log.info( f" .remote Mu32 server address:  {self._server_address}:{self._server_port}" )
		log.info( f" .desired recording duration: {self._duration}s" )
		log.info( f" .minimal recording duration: {( self._transfers_count*self._buffer_length ) / self._sampling_frequency}s" )
		log.info( f" .{self._mems_number} activated microphones" )
		log.info( f" .activated microphones: {self._mems}" )
		log.info( f" .{self._analogs_number} activated analogic channels" )
		log.info( f" .activated analogic channels: {self._analogs }" )
		log.info( f" .whether counter is activated: {self._counter}" )
		log.info( f" .whether counter activity is removed: {self._counter_skip}" )
		log.info( f" .whether status is activated: {self._status}" )
		log.info( f" .total channels number is {self._channels_number}" )
		log.info( f" .datatype: {self._datatype}" )

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

		if self._h5_recording:
			"""
			The local system or remote server will record data in H5 file
			"""
			if self._h5_pass_through:
				log.info( f" .H5 recording by server: OFF (pass through mode not allowed for listening request)" )
				self._h5_pass_through = False
			else:
				log.info( f" .H5 recording: ON" )
			self.h5_log_info()
		else:
			log.info( f" .H5 recording: OFF" )

		if self._system == 'MuH5':
			"""
			The server will run in H5 play mode
			"""
			raise Exception ( "MuH5 system cannot be executed: cannot request remote server to turn on H5 playing mode while running as listener" )

		try:
			async with websockets.connect( 'ws://' + self._server_address + ':' + str( self._server_port ) ) as websocket:
				"""
				Request watch command
				"""
				log.info( f" .connect to server and send listening command..." )
				parameters = {
					'sampling_frequency': self._sampling_frequency,
					'mems': self._mems,
					'analogs': self._analogs,
					'counter': self._counter,
					'counter_skip': self._counter_skip,
					'status': self._status,
					'duration': self._duration,
					'buffer_length': self._buffer_length,
					'buffers_number': self._buffers_number
				}

				message = json.dumps( {
					'request': 'listen',
					'parameters': parameters
				} )
				await websocket.send( message )
				response = json.loads( await websocket.recv() )
				if response['type'] == 'status' and response['response'] == "OK":
					log.info( " .listen command accepted by server" )
					"""
					Update local parameters according server parameters
					"""		
					self._buffer_length = response['status']['buffer_length']
					self._buffers_number = response['status']['buffers_number']
					if response['status']['sampling_frequency'] != self._sampling_frequency:
						log.info( f"Server frequency is {response['status']['sampling_frequency']}Hz. Cannot change it to {self._sampling_frequency}Hz!" )
						self._sampling_frequency = response['status']['sampling_frequency']
					else:
						log.info( f" .sampling frequency: {self._sampling_frequency}Hz" )

					log.info( f" .from server: number of USB transfer buffers: {self._buffers_number}" )
					log.info( f" .from server: buffer length in samples number: {self._buffer_length} ({self._buffer_length*1000/self._sampling_frequency} ms duration)" )			
					log.info( f" .from server: buffer length in 32 bits words number: {self._buffer_length}x{self._channels_number}={self._buffer_words_length} ({self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE} bytes)" )
					log.info( f" .from server: minimal transfers count: {self._transfers_count}" )
					log.info( f" .multi-threading execution mode: {not self._block}" )

				elif response['type'] == 'error':
					raise MuException( f"Listening command failed. Server {self._server_address}:{self._server_port} said:  {response['error']}: {response['message']}" )
				else:
					log.error( f"unexpected server type response `{response['type']}`" )
					raise MuException( f"unexpected server type response `{response['type']}`" )

				"""
				Open H5 file if recording on and no pass through
				"""
				if self._h5_recording and not self._h5_pass_through:
					self.h5_init()

				"""
				Proccess received data
				"""
				self._transfer_index = 0
				self._recording = True
				while self._recording:
					data = await websocket.recv()
					if isinstance( data, str ):
						input_data = json.loads( data )
						if input_data['type'] == 'error':
							raise MuException( f"Received error message from server: {input_data['type']}: {input_data['response']}" )
						elif input_data['type'] == 'status' and input_data['response'] == 'END':
							log.info( f" .Received end of service from server. Stop watching." )
							break
						else:
							raise MuException( f"Received unexpected type message from server: {input_data['type']}" )

					input_data = np.frombuffer( data, dtype=np.int32 )

					"""
					Get current timestamp as it was at transfer start
					"""
					transfer_timestamp = time.time() - self._buffer_duration

					input_data = np.reshape( input_data, ( self._buffer_length, self._channels_number ) ).T

					"""
					Remove counter signal is requested
					"""
					if self._counter and self._counter_skip:
						input_data = input_data[:,1:]

					"""
					Proceed to buffer recording in h5 file if requested
					"""
					if self._h5_recording and not self._h5_pass_through:
						try:
							self.h5_write_mems( input_data, transfer_timestamp )
						except Exception as e:
							log.error( f"Mu32: H5 writing process failed: {e}. Aborting..." )
							self._recording = False

					"""
					Call user callback processing function if any.
					Otherwise push data in the object signal queue
					"""
					if self._callback_fn != None:
						try:
							self._callback_fn( self, input_data )
						except KeyboardInterrupt as e:
							log.info( ' .keyboard interrupt during user processing function call' )
							self._recording = False
						except Exception as e:
							log.error( f"Unexpected error {e}. Aborting..." )
							raise
					else:
						if self._queue_size > 0 and self._signal_q.qsize() >= self._queue_size:
							"""
							Queue size is limited and filled -> delete older element before queuing new:  
							"""
							self._signal_q.get()
						self._signal_q.put( input_data )

 
					"""
					Control duration and stop acquisition if the transfer count is reach
					_transfers_count set to 0 means the acquisition is infinite loop
					"""
					self._transfer_index += 1
					"""
					The problem is to decide which of the client or the server is responsible for counting.
					Until now we are on the server strategy for finite loop. 
					"""
					#if self._transfers_count != 0 and  self._transfer_index > self._transfers_count:
					#	self._recording = False


				if not self._recording:
					"""
					Recording flag False means the stop command comes from the client -> send stop command to the server
					"""
					log.info( ' .send stop command to server...' )
					await websocket.send( json.dumps({ 'request': 'stop'}) )

				if self._h5_recording and not self._h5_pass_through:
					"""
					Stop H5 recording
					"""
					self.h5_close()

				log.info( ' .end of acquisition' )

				"""
				Call the final callback user function if any 
				"""
				if self._post_callback_fn != None:
					log.info( ' .data post processing...' )
					self._post_callback_fn( self )


		except Exception as e:
			log.error( f"Stop running due to exception: {e}." )
			self._transfer_thread_exception = e
			if self._h5_recording and not self._h5_pass_through:
				"""
				Stop H5 recording
				"""
				self.h5_close()





	async def transfer_loop( self ):

		log.info( f" .remote Mu32 server address:  {self._server_address}:{self._server_port}" )
		log.info( f" .desired recording duration: {self._duration}s" )
		log.info( f" .minimal recording duration: {( self._transfers_count*self._buffer_length ) / self._sampling_frequency}s" )
		log.info( f" .{self._mems_number} activated microphones" )
		log.info( f" .activated microphones: {self._mems}" )
		log.info( f" .{self._analogs_number} activated analogic channels" )
		log.info( f" .activated analogic channels: {self._analogs }" )
		log.info( f" .whether counter is activated: {self._counter}" )
		log.info( f" .whether counter activity is removed: {self._counter_skip}" )
		log.info( f" .whether status is activated: {self._status}" )
		log.info( f" .total channels number is {self._channels_number}" )
		log.info( f" .datatype: {self._datatype}" )
		log.info( f" .number of USB transfer buffers: {self._buffers_number}" )
		log.info( f" .buffer length in samples number: {self._buffer_length} ({self._buffer_length*1000/self._sampling_frequency} ms duration)" )			
		log.info( f" .buffer length in 32 bits words number: {self._buffer_length}x{self._channels_number}={self._buffer_words_length} ({self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE} bytes)" )
		log.info( f" .minimal transfers count: {self._transfers_count}" )
		log.info( f" .multi-threading execution mode: {not self._block}" )
		log.info( f" .whether input stream is not blocked: {not self._stream_skip}" )

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


		if self._h5_recording:
			"""
			The local system or remote server will record data in H5 file
			"""
			if self._h5_pass_through:
				log.info( f" .H5 recording: ON by server (pass-through mode)" )
			else:
				log.info( f" .H5 recording: ON" )
			self.h5_log_info()
		else:
			log.info( f" .H5 recording: OFF" )

		if self._system == 'MuH5':
			"""
			The server will run in H5 play mode
			"""
			log.info( f" .Request remote server to turn on H5 playing mode" )
			log.info( f" .Remote file or directory to play: {self._h5_play_filename}" )
			log.info( f" .Start time set to {self._h5_start_time}s" )
			
		try:
			async with websockets.connect( 'ws://' + self._server_address + ':' + str( self._server_port ) ) as websocket:
				"""
				Request run command
				"""
				log.info( f" .connect to server and send running command..." )
				parameters = {
					'sampling_frequency': self._sampling_frequency,
					'mems': self._mems,
					'analogs': self._analogs,
					'counter': self._counter,
					'counter_skip': self._counter_skip,
					'status': self._status,
					'duration': self._duration,
					'buffer_length': self._buffer_length,
					'buffers_number': self._buffers_number,
					'stream_skip': self._stream_skip
				}
				if self._h5_recording and self._h5_pass_through:
					"""
					Ask the server to perform H5 recording
					"""
					parameters.update( {
						'h5_recording': True,
						'h5_rootdir': self._h5_rootdir,
						'h5_dataset_duration': self._h5_dataset_duration,
						'h5_file_duration': self._h5_file_duration,
						'h5_compressing': self._h5_compressing,
						'h5_compression_algo': self._h5_compression_algo,
						'h5_gzip_level': self._h5_gzip_level
					} )
				if self._system == 'MuH5':
					"""
					Ask the server to run in H5 play mode
					"""
					parameters.update( {
						'system': self._system,
						'h5_play_filename' : self._h5_play_filename,
						'h5_start_time': self._h5_start_time
					} )

				message = json.dumps( {
					'request': 'run',
					'parameters': parameters
				} )
				await websocket.send( message )
				response = json.loads( await websocket.recv() )
				if response['type'] == 'status' and response['response'] == "OK":
					log.info( " .run command accepted by server" )						
				elif response['type'] == 'error':
					raise MuException( f"Running command failed. Server {self._server_address}:{self._server_port} said:  {response['error']}: {response['message']}" )
				else:
					log.error( f"unexpected server type response `{response['type']}`" )
					raise MuException( f"unexpected server type response `{response['type']}`" )

				"""
				Open H5 file if recording on and no pass through
				"""
				if self._h5_recording and not self._h5_pass_through:
					self.h5_init()

				"""
				Proccess received data
				"""
				self._transfer_index = 0
				self._recording = True
				while self._recording:
					data = await websocket.recv()
					if isinstance( data, str ):
						input_data = json.loads( data )
						if input_data['type'] == 'error':
							raise MuException( f"Received error message from server: {input_data['type']}: {input_data['response']}" )
						elif input_data['type'] == 'status' and input_data['response'] == 'END':
							log.info( f" .Received end of service from server. Stop running." )
							break
						else:
							raise MuException( f"Received unexpected type message from server: {input_data['type']}" )

					input_data = np.frombuffer( data, dtype=np.int32 )

					"""
					Get current timestamp as it was at transfer start
					"""
					transfer_timestamp = time.time() - self._buffer_duration

					input_data = np.reshape( input_data, ( self._buffer_length, self._channels_number - self._counter_skip ) ).T

					"""
					Remove counter signal is requested
					! NOT OK -> aborting:  index 1 is out of bounds for axis 0 with size 1
					"""
					#if self._counter and self._counter_skip:
					#	input_data = input_data[1:,:]

					"""
					Proceed to buffer recording in h5 file if requested
					"""
					if self._h5_recording and not self._h5_pass_through:
						try:
							self.h5_write_mems( input_data, transfer_timestamp )
						except Exception as e:
							log.error( f"Mu32: H5 writing process failed: {e}. Aborting..." )
							self._recording = False

					"""
					Call user callback processing function if any.
					Otherwise push data in the object signal queue
					"""
					if self._callback_fn != None:
						try:
							self._callback_fn( self, input_data )
						except KeyboardInterrupt as e:
							log.info( ' .keyboard interrupt during user processing function call' )
							self._recording = False
						except Exception as e:
							log.error( f"Unexpected error {e}. Aborting..." )
							raise
					else:
						if self._queue_size > 0 and self._signal_q.qsize() >= self._queue_size:
							"""
							Queue size is limited and filled -> delete older element before queuing new:  
							"""
							self._signal_q.get()
						self._signal_q.put( input_data )

 
					"""
					Control duration and stop acquisition if the transfer count is reach
					_transfers_count set to 0 means the acquisition is infinite loop
					"""
					self._transfer_index += 1
					"""
					The problem is to decide which of the client or the server is responsible for counting.
					Until now we are on the server strategy for finite loop. 
					"""
					#if self._transfers_count != 0 and  self._transfer_index > self._transfers_count:
					#	self._recording = False


				if not self._recording:
					"""
					Recording flag False means the stop command comes from the client -> send stop command to the server
					"""
					log.info( ' .send stop command to server...' )
					await websocket.send( json.dumps({ 'request': 'stop'}) )

				if self._h5_recording and not self._h5_pass_through:
					"""
					Stop H5 recording
					"""
					self.h5_close()

				log.info( ' .end of acquisition' )

				"""
				Call the final callback user function if any 
				"""
				if self._post_callback_fn != None:
					log.info( ' .data post processing...' )
					self._post_callback_fn( self )


		except Exception as e:
			log.error( f"Stop running due to exception: {e}." )
			self._transfer_thread_exception = e
			if self._h5_recording and not self._h5_pass_through:
				"""
				Stop H5 recording
				"""
				self.h5_close()

