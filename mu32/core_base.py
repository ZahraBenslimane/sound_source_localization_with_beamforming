# mu32.core_base.py python program interface for MegaMicro transceiver 
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
MegaMicro class is an abstract base class that should not be instanciated. Use instead Mu32, Mu256 or Mu1024 classes for your application.

Mu32 documentation is available on https://distalsense.io
See documentation on usb device programming with libusb on https://pypi.org/project/libusb1/1.3.0/#documentation
Examples are available on https://github.com/vpelletier/python-libusb1

Please, note that the following packages should be installed before using this program:
	> pip install libusb1 h5py

See the Principal.h programm code for more documentation about triggering the MegaMicro devices
"""

from cgitb import handler
import os
import h5py
import threading
import libusb1
import usb1
import time
import numpy as np
import queue
import cv2 as cv
from datetime import datetime
from ctypes import addressof, byref, sizeof, create_string_buffer, CFUNCTYPE
from math import ceil as ceil

from .log import mulog as log
from .exception import MuException

"""
Suported system names
"""
MU32_SYSTEM_NAME				= 'Mu32'
MU32USB2_SYSTEM_NAME			= 'Mu32usb2'
MU256_SYSTEM_NAME				= 'Mu256'
MU1024_SYSTEM_NAME				= 'Mu1024'

"""
Some constants
"""
MEGAOCTET_BYTES					= 1024*1024
GIGAOCTET_BYTES					= MEGAOCTET_BYTES * 1024


"""
USB properties
"""
USB_DEFAULT_TIMEOUT				= 1000
USB_RECIPIENT_DEVICE			= 0x00
USB_REQUEST_TYPE_VENDOR			= 0x40
USB_ENDPOINT_OUT				= 0x00

"""
MegaMicro hardware commands
"""
MU_CMD_RESET					= b'\x00'									# Reset: power off the microphones
MU_CMD_INIT						= b'\x01'									# Sampling frequency setting
MU_CMD_START					= b'\x02'									# Acquisition running command
MU_CMD_STOP						= b'\x03'									# Acquisition stopping command
MU_CMD_COUNT					= b'\x04'									# Number of expected samples for next acqusition running
MU_CMD_ACTIVE					= b'\x05'									# Channels selection (MEMs, analogics, counter and status activating)
MU_CMD_PURGE					= b'\x06'									# Purge FiFo. No doc found about this command
MU_CMD_DELAY					= b'\x07'									# Test and tunning command. Not used in production mode. See documentation (no write function provided so far)
MU_CMD_DATATYPE					= b'\x09'									# Set datatype
MU_CMD_FX3_RESET				= 0xC0										# Init FX3 usb controler
MU_CMD_FX3_PH					= 0xC4										# External FPGA reset (hard reset)
MU_CMD_FPGA_0					= 0xB0										# Send a 0 byte command to FPGA
MU_CMD_FPGA_1					= 0xB1										# Send a 1 byte command to FPGA
MU_CMD_FPGA_2					= 0xB2										# Send a 2 byte command to FPGA
MU_CMD_FPGA_3					= 0xB3										# Send a 3 byte command to FPGA
MU_CMD_FPGA_4					= 0xB4										# Send a 4 byte command to FPGA
MU_CMD_DATATYPE					= b'\x09'									# Set datatype

"""
Cypress FX3 commands
"""
MU_CYPRESS_VENDOR_ID			= 0x04b4
MU_CYPRESS_VENDOR_PRODUCT		= 0x00bc
MU_CYPRESS_BUS_ADDRESS			= 0x81
MU_CYPRESS_CMD_FX3_RESET		= 0xA0										# Init FX3 usb controler using Cypress reset command
MU_TERMINUS_TECH_VENDOR_ID		= 0x1a40
MU_TERMINUS_TECH_VENDOR_PRODUCT	= 0x0101

"""
MemgaMicro hardware code values
"""																	
MU_CODE_DATATYPE_INT32			= b'\x00'									# Int32 datatype code
MU_CODE_DATATYPE_FLOAT32		= b'\x01'									# Float32 datatype code

"""
MegaMicro receiver properties
"""
MU_BEAM_MEMS_NUMBER				= 8											# MEMS number per beam
MU_MEMS_UQUANTIZATION			= 24										# MEMs unsigned quantization 
MU_MEMS_QUANTIZATION			= MU_MEMS_UQUANTIZATION - 1					# MEMs signed quantization 
MU_MEMS_AMPLITUDE				= 2**MU_MEMS_QUANTIZATION					# MEMs maximal amlitude value for "int32" data type
MU_MEMS_SENSIBILITY				= 1/(MU_MEMS_AMPLITUDE*10**(-26/20)/3.17)	# MEMs sensibility factor (-26dBFS for 104 dB that is 3.17 Pa)
MU_TRANSFER_DATAWORDS_SIZE		= 4											# Size of transfer words in bytes (same for in32 and float32 data type which always states for 32 bits (-> 4 bytes) )

"""
Default run propertie's values
"""
DEFAULT_BUFFERS_NUMBER			= 8											# USB transfer buffer number
DEFAULT_BUFFER_LENGTH			= 512										# buffer length in samples number to be received by each microphone
DEFAULT_DURATION				= 1											# Default acquisition time in seconds
DEFAULT_MAX_RETRY_ATTEMPT		= 5											# Maximal reset attempts when rebooting FX3 USB adapter
DEFAULT_TRANSFER_TIMEOUT		= 1000										# Waiting time of incomming receiver signals before acquisition is stoped
DEFAULT_START_TRIG_TIMEOUT		= 1000*60									# Waiting time before start trig reception (not implemented)

DEFAULT_CLOCKDIV				= 0x09										# Default internal acquisition clock value
DEFAULT_TIME_ACTIVATION			= 1											# Waiting time after MEMs powering in seconds
DEFAULT_TIME_ACTIVATION_RESET	= 0.01										# Waiting time between commands of the MegaMicro device reset sequence  
DEFAULT_PACKET_SIZE				= 512*1024
DEFAULT_PACKET_NUMBER			= 0
DEFAULT_TIMEOUT					= 1000
DEFAULT_DATATYPE				= "int32"									# Default receiver incoming data type ("int32" or "float32") 
DEFAULT_ACTIVATED_MEMS			= (0, )										# Default activated MEMs
DEFAULT_SAMPLING_FREQUENCY		= 500000 / ( DEFAULT_CLOCKDIV + 1 )			# Default sampling frequency
DEFAULT_ACTIVATED_ANALOG		= []										# Default activated analog channels
DEFAULT_ACTIVATED_COUNTER		= True										# Counter channel activation flag
DEFAULT_ACTIVATED_STATUS		= False										# Status channel activation flag
DEFAULT_COUNTER_SKIPPING		= True										# Counter channel blocking 
DEFAULT_BLOCK_FLAG				= False										# Default execution mode (False = multi-threading mode)
DEFAULT_QUEUE_SIZE				= 0											# Queue size as the number of buffer that can be queued (0 means infinite signal queueing)
DEFAULT_START_TRIG				= False										# Whether start by external trig or not 

"""
Default H5 values
"""
DEFAULT_H5_RECORDING				= False									# Whether H5 recording is On or Off
DEFAULT_H5_SEQUENCE_DURATION		= 1										# Time duration of a dataset in seconds
DEFAULT_H5_FILE_DURATION			= 15*60									# Time duration of a complete H5 file in seconds
DEFAULT_H5_COMPRESSING				= False									# Whether compression mode is On or Off
DEFAULT_H5_COMPRESSION_ALGO 		= 'gzip'								# Compression algorithm (gzip, lzf, szip)
DEFAULT_H5_GZIP_LEVEL 				= 4										# compression level for gzip algo (0 to 9, default 4) 
DEFAULT_H5_DIRECTORY				= './'									# The default directory where H5 files are saved

"""
Default video monitoring values
"""
DEFAULT_CV_MONITORING				= False									# Whether video monitoring is On or Off
DEFAULT_CV_CODEC					= 'mp4v'								# Video codec (OS/platform dependant)
DEFAULT_CV_DEVICE					= 0										# Default camera device (0, 1, 2,... depending on connected devices)
DEFAULT_CV_DIRECTORY				= './'									# The default directory where video files are saved
DEFAULT_CV_COLOR_MODE				= cv.COLOR_BGR2GRAY						# Default set to grey frames
DEFAULT_CV_SAMPLING_FREQUENCY		= 20.0									# Frame number per seconds
DEFAULT_CV_SHOW						= False									# Whether frames are showed or not 
DEFAULT_CV_WIDTH					= 640									# Frame size (width)
DEFAULT_CV_HEIGHT					= 480									# Frame size (height)
DEFAULT_CV_FILE_DURATION			= 15*60									# Time duration of a complete Video file in seconds

class MegaMicro:
	"""
	MegaMicro core abstract class
	"""
	_system = ''
	_usb_vendor_id = 0
	_usb_vendor_product = 0
	_usb_bus_address = 0
	_pluggable_beams_number = 0
	_signal_q = queue.Queue()
	_mems = DEFAULT_ACTIVATED_MEMS
	_mems_number = len( _mems )
	_available_mems = None
	_analogs = DEFAULT_ACTIVATED_ANALOG
	_analogs_number = len( _analogs )
	_available_analogs = None
	_counter = DEFAULT_ACTIVATED_COUNTER
	_counter_skip = DEFAULT_COUNTER_SKIPPING
	_status = DEFAULT_ACTIVATED_STATUS
	_channels_number = _mems_number + _analogs_number + _counter + _status
	_start_trig = DEFAULT_START_TRIG
	_clockdiv = DEFAULT_CLOCKDIV
	_sampling_frequency = 500000 / ( DEFAULT_CLOCKDIV + 1 )
	_buffer_length = DEFAULT_BUFFER_LENGTH
	_buffers_number = DEFAULT_BUFFERS_NUMBER
	_buffer_duration = _buffer_length / _sampling_frequency
	_duration = DEFAULT_DURATION
	_transfers_count = int( ( DEFAULT_DURATION * ( 500000 / ( DEFAULT_CLOCKDIV + 1 ) ) )//DEFAULT_BUFFER_LENGTH )
	_buffer_words_length = _channels_number*_buffer_length
	_datatype = DEFAULT_DATATYPE
	_callback_fn = None
	_post_callback_fn = None
	_transfer_index = 0
	_recording = False
	_restart_request = False
	_restart_attempt = 0
	_counter_state = 0
	_previous_counter_state = 0
	_block = DEFAULT_BLOCK_FLAG
	_transfer_thread = None
	_transfer_thread_exception: MuException = None
	_queue_size = DEFAULT_QUEUE_SIZE
	_h5_recording = DEFAULT_H5_RECORDING
	_h5_rootdir = DEFAULT_H5_DIRECTORY
	_h5_file_duration  = DEFAULT_H5_FILE_DURATION
	_h5_compressing = DEFAULT_H5_COMPRESSING
	_h5_compression_algo = DEFAULT_H5_COMPRESSION_ALGO
	_h5_gzip_level = DEFAULT_H5_GZIP_LEVEL
	_h5_current_file = None
	_h5_dataset_duration = DEFAULT_H5_SEQUENCE_DURATION
	_h5_dataset_length = int( DEFAULT_H5_SEQUENCE_DURATION * _sampling_frequency )
	_h5_dataset_index = 0
	_h5_dataset_number = int( DEFAULT_H5_FILE_DURATION // DEFAULT_H5_SEQUENCE_DURATION )
	_h5_buffer = None
	_h5_buffer_length = _h5_dataset_length
	_h5_buffer_index = 0
	_h5_timestamp = 0
	_cv_monitoring = DEFAULT_CV_MONITORING
	_cv_codec = DEFAULT_CV_CODEC
	_cv_device = DEFAULT_CV_DEVICE
	_cv_rootdir = DEFAULT_CV_DIRECTORY
	_cv_color_mode = DEFAULT_CV_COLOR_MODE
	_cv_sampling_frequency = DEFAULT_CV_SAMPLING_FREQUENCY
	_cv_show = DEFAULT_CV_SHOW
	_cv_file_duration = DEFAULT_CV_FILE_DURATION

	__cv_thread = None
	__cv_thread_exception: MuException = None
	__cv_running = False

	def __init__( self, usb_vendor_id, usb_vendor_product, usb_bus_address, pluggable_beams_number ):
		"""
		Set properties to default values
		"""
		self._usb_vendor_id = usb_vendor_id
		self._usb_vendor_product = usb_vendor_product
		self._usb_bus_address = usb_bus_address
		self._pluggable_beams_number = pluggable_beams_number

		log.info( f" .MegaMicro({self._system}): created" )


	def __del__( self ):
		log.info( f" .MegaMicro({self._system}): destroyed" )

	@property
	def signal_q( self ):
		return self._signal_q

	@property
	def signal_ts( self ):
		return self._signal_ts

	@property
	def mems( self ):
		return self._mems

	@property
	def mems_number( self ):
		return self._mems_number

	@property
	def analogs( self ):
		return self._analogs

	@property
	def analogs_number( self ):
		return self._analogs_number

	@property
	def counter( self ):
		return self._counter

	@property
	def counter_skip( self ):
		return self._counter_skip

	@property
	def status( self ):
		return self._status

	@property
	def channels_number( self ):
		return self._channels_number

	@property
	def clockdiv( self ):
		return self._clockdiv

	@property
	def start_trig( self ):
		return self._start_trig

	@property
	def sampling_frequency( self ):
		return self._sampling_frequency

	@property
	def buffer_length( self ):
		return self._buffer_length

	@property
	def buffers_number( self ):
		return self._buffers_number

	@property
	def buffer_duration( self ):
		return self._buffer_duration

	@property
	def duration( self ):
		return self._duration

	@property
	def transfers_count( self ):
		return self._transfers_count

	@property
	def datatype( self ):
		return self._datatype

	@property
	def sensibility( self ):
		return MU_MEMS_SENSIBILITY

	@property
	def available_mems( self ):
		return self._available_mems

	@property
	def status( self ):
		return {
			'clockdiv': self._clockdiv,
			'sampling_frequency': self._sampling_frequency,
			'buffer_length': self._buffer_length,
			'buffers_number': self._buffers_number,
			'buffer_duration': self._buffer_duration,
			'duration': self._duration,
			'mems': self._mems,
			'mems_number': self._mems_number,
			'analogs': self._analogs,
			'analogs_number': self._analogs_number,
			'counter': self._counter,
			'counter_skip': self._counter_skip,
			'status': self._status,
			'start_trig': self._start_trig,
			'channels_number': self._channels_number,
			'buffer_words_length': self._buffer_words_length,
			'transfers_count': self._transfers_count,
			'block': self._block,
			'h5_recording': self._h5_recording,
			'h5_rootdir': self._h5_rootdir,
			'h5_dataset_duration': self._h5_dataset_duration,
			'h5_file_duration': self._h5_file_duration,
			'h5_compressing': self._h5_compressing,
			'h5_compression_algo': self._h5_compression_algo,
			'h5_gzip_level': self._h5_gzip_level,
			'cv_monitoring':self._cv_monitoring,
			'cv_codec': self._cv_codec,
			'cv_device': self._cv_device,
			'cv_rootdir': self._cv_rootdir,
			'cv_color_mode': self._cv_color_mode,
			'cv_sampling_frequency': self._cv_sampling_frequency,
			'cv_show': self._cv_show,
			'cv_file_duration': self._cv_file_duration
		}

	@property
	def parameters( self ):
		return {
			'clockdiv': self._clockdiv,
			'sampling_frequency': self._sampling_frequency,
			'buffer_length': self._buffer_length,
			'buffers_number': self._buffers_number,
			'buffer_duration': self._buffer_duration,
			'duration': self._duration,
			'mems': self._mems,
			'available_mems': self.available_mems,
			'mems_number': self._mems_number,
			'analogs': self._analogs,
			'analogs_number': self._analogs_number,
			'counter': self._counter,
			'counter_skip': self._counter_skip,
			'status': self._status,
			'start_trig': self._start_trig,
			'channels_number': self._channels_number,
			'buffer_words_length': self._buffer_words_length,
			'transfers_count': self._transfers_count,
			'block': self._block,
			'h5_recording': self._h5_recording,
			'h5_rootdir': self._h5_rootdir,
			'h5_dataset_duration': self._h5_dataset_duration,
			'h5_file_duration': self._h5_file_duration,
			'h5_compressing': self._h5_compressing,
			'h5_compression_algo': self._h5_compression_algo,
			'h5_gzip_level': self._h5_gzip_level,
			'cv_monitoring':self._cv_monitoring,
			'cv_codec': self._cv_codec,
			'cv_device': self._cv_device,
			'cv_rootdir': self._cv_rootdir,
			'cv_color_mode': self._cv_color_mode,
			'cv_sampling_frequency': self._cv_sampling_frequency,
			'cv_show': self._cv_show,
			'cv_file_duration': self._cv_file_duration
		}

	@property
	def h5_recording( self ):
		return self._h5_recording

	@property
	def h5_rootdir( self ):
		return self._h5_rootdir

	@property
	def h5_dataset_duration( self ):
		return self._h5_dataset_duration

	@property
	def h5_dataset_length( self ):
		return self._h5_dataset_length

	@property
	def h5_file_duration( self ):
		return self._h5_file_duration

	@property
	def h5_compressing( self ):
		return self._h5_compressing

	@property
	def h5_compression_algo( self ):
		return self._h5_compression_algo

	@property
	def h5_gzip_level( self ):
		return self._h5_gzip_level

	@property
	def h5_dataset_number( self ):
		return self._h5_dataset_number

	@property
	def queue_size( self ):
		return self._queue_size


	def disconnect_usb( self ):
		"""
		This command performs a FX3 usb controler reset using the Cypress 0xA0 control command.
		Use only when the Megamicro usb driver is not recognized but only the FX3 Cypress controler.
		Performs like a physical diconnect/connect of the usb cable.  
		Please note that this command shutdown the usb device. Subsequent calls will all raise an USBErrorNoDevice [-4]   
		"""
		log.info( " .Request for disconnecting the usb device. Beware that subsequent call to usb device will fail by throwing a 'USBErrorNoDevice' exception" )
		try:
			with usb1.USBContext() as context:
				"""
				open Usb device and claims interface using the Cypress vendor and product identifiers
				"""	
				handle = context.openByVendorIDAndProductID( 
					MU_CYPRESS_VENDOR_ID,
					MU_CYPRESS_VENDOR_PRODUCT,
					skip_on_error=True,
				)
				if handle is None:
					raise MuException( f"USB3 (Cypress) device is not present or user is not allowed to access device" )
					return
				else:
					log.info( " .USB3 Cypress device successfully opened" )

				with handle.claimInterface( 0 ):
					"""
					Reset FX3
					"""
					log.info( " .Try reseting FX3..." )
					self.ctrlWriteReset( handle, MU_CYPRESS_CMD_FX3_RESET, time_out=1 )
					log.info( " .FX3 reset successfull" )

		except usb1.USBErrorNoDevice as e:
			log.error( f"Catch normal exception following the USB disconnecting request: {e} " )
		except Exception as e:
			log.error( f"USB disconnect failed: {e}" )


	def ctrlCypressResetFx3( self, handle ):
		"""

		"""
		try:
			self.ctrlWriteReset( handle, MU_CYPRESS_CMD_FX3_RESET, time_out=1 )
		except Exception as e:
			log.error( f"Fx3 reset failed: {e}" ) 
			raise


	def check_usb( self, verbose=True ):
		"""
		check for MegaMicro USB plug with verbose mode off
		raise exception if device not found or USB connecting problems
		"""
		if verbose==False:
			with usb1.USBContext() as context:
				handle = context.openByVendorIDAndProductID( 
					self._usb_vendor_id,
					self._usb_vendor_product,
					skip_on_error=True,
				)
				if handle is None:
					raise MuException( 'USB device is not present or user is not allowed to access device' )

				try:
					with handle.claimInterface( 0 ):
						info = {
							"vendor_id": self._usb_vendor_id, 
							"product_id": self._usb_vendor_product,
							"name": handle.getDevice().getProduct(),
							"manufacturer": handle.getDevice().getManufacturer(),
							"serial": handle.getDevice().getSerialNumber(),
							"device_address": handle.getDevice().getDeviceAddress(), 
							"bus": handle.getDevice().getBusNumber(), 
							"port": handle.getDevice().getPortNumber(),
							"speed": handle.getDevice().getDeviceSpeed()
						}

				except Exception as e:	
					raise MuException( f"USB device buzy: cannot claim it: {e}" )

			return info

		"""
		check for MegaMicro USB plug with verbose mode on
		"""
		log.info(' .Checking usb devices...')

		Mu32_device = None
		print( 'Found following devices:' )
		with usb1.USBContext() as context:
			print( '-'*20 )
			for device in context.getDeviceIterator( skip_on_error=True ):
				print( f" .ID {device.getVendorID():04x}:{device.getProductID():04x} {'->'.join(str(x) for x in [' Bus %03i' % (device.getBusNumber(), )] + device.getPortNumberList())} Device {device.getDeviceAddress()}" )
				if device.getVendorID() == self._usb_vendor_id and device.getProductID() == self._usb_vendor_product:
					Mu32_device = device
				if device.getVendorID() == MU_CYPRESS_VENDOR_ID and device.getProductID() == MU_CYPRESS_VENDOR_PRODUCT:
					log.warning( f"Found Cypress device. If USB device is not present you may face to USB connection problem. Please disconnect or run usb soft disconnecting program." )

			print( '-'*20 )
			if Mu32_device is None:
				raise MuException( 'USB device is not present or user is not allowed to access device' )
			else:
				print( f"Found MegaMicro device {Mu32_device.getVendorID():04x}:{Mu32_device.getProductID():04x}")

			"""
			open Usb device and claims interface
			"""	
			handle = context.openByVendorIDAndProductID( 
				self._usb_vendor_id, 
				self._usb_vendor_product,
				skip_on_error=True,
			)

			if handle is None:
				raise MuException( 'USB device is not present or user is not allowed to access device' )
			else:
				print( f"Gain handle on USB device {self._usb_vendor_id:04x}:{self._usb_vendor_product:04x}" )

			try:
				with handle.claimInterface( 0 ):
					pass
			except Exception as e:	
				log.info( f"USB device buzy: cannot claim it: {e}" )
			
			print( '-'*20 )
			print( f"Found following device {Mu32_device.getVendorID():04x}:{Mu32_device.getProductID():04x} characteristics :" )
			print( f"  .Bus number: {Mu32_device.getBusNumber()}" )
			print( f"  .Ports number: {Mu32_device.getPortNumber()}" )
			print( f"  .Device address: {Mu32_device.getDeviceAddress()} ({Mu32_device.getDeviceAddress():04x})" )
			print( f"  .Device name: {Mu32_device.getProduct()}" )
			print( f"  .Manufacturer: {Mu32_device.getManufacturer()}" )
			print( f"  .Serial number: {Mu32_device.getSerialNumber()}" )
			deviceSpeed =  Mu32_device.getDeviceSpeed()
			if deviceSpeed  == libusb1.LIBUSB_SPEED_LOW:
				print( '  .Device speed:  [LOW SPEED] (The OS doesn\'t report or know the device speed)' )
			elif deviceSpeed == libusb1.LIBUSB_SPEED_FULL:
				print( '  .Device speed:  [FULL SPEED] (The device is operating at low speed (1.5MBit/s))' )
			elif deviceSpeed == libusb1.LIBUSB_SPEED_HIGH:
				print( '  .Device speed:  [HIGH SPEED] (The device is operating at full speed (12MBit/s))' )
			elif deviceSpeed == libusb1.LIBUSB_SPEED_SUPER:
				print( '  .Device speed:  [SUPER SPEED] (The device is operating at high speed (480MBit/s))' )
			elif deviceSpeed == libusb1.LIBUSB_SPEED_SUPER_PLUS:
				print( '  .Device speed:  [SUPER PLUS SPEED] (The device is operating at super speed (5000MBit/s))' )
			elif deviceSpeed == libusb1.LIBUSB_SPEED_UNKNOWN:
				print( '  .Device speed:  [LIBUSB_SPEED_UNKNOWN] (The device is operating at unknown speed)' )
			else:
				print( '  .Device speed:  [?] (The device is operating at unknown speed)' )
			print( '-'*20 )

			return {
				"vendor_id": Mu32_device.getVendorID(), 
				"product_id": Mu32_device.getProductID(),
				"name": Mu32_device.getProduct(),
				"manufacturer": Mu32_device.getManufacturer(),
				"serial": Mu32_device.getSerialNumber(),
				"device_address": Mu32_device.getDeviceAddress(), 
				"bus": Mu32_device.getBusNumber(), 
				"port": Mu32_device.getPortNumber(),
				"speed": Mu32_device.getDeviceSpeed()
			}

	def ctrlWrite( self, handle, request, data, time_out=USB_DEFAULT_TIMEOUT, recipient_device=USB_RECIPIENT_DEVICE, type_vendor=USB_REQUEST_TYPE_VENDOR, endpoint_out=USB_ENDPOINT_OUT ):
		"""
		Send a write command to the MegaM%icro FPGA through the usb interface
		"""
		ndata = handle.controlWrite(
						# command type
			recipient_device | type_vendor | endpoint_out,
			request, 	# command
			0,			# command parameter value
			0,			# index
			data,		# data to send 
			time_out 
		)
		if ndata != sizeof( data ):
			log.warning( 'Mu32::ctrlWrite(): command failed with ', ndata, ' data transfered against ', sizeof( data ), ' wanted ' )


	def ctrlWriteReset( self, handle, request, time_out=USB_DEFAULT_TIMEOUT, recipient_device=USB_RECIPIENT_DEVICE, type_vendor=USB_REQUEST_TYPE_VENDOR, endpoint_out=USB_ENDPOINT_OUT ):
		"""
		Send a reset write command to the MegaMicro FPGA through the usb interface.
		This command needs to perform a _controlTransfer() call instead of a controlWrite() call.
		This is because we have no data to transfer (0 length) while the buffer should not be empty.
		controlWrite() computes the data length on its own, that is something >0 conducting to a LIBUSB_ERROR_PIPE [-9] exception throwing
		"""
		data = create_string_buffer( 16 )
		try:
			ndata = handle._controlTransfer(
				recipient_device | type_vendor | endpoint_out, 
				request, 
				0,
				0, 
				data, 
				0,
				time_out,
			)
		except Exception as e:
			log.error( f"reset write failed on device: {e}" )
			raise

		if ndata != 0:
			log.warning( 'Mu32::ctrlWrite(): command failed with ', ndata, ' data transfered against 0 wanted ' )


	def ctrlTixels( self, handle, samples_number ):
		"""
		Set the samples number to be sent by the Mu32 system 
		"""
		buf = create_string_buffer( 5 )
		buf[0] = MU_CMD_COUNT
		buf[1] = bytes(( samples_number & 0x000000ff, ) )
		buf[2] = bytes( ( ( ( samples_number & 0x0000ff00 ) >> 8 ),) )
		buf[3] = bytes( ( ( ( samples_number & 0x00ff0000 ) >> 16 ),) )
		buf[4] = bytes( ( ( ( samples_number & 0xff000000 ) >> 24 ),) )
		self.ctrlWrite( handle, 0xB4, buf )


	def ctrlResetAcq32( self, handle ):
		"""
		Reset and purge fifo
		No documention found about the 0x06 code value. Use ctrlResetMu32() instead for a complete system reset
		"""
		buf = create_string_buffer( 1 )
		buf[0] = MU_CMD_RESET
		self.ctrlWrite( handle, 0xB0, buf )
		buf[0] = MU_CMD_PURGE
		self.ctrlWrite( handle, 0xB0, buf )


	def ctrlResetFx3( self, handle ):
		"""
		Mu32 needs the 0xC4 command but not the 0xC2 unlike what is used on other programs...
		Regarding the Mu32 documentation, this control seems incomplete (/C0/C4/(B0 00)). 
		256 doc says that ctrlResetMu32() is the complete sequence that should be used with fiber (/C0/C4/(B0 00)/C4/C0)
		while ctrlResetFx3() should only be used with USB with non-fiber USB.
		Please use ctrlResetMu32() in all cases
		"""
		try:
			self.ctrlWriteReset( handle, MU_CMD_FX3_RESET, time_out=1 )
			self.ctrlWriteReset( handle, MU_CMD_FX3_PH, time_out=1 )
		except Exception as e:
			log.error( f"Fx3 reset failed: {e}" ) 
			raise


	def ctrlResetMu32( self, handle ):
		"""
		full reset of Mu32 receiver using fiber or not
		"""
		buf = create_string_buffer( 1 )
		buf[0] = MU_CMD_RESET
		try:
			self.ctrlWriteReset( handle, MU_CMD_FX3_RESET, time_out=1 )
			time.sleep( DEFAULT_TIME_ACTIVATION_RESET )
			self.ctrlWriteReset( handle, MU_CMD_FX3_PH, time_out=1 )
			time.sleep( DEFAULT_TIME_ACTIVATION_RESET )
			self.ctrlWrite( handle, MU_CMD_FPGA_0, buf )
			time.sleep( DEFAULT_TIME_ACTIVATION_RESET )
			self.ctrlWriteReset( handle, MU_CMD_FX3_PH, time_out=1 )
			time.sleep( DEFAULT_TIME_ACTIVATION_RESET )
			self.ctrlWriteReset( handle, MU_CMD_FX3_RESET, time_out=1 )
			time.sleep( DEFAULT_TIME_ACTIVATION_RESET )
		except Exception as e:
			log.error( f"Mu32 reset failed: {e}" ) 
			raise

	def ctrlResetFPGA( self, handle ):
		"""
		reset of FPGA
		"""
		buf = create_string_buffer( 1 )
		buf[0] = MU_CMD_RESET
		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_0, buf )
		except Exception as e:
			log.error( f"FPGA reset failed: {e}" ) 
			raise


	def ctrlClockdiv( self, handle, clockdiv=0x09, time_activation=DEFAULT_TIME_ACTIVATION ):
		"""
		Init acq32: set sampling frequency and supplies power to microphones 
		"""
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_INIT
		buf[1] = clockdiv
		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_1, buf )
		except Exception as e:
			log.error( f"Mu32 clock setting and powerwing on microphones failed: {e}" ) 
			raise	

		"""
		wait for mems activation
		"""
		time.sleep( time_activation )


	def ctrlDatatype( self, handle, datatype='int32' ):
		"""
		Set datatype
		! note that float32 is not considered -> TO DO
		""" 
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_DATATYPE
		if datatype=='int32':
			buf[1] = MU_CODE_DATATYPE_INT32
		elif datatype=='float32':
			buf[1] = MU_CODE_DATATYPE_FLOAT32
		else:
			raise MuException( 'Mu32::ctrlDatatype(): Unknown data type [%s]. Please, use [int32] or [float32]' % datatype )

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_1, buf )
		except Exception as e:
			log.error( f"Mu32 datatype setting failed: {e}" ) 
			raise	

	def ctrlMems( self, handle, request, beams_number, mems='all' ):
		"""
		Activate or deactivate MEMs
		"""
		try:
			buf = create_string_buffer( 4 )
			buf[0] = MU_CMD_ACTIVE		
			buf[1] = 0x00					# module
			if mems == 'all':
				if request == 'activate':
					for beam in range( beams_number ):
						buf[2] = beam		# beam number
						buf[3] = 0xFF		# active MEMs map
						self.ctrlWrite( handle, MU_CMD_FPGA_3, buf )
				elif request == 'deactivate':
					for beam in range( beams_number ):
						buf[2] = beam		
						buf[3] = 0x00		
						self.ctrlWrite( handle, MU_CMD_FPGA_3, buf )
				else:
					raise MuException( 'In Mu32::ctrlMems(): Unknown parameter [%s]' % request )
			else:
				if request == 'activate':
					map_mems = [0 for _ in range( beams_number )]
					for mic in mems:
						mic_index = mic % MU_BEAM_MEMS_NUMBER
						beam_index = int( mic / MU_BEAM_MEMS_NUMBER )
						if beam_index >= beams_number:
							raise MuException( 'microphone index [%d] is out of range (should be less than %d)' % ( mic,  beams_number*MU_BEAM_MEMS_NUMBER ) )
						map_mems[beam_index] += ( 0x01 << mic_index )

					for beam in range( beams_number ):
						if map_mems[beam] != 0:
							buf[2] = beam
							buf[3] = map_mems[beam]				
							self.ctrlWrite( handle, MU_CMD_FPGA_3, buf )
				else:
					raise MuException( 'In Mu32::ctrlMems(): request [%s] is not implemented' % request )
		except Exception as e:
			log.error( f"Mu32 microphones activating failed: {e}" ) 
			raise	


	def ctrlCSA( self, handle, counter, status, analogs ):
		"""
		Activate or deactivate analogic, status and counter channels
		"""		
		buf = create_string_buffer( 4 )
		buf[0] = MU_CMD_ACTIVE		# command
		buf[1] = 0x00				# module
		buf[2] = 0xFF				# counter, status and analogic channels

		map_csa = 0x00
		if len( analogs ) > 0:
			for anl_index in analogs:
				map_csa += ( 0x01 << anl_index ) 
		if status:
			map_csa += ( 0x01 << 6 )
		if counter:
			map_csa += ( 0x01 << 7 )

		buf[3] = map_csa

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_3, buf )
		except Exception as e:
			log.error( f"Mu32 analogic channels and status activating failed: {e}" ) 
			raise	


	def ctrlStart( self, handle ):
		"""
		start acquiring by soft triggering
		"""
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_START
		buf[1] = 0x00

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_1, buf )
		except Exception as e:
			log.error( f"Mu32 starting failed: {e}" ) 
			raise	

	def ctrlStartTrig( self, handle ):
		"""
		start acquiring by external triggering
		"""
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_START
		buf[1] = 0x01										# front montant 
		#buf[1] = 0x01 + ( 0x01 << 7 )						# (état haut)

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_1, buf )
		except Exception as e:
			log.error( f"Mu32 starting by external trig failed: {e}" ) 
			raise	

	def ctrlStop( self, handle ):
		"""
		stop acquiring by soft triggering
		"""
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_STOP
		buf[1] = 0x00

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_1, buf )
		except Exception as e:
			log.error( f"Mu32 stop failed: {e}" ) 
			raise


	def ctrlPowerOffMic( self, handle ):
		"""
		powers off microphones
		"""
		buf = create_string_buffer( 2 )
		buf[0] = MU_CMD_RESET

		try:
			self.ctrlWrite( handle, MU_CMD_FPGA_0, buf )
		except Exception as e:
			log.error( f"Mu32 microphones powering off failed: {e}" ) 
			raise	


	def processFlush( self, transfer ):
		"""
		Callback flushing function: only intended to flush MegaMicro internal buffers
		"""
		if transfer.getActualLength() > 0:
			log.info( f" .flushed {transfer.getActualLength()} data bytes from transfer buffer [{transfer.getUserData()}]" )


	def processRun( self, transfer ):
		"""
		Callback run function: check transfer error, call user callback function and submit next transfer
		"""

		"""
		Get current timestamp as it was at transfer start
		"""
		transfer_timestamp = time.time() - self._buffer_duration

		if self._restart_request == True:
			"""
			A request for restart has been sent -> do nothing and do not submit new transfer
			"""
			return

		if transfer.getStatus() != usb1.TRANSFER_COMPLETED:
			"""
			Transfer not completed -> skip data transfer without runing user callback
			Data is lost, if anay
			"""
			if transfer.getStatus() == usb1.TRANSFER_CANCELLED:
				log.info( f" .transfer [{transfer.getUserData()}] cancelled." )
			elif transfer.getStatus() == usb1.TRANSFER_NO_DEVICE:
				log.critical( f"transfer [{transfer.getUserData()}]: no device. Exit skiping callback run." )
			elif transfer.getStatus() == usb1.TRANSFER_ERROR:
				log.error( f"transfer [{transfer.getUserData()}] error. Exit skiping callback run." )
			elif transfer.getStatus() == usb1.TRANSFER_TIMED_OUT:
				if self._start_trig:
					"""
					This may due to trigger signal not send -> nothing to do but waiting for it...
					"""
					log.warning( f"transfer [{transfer.getUserData()}] timed out. Waiting for external starting trigger signal..." )
					if( self._recording ):
						try:
							transfer.submit()
						except Exception as e:
							log.error( f"Mu32: transfer submit failed: {e}. Aborting..." )
							self._recording = False
					return
				else:
					log.error( f"transfer [{transfer.getUserData()}] timed out. Exit skiping callback run." )
			elif transfer.getStatus() == usb1.TRANSFER_STALL:
				log.error( f"transfer [{transfer.getUserData()}] stalled. Exit skiping callback run." )
			elif transfer.getStatus() == usb1.TRANSFER_OVERFLOW:
				log.error( f"transfer [{transfer.getUserData()}] overflow. Exit skiping callback run." )
			else:
				log.error( f"transfer [{transfer.getUserData()}] unknown error. Exit skiping callback run." )
				
			self._recording = False
			return


		"""
		get data from buffer
		"""
		data = np.frombuffer( transfer.getBuffer()[:transfer.getActualLength()], dtype=np.int32 )

		if len( data ) != self._buffer_words_length:
			"""
			buffer is not fully completed. Some data are missing
			try again anyway but skip the user process callback call. Current data is lost
			"""
			log.warning( f" .lost {self._buffer_words_length - len( data )} lost samples. Retry transfer" )
			if( self._recording ):
				try:
					transfer.submit()
				except Exception as e:
					log.error( f"transfer submit failed: {e}" )
					self._recording = False
			return

		if self._counter:
			"""
			counter flag is True: performs data control such as to know if some data have been lost
			This usually appears when user callback function takes too long.
			Control is done by substracting the frame last counter value with the frame first counter value. Result should be equal to the buffer size in samples number
			Beware that, if not, it means that samples have been lost or, whorst than that, data is no longer aligned in which case this difference no longer makes sense.
			Do not submit next transfer but leave the recording flag to True. 
			At the main loop level this will suggest to retry after having reset the FX3 (data Misalignement seems to come from the FX3 USB controler.)
			"""
			ctrl_buffer_length = data[self._buffer_words_length-self._channels_number] - data[0] + 1
			if ctrl_buffer_length != self._buffer_length:
				log.warning( f"from transfer[{transfer.getUserData()}]: data has been lost. Send a restart request...")
				log.info( f" .last known counter value: {self._counter_state}")
				self._restart_request = True
				return

			"""
			All seems correct -> continue
			save current counter value and reset attempt counter if needed
			"""
			self._previous_counter_state = self._counter_state
			self._counter_state = data[self._buffer_words_length-self._channels_number]
			if self._counter_state - self._previous_counter_state > self._buffer_length and self._previous_counter_state != 0:
				log.info( f" .{self._counter_state - self._previous_counter_state - self._buffer_length} samples lost it seems.")

			self._restart_attempt = 0

		data = np.reshape( data, ( self._buffer_length, self._channels_number ) ).T

		if self._counter and self._counter_skip:
			"""
			Remove counter signal
			"""
			data = data[1:,:]

		"""
		Proceed to buffer recording in h5 file if requested
		"""
		if self._h5_recording:
			try:
				self.h5_write_mems( data, transfer_timestamp )
			except Exception as e:
				log.error( f"Mu32: H5 writing process failed: {e}. Aborting..." )
				self._recording = False

		"""
		Call user callback processing function if any.
		Otherwise push data and timestamp in the object signal queues
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
			if self._queue_size > 0 and self._signal_q.qsize() >= self._queue_size:
				"""
				Queue size is limited and filled -> delete older element before queuing new:  
				"""
				self._signal_q.get()
			self._signal_q.put( data )

		"""
		Resubmit transfer once data is processed and while recording mode is on
		"""
		if( self._recording ):
			try:
				transfer.submit()
			except Exception as e:
				log.error( f"Mu32: transfer submit failed: {e}. Aborting..." )
				self._recording = False

		"""
		Control duration and stop acquisition if the transfer count is reach
		_transfers_count set to 0 means the acquisition is infinite loop
		"""
		self._transfer_index += 1
		if self._transfers_count != 0 and  self._transfer_index > self._transfers_count:
			self._recording = False
	

	def run_setargs( self, kwargs ):
		"""
		Set MegaMicro property values with priority order given to arguments (if given), parameter list (if given) and then defaults values.

		:param clockdiv: decide for the sampling frequency. The sampling frequency is given by int( 500000/( clockdiv+1 ) ).Ex: 0x09 set for 50kHz
		:param buffers_number: the number of buffers used by the USB device for the data bulk transfer. It can be set from 1 to n>1 (default is given by MU_DEFAULT_BUFFERS_NUMBER)
		:param buffer_length: the number of samples that will be sent for each microphone by the Mu32 system in each transfer buffer. buffers_number_number and buffer_length have effects on latence and real time capabilities
		:param duration: the desired recording time in seconds
		"""

		"""
		Set default values
		"""
		sampling_frequency = DEFAULT_SAMPLING_FREQUENCY
		buffers_number = DEFAULT_BUFFERS_NUMBER
		buffer_length = DEFAULT_BUFFER_LENGTH
		duration = DEFAULT_DURATION
		datatype = DEFAULT_DATATYPE
		mems = DEFAULT_ACTIVATED_MEMS
		analogs = DEFAULT_ACTIVATED_ANALOG
		counter = DEFAULT_ACTIVATED_COUNTER
		counter_skip = DEFAULT_COUNTER_SKIPPING
		status = DEFAULT_ACTIVATED_STATUS
		start_trig = DEFAULT_START_TRIG
		block = DEFAULT_BLOCK_FLAG
		queue_size = DEFAULT_QUEUE_SIZE
		callback_fn = None
		post_callback_fn = None

		h5_recording = DEFAULT_H5_RECORDING
		h5_rootdir = DEFAULT_H5_DIRECTORY
		h5_dataset_duration = DEFAULT_H5_SEQUENCE_DURATION
		h5_file_duration = DEFAULT_H5_FILE_DURATION
		h5_compressing = DEFAULT_H5_COMPRESSING
		h5_compression_algo = DEFAULT_H5_COMPRESSION_ALGO
		h5_gzip_level = DEFAULT_H5_GZIP_LEVEL

		cv_monitoring = DEFAULT_CV_MONITORING
		cv_codec = DEFAULT_CV_CODEC
		cv_device = DEFAULT_CV_DEVICE
		cv_rootdir = DEFAULT_CV_DIRECTORY
		cv_color_mode = DEFAULT_CV_COLOR_MODE
		cv_sampling_frequency = DEFAULT_CV_SAMPLING_FREQUENCY
		cv_show = DEFAULT_CV_SHOW
		cv_file_duration = DEFAULT_CV_FILE_DURATION

		if len( kwargs ) == 0:
			"""
			No argument provided -> perform autotest
			"""
			post_callback_fn = self.autotest
			mems = [i for i in range( self._pluggable_beams_number*MU_BEAM_MEMS_NUMBER )]


		if 'parameters' in kwargs:
			"""
			Update with parameter list dicionnary content
			"""
			parameters = kwargs['parameters']
			if 'sampling_frequency' in parameters:
				sampling_frequency = parameters.get( 'sampling_frequency' )
			if 'buffers_number' in parameters:
				buffers_number = parameters.get( 'buffers_number' )
			if 'buffer_length' in parameters:
				buffer_length = parameters.get( 'buffer_length' )
			if 'duration' in parameters:
				duration = parameters.get( 'duration' )
			if 'datatype' in parameters:
				datatype = parameters.get( 'datatype' )
			if 'mems' in parameters:
				mems = parameters.get( 'mems' )
			if 'analogs' in parameters:
				analogs = parameters.get( 'analogs' )
			if 'counter' in parameters:
				counter = parameters.get( 'counter' )		
			if 'counter_skip' in parameters:
				counter_skip = parameters.get( 'counter_skip' )		
			if 'status' in parameters:
				status = parameters.get( 'status' )
			if 'start_trig' in parameters:
				start_trig = parameters.get( 'start_trig' )			
			if 'block' in parameters:
				block = parameters.get( 'block' )
			if 'queue_size' in parameters:
				queue_size = parameters.get( 'queue_size')

			if 'h5_recording' in parameters:
				h5_recording = parameters.get( 'h5_recording' )
			if 'h5_rootdir' in parameters:
				h5_rootdir = parameters.get( 'h5_rootdir' )	
			if 'h5_seq_duration' in parameters:
				h5_dataset_duration = parameters.get( 'h5_dataset_duration' )
			if 'h5_file_duration' in parameters:
				h5_file_duration = parameters.get( 'h5_file_duration' )	
			if 'h5_compressing' in parameters:
				h5_compressing = parameters.get( 'h5_compressing' )	
			if 'h5_compression_algo' in parameters:
				h5_compression_algo = parameters.get( 'h5_compression_algo' )	
			if 'h5_gzip_level' in parameters:
				h5_gzip_level = parameters.get( 'h5_gzip_level' )

			if 'cv_monitoring' in parameters:
				cv_monitoring = parameters.get( 'cv_monitoring' )				
			if 'cv_codec' in parameters:
				cv_codec = parameters.get( 'cv_codec' )				
			if 'cv_device' in parameters:
				cv_device = parameters.get( 'cv_device' )				
			if 'cv_rootdir' in parameters:
				cv_rootdir = parameters.get( 'cv_rootdir' )				
			if 'cv_color_mode' in parameters:
				cv_color_mode = parameters.get( 'cv_color_mode' )				
			if 'cv_sampling_frequency' in parameters:
				cv_sampling_frequency = parameters.get( 'cv_sampling_frequency' )
			if 'cv_show' in parameters:
				cv_show = parameters.get( 'cv_show' )
			if 'cv_file_duration' in parameters:
				cv_file_duration = parameters.get( 'cv_file_duration' )


		"""
		Update with run() arguments
		"""
		if 'sampling_frequency' in kwargs: sampling_frequency = kwargs['sampling_frequency']
		if 'buffers_number' in kwargs: buffers_number = kwargs['buffers_number']
		if 'buffer_length' in kwargs: buffer_length = kwargs['buffer_length']
		if 'duration' in kwargs: duration = kwargs['duration']
		if 'datatype' in kwargs: datatype = kwargs['datatype']
		if 'mems' in kwargs: mems = kwargs['mems']
		if 'analogs' in kwargs: analogs = kwargs['analogs']
		if 'counter' in kwargs: counter = kwargs['counter']
		if 'counter_skip' in kwargs: counter_skip = kwargs['counter_skip']
		if 'status' in kwargs: status = kwargs['status']
		if 'start_trig' in kwargs: start_trig = kwargs['start_trig']
		if 'post_callback_fn' in kwargs: post_callback_fn = kwargs['post_callback_fn']
		if 'callback_fn' in kwargs: callback_fn = kwargs['callback_fn']
		if 'block' in kwargs: block = kwargs['block']
		if 'queue_size' in kwargs: queue_size = kwargs['queue_size']

		if 'h5_recording' in kwargs: h5_recording = kwargs['h5_recording']
		if 'h5_rootdir' in kwargs: h5_rootdir = kwargs['h5_rootdir']
		if 'h5_dataset_duration' in kwargs: h5_dataset_duration = kwargs['h5_dataset_duration']
		if 'h5_file_duration' in kwargs: h5_file_duration = kwargs['h5_file_duration']
		if 'h5_compressing' in kwargs: h5_compressing = kwargs['h5_compressing']
		if 'h5_compression_algo' in kwargs: h5_compression_algo = kwargs['h5_compression_algo']
		if 'h5_gzip_level' in kwargs: h5_gzip_level = kwargs['h5_gzip_level']

		if 'cv_monitoring' in kwargs: cv_monitoring = kwargs['cv_monitoring']
		if 'cv_codec' in kwargs: cv_codec = kwargs['cv_codec']
		if 'cv_device' in kwargs: cv_device = kwargs['cv_device']
		if 'cv_rootdir' in kwargs: cv_directory = kwargs['cv_rootdir']
		if 'cv_color_mode' in kwargs: cv_color_mode = kwargs['cv_color_mode']
		if 'cv_sampling_frequency' in kwargs: cv_sampling_frequency = kwargs['cv_sampling_frequency']
		if 'cv_show' in kwargs: cv_show = kwargs['cv_show']
		if 'cv_file_duration' in kwargs: cv_file_duration = kwargs['cv_file_duration']

		"""
		Set atributes
		"""
		self._clockdiv = max( int( 500000 / sampling_frequency ) - 1, 9 )
		self._sampling_frequency = 500000 / ( self._clockdiv + 1 )
		self._buffer_length = buffer_length
		self._buffers_number = buffers_number
		self._datatype = datatype
		self._buffer_duration = self._buffer_length / self._sampling_frequency
		self._duration = duration
		self._mems = mems
		self._mems_number = len( self._mems )
		self._analogs = analogs
		self._analogs_number = len( self._analogs )
		self._counter = counter
		self._counter_skip = counter_skip
		self._status = status
		self._start_trig = start_trig
		self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
		self._buffer_words_length = self._channels_number*self._buffer_length
		self._transfers_count = int( ( self._duration * self._sampling_frequency ) // self._buffer_length )
		self._post_callback_fn = post_callback_fn
		self._callback_fn = callback_fn
		self._block = block
		self._queue_size = queue_size

		self._h5_recording = h5_recording
		self._h5_rootdir = h5_rootdir
		self._h5_dataset_duration = h5_dataset_duration
		self._h5_file_duration = h5_file_duration
		self._h5_dataset_number = int( h5_file_duration // h5_dataset_duration )
		self._h5_compressing = h5_compressing
		self._h5_compression_algo = h5_compression_algo
		self._h5_gzip_level = h5_gzip_level

		self._cv_monitoring = cv_monitoring
		self._cv_codec = cv_codec
		self._cv_device = cv_device
		self._cv_rootdir = cv_rootdir
		self._cv_color_mode = cv_color_mode
		self._cv_sampling_frequency = cv_sampling_frequency
		self._cv_show = cv_show
		self._cv_file_duration = cv_file_duration


	def run( self, **kwargs ):
		"""
		Run is a generic acquisition method that get signals from the activated MEMs

		:param sampling_fequency: sampling frequency. Default is set to max value 50000Hz
		:type sampling_frequency: float
		"""

		self.run_setargs( kwargs )

		try:
			"""
			Do some controls and print recording parameters
			"""
			if self._system==MU32_SYSTEM_NAME and self._analogs_number > 0:
				log.warning( f"Mu32: {self._analogs_number} analogs channels were activated while they are not supported on {self._system} device -> unselecting")
				self._analogs = []
				self._analogs_number = 0
				self._channels_number = self._mems_number + self._analogs_number + self._counter + self._status
				self._buffer_words_length = self._channels_number*self._buffer_length

			log.info( f" .MegaMicro({self._system}): start running acquisition..." )

			if self._datatype != 'int32' and self._datatype != 'float32':
				raise MuException( 'Unknown datatype [%s]' % self._datatype )
			self._datatype = self._datatype

			if self._sampling_frequency > 50000:
				log.warning( 'Mu32: desired sampling frequency [%s Hz] is greater than the max admissible sampling frequency. Adjusted to 50kHz' % self._sampling_frequency )
			else:
				log.info( ' .sampling frequency: %d Hz' % self._sampling_frequency )

			if self._counter_skip and not self._counter:
				log.warning( 'Mu32: cannot skip counter in the absence of counter (counter flag is off)' )

			if self._cv_monitoring:
				"""
				Start video monitoring if requested
				"""
				log.info( f" .Video monitoring: ON" )
				self.__cv_running = True
				self.__cv_thread = threading.Thread( target = self.cv_monitor_loop )
				self.__cv_thread.start()
			else:
				log.info( f" .Video monitoring: OFF" )

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


	def wait( self ):
		"""
		wait for thread termination (blocking call)
		"""
		if self._block:
			log.warning( "wait() should not be used in blocking mode" )
			return

		self._transfer_thread.join()
		if self._transfer_thread_exception:
			if self._cv_monitoring:
				self.__cv_running = False
				self.__cv_thread.join()
			raise self._transfer_thread_exception

		if self._cv_monitoring:
			self.__cv_running = False
			self.__cv_thread.join()
			if self.__cv_thread_exception:
				raise self.__cv_thread_exception


	def is_alive( self ):
		"""
		chack if thread is always running (non blocking call)
		"""
		if self._block:
			log.warning( "is_alive() should not be used in blocking mode" )
			return
		
		return self._transfer_thread.is_alive()


	def stop( self ):
		"""
		Stop the transfer loop
		"""
		self._recording = False

		"""
		Stop monitoring if any
		"""
		if self._cv_monitoring:
			self.__cv_running = False

	def cv_monitor_loop( self ):

		log.info( f" .Starting video monitoring thread..." )

		"""
		Set filename
		"""
		date = datetime.now()
		timestamp0 = date.timestamp()
		date0str = datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')
		abs_path = os.path.abspath( self._cv_rootdir )
		filename = os.path.join( abs_path, 'muVideo-' + f"{date.year}{date.month:02}{date.day:02}-{date.hour:02}{date.minute:02}{date.second:02}" + '.mp4' )

		"""
		Init video
		"""
		try:
			self.cv_log_info()

			cap = cv.VideoCapture( self._cv_device )
			if not cap.isOpened():
				raise MuException( f"Video camera initialization failed" )

			width = int( cap.get( cv.CAP_PROP_FRAME_WIDTH ) )
			height = int( cap.get( cv.CAP_PROP_FRAME_HEIGHT ) )
			log.info( f" .Video frame size: {width} x {height} pixels" )

			fourcc = cv.VideoWriter_fourcc( *self._cv_codec )   # .mp4
			log.info( f" .Video codec: {self._cv_codec}" )

			file_frame_nbr = int( self._cv_sampling_frequency * self._cv_file_duration )
			log.info( f" .Video file frames number: {file_frame_nbr}" )

			out = cv.VideoWriter( filename, fourcc, self._cv_sampling_frequency, (width,  height), isColor=False )
			log.info( f" .Video create new file: {filename}" )


		except Exception as e:
			self.__cv_thread_exception = MuException( f"Video thread failed during initialization: {e}" )
			log.info( f" .Exiting from monitoring thread on error: {e}" )
			return

		"""
		Start loop
		"""
		try:
			frame_number = 0
			while self.__cv_running and cap.isOpened():
				ret, frame = cap.read()
				if not ret:
					raise MuException( f"Can't receive video frame (stream end?). Exiting ..." )
				frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
				if frame_number >= file_frame_nbr:
					"""
					Open a new file
					"""
					out.release()
					date = datetime.now()
					abs_path = os.path.abspath( self._cv_rootdir )
					filename = os.path.join( abs_path, 'muVideo-' + f"{date.year}{date.month:02}{date.day:02}-{date.hour:02}{date.minute:02}{date.second:02}" + '.mp4' )
					out = cv.VideoWriter( filename, fourcc, self._cv_sampling_frequency, (width,  height), isColor=False )
					log.info( f" .Video create new file: {filename}" )
					frame_number = 0

				out.write( frame )
				if self._cv_show:
					cv.imshow( 'frame', frame )
				frame_number += 1

		except Exception as e:
			self.__cv_thread_exception = MuException( f"Video thread failed during monitoring loop: {e}" )
			cap.release()
			out.release()
			cv.destroyAllWindows()
			log.info( f" .Exiting from monitoring thread on error: {e}" )
			return

		"""
		Job is finished -> release everything
		"""
		cap.release()
		out.release()
		cv.destroyAllWindows()
		log.info( f" .Video monitoring thread stopped" )


	def cv_log_info( self ):
		"""
		Log requested parameter values about video monitoring
		"""
		log.info( f" .Video codec: {self._cv_codec}" )
		log.info( f" .Video device: {self._cv_device}" )
		log.info( f" .Video recording directory: {self._cv_rootdir}" )
		log.info( f" .Video colormode is: {self._cv_color_mode}" )
		log.info( f" .Video frame frequency: {self._cv_sampling_frequency}" )
		log.info( f" .Video showing video stream: {self._cv_show}" )
		log.info( f" .Video files duration: {self._cv_file_duration}s" )


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
		log.info( f" .buffer length in 32 bits words number: {self._buffer_length}x{self._channels_number}={self._buffer_words_length} ({self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE} bytes)" )
		log.info( f" .buffer duration in seconds: {self._buffer_duration}" )
		log.info( f" .minimal transfers count: {self._transfers_count}" )
		log.info( f" .multi-threading execution mode: {not self._block}" )
		log.info( f" .starting from external triggering: {'True' if self._start_trig else 'False'}" )

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
			log.info( f" .H5 recording: ON" )
			self.h5_log_info()
		else:
			log.info( f" .H5 recording: OFF" )

		with usb1.USBContext() as context:
			"""
			open Usb device and claims interface
			"""	
			handle = context.openByVendorIDAndProductID( 
				self._usb_vendor_id,
				self._usb_vendor_product,
				skip_on_error=True,
			)
			if handle is None:
				self._transfer_thread_exception = MuException( f"USB3 device for {self._system} system is not present or user is not allowed to access device" )
				return

			try:
				with handle.claimInterface( 0 ):
					"""
					init Mu32 and send acquisition starting command
					Note that counter is always selected for control purpose. This channel won't be reported if user do not select COUNTER 
					"""
					self.ctrlResetMu32( handle)
					self.ctrlClockdiv( handle, self._clockdiv, DEFAULT_TIME_ACTIVATION )
					self.ctrlTixels( handle, 0 )
					self.ctrlDatatype( handle, self._datatype )
					self.ctrlMems( handle, request='activate', mems=self._mems )
					self.ctrlCSA( handle, counter=self._counter, status=self._status, analogs=self._analogs )
					if self._start_trig:
						self.ctrlStartTrig( handle )
					else:
						self.ctrlStart( handle )

					"""
					Open H5 file if recording on 
					"""
					if self._h5_recording:
						self.h5_init()

					"""
					Allocate the list of transfer objects
					"""
					transfer_list = []
					for id in range( self.buffers_number ):
						transfer = handle.getTransfer()
						transfer.setBulk(
							usb1.ENDPOINT_IN | self._usb_bus_address,
							self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE,
							callback=self.processRun,
							user_data = id,
							timeout=DEFAULT_TRANSFER_TIMEOUT
						)
						transfer_list.append( transfer )
						transfer.submit()
						
					"""
					Recording loop
					"""
					self._transfer_index = 0
					self._counter_state = self._previous_counter_state = 0
					self._recording = True
					self._restart_request = False

					log.info( f" .start acquisition..." )
					while self._recording == True:
						"""
						Attemps loop while recording is open
						"""
						while any( x.isSubmitted() for x in transfer_list ):
							"""
							Main recording loop.
							Waits for pending tranfers while there are any.
							Once a transfer is finished, handleEvents() trigers callback  
							"""
							try:
								context.handleEvents()
							except KeyboardInterrupt:
								log.info( f" .Keyboard interrupting..." )
								self._recording = False	
							except usb1.USBErrorInterrupted:
								log.errort( f"Mu32: USB error interrupting..." )
								self._recording = False
							except Exception as e:
								log.error( f"Mu32: unexpected error {e}. Aborting..." )
								self._recording = False
						
						if self._restart_request and self._recording:
							"""
							Exit loop while recording flag is still True.
							It means that packets have been lost (this is a restart request).
							Retry after having reset FX3
							"""
							self._restart_attempt += 1
							if self._restart_attempt == 1:
								log.info( " .restart device..." )
							elif self._restart_attempt >1 and self._restart_attempt < DEFAULT_MAX_RETRY_ATTEMPT:
								log.info( f" .restart device... [{self._restart_attempt} times]" )
							else:
								log.error( f"Mu32: device restart failed {self._restart_attempt} times -> aborting..." )
								self._recording = False
								self._restart_request = False
								break
							
							self.ctrlResetFx3( handle )
							log.info( " .transfer restarting..." )
							self._restart_request = False
							for transfer in transfer_list:
								transfer.submit()

						else:
							log.info( f" .quitting recording loop" )

					"""
					Stop recording
					"""
					if self._h5_recording:
						self.h5_close()

					"""
					After loop processing
					Attempt to cancel transfers that could be yet pending
					"""
					for transfer in transfer_list:
						if transfer.isSubmitted():
							log.info( f" .cancelling transfer [{transfer.getUserData()}] (may takes a while) ..." )
							try:
								transfer.cancel()
							except:
								pass
					
					while any( x.isSubmitted() for x in transfer_list ):
						try:
							context.handleEvents()
						except:
							pass

					log.info( f" .cancelling transfer [done]" )

					"""
					Send stop command to Mu32 FPGA
					"""
					self.ctrlStop( handle )

					"""
					Flush Mu32 remaining data from buffers
					"""
					log.info( f" .flushing buffers..." )
					for id in range( self.buffers_number ):
						transfer = transfer_list[id]
						if not transfer.isSubmitted():
							transfer.setBulk(
								usb1.ENDPOINT_IN | self._usb_bus_address,
								self._buffer_words_length*MU_TRANSFER_DATAWORDS_SIZE,
								callback=self.processFlush,
								user_data = id,
								timeout=10
							)
							try:
								transfer.submit()
							except Exception as e:
								log.info( f" .transfer [{transfer.getUserData()}] flushing failed: {e}" )

					while any( x.isSubmitted() for x in transfer_list ):
						try:
							context.handleEvents()
						except :
							pass

					log.info( f" .flushing [done]" )
					
					"""
					Reset Mu32 and powers off microphones
					"""
					self.ctrlResetMu32( handle)

			except Exception as e:
				self._transfer_thread_exception = MuException( f"Mu32 USB3 run failed: [{e}]" )
				return


		log.info( ' .end of acquisition' )

		"""
		Call the final callback user function if any 
		"""
		if self._post_callback_fn != None:
			log.info( ' .data post processing...' )
			self._post_callback_fn( self )


	def autotest( self, mu32 ):
		""" 
		post processing callback function for autotesting the Mu32 system 
		"""

		q_size = self.signal_q.qsize()
		if q_size== 0:
			raise MuException( 'Processing autotest: No received data !' )		

		signal = self.signal_q.get()
		while not self.signal_q.empty():
			signal = np.append( signal, self.signal_q.get(), axis=1 )

		"""
		compute mean energy
		"""
		mic_power = np.sum( signal**2, axis=1 )
		n_samples = np.size( signal, 1 )
			
		print( 'Autotest results:')
		print( '-'*20 )
		print( f" .counted {q_size} recorded data buffers" )
		print( f" .equivalent recording time is: {n_samples / mu32.sampling_frequency} " )
		print( f" .detected {len( np.where( mic_power > 0 )[0] )} active MEMs: {np.where( mic_power > 0 )[0]}" )
		print( '-'*20 )

		"""
		Save available mems 
		"""
		mu32._available_mems = np.where( mic_power > 0 )[0].tolist()


	def callback_power( self, mu32, data: np.ndarray ):
		""" 
		Compute energy (mean power) on transfered frame
		"""
		signal = data * self.sensibility
		mean_power = np.sum( signal**2, axis=1 ) / self.buffer_length

		self.signal_q.put( mean_power )


	def save ( self, filename ):
		"""
		Save the current signal queue in H5 file.
		The acquisition should be endded before call.
		Saving process empties the queue so that data are no more available after.
		"""
		#if not os.path.isfile( filename ):
		#	raise MuException( f"H5 file {filename} not found" )

		if self.signal_q.empty():
			raise MuException( f"Unable to save data: Signal queue is empty" )

		"""
		Get queued signal
		"""
		signal = self.signal_q.get()
		while not self.signal_q.empty():
			signal = np.append( signal, self.signal_q.get(), axis=1 )

		"""
		Open hdf5 file, write data and add attributes
		"""
		with h5py.File( filename, "w" ) as f:
			# creata the data set:
			dataset = f.create_dataset( "megamicro", ( self._channels_number - int(self._counter and self._counter_skip), np.size(signal, 1) ), dtype=self.datatype )

			# write data:
			dataset[:] = signal

			# write attributes:
			dataset.attrs['parameters'] = self.parameters


	def h5_log_info( self ):
		"""
		Log info about H5 file system
		"""
		h5_dataset_length = int( self._h5_dataset_duration * self._sampling_frequency )
		h5_dataset_size = h5_dataset_length * self.channels_number * MU_TRANSFER_DATAWORDS_SIZE
		h5_file_samples_number = h5_dataset_length * self._h5_dataset_number
		log.info( f" .H5 directory: `{self._h5_rootdir}`" )
		log.info( f" .H5 dataset length is: {h5_dataset_length} samples ({self._h5_dataset_duration}s)" )
		log.info( f" .H5 dataset size: {h5_dataset_size/1024/1024} Mo" )
		log.info( f" .H5 file maximum length: {h5_file_samples_number} samples ({self._h5_file_duration}s)")
		if self._h5_compressing:
			log.info( f" .H5 compression: ON (algo is {self._h5_compression_algo})" )
			if self._h5_compression_algo == 'gzip':
				log.info( f" .H5 compression level (0 to 9): {self._h5_gzip_level}")
		else:
			log.info( f" .H5 compression: OFF" )


	def h5_init( self ):
		"""
		Init H5 file system.
		Organization of H5 file is as follows (fs of 50000Hz with 32 MEMs are values taken as reference):

		* transfer buffers are saved into dataset of ``_h5_dataset_duration`` duration
		* datasets are stored into h5 files of '_h5_file_duration' duration

		These h5 parameters are MegaMicro parameters that have default values (1 second datasets, 15 minutes files,
		see ``core_base.DEFAULT_H5_SEQUENCE_DURATION`` and ``core_base.DEFAULT_H5_FILE_DURATION`` parameters).
		With buffers of 512 samples each, it means that a complete file stores about one minute data (22Go at 50000Hz).
		Files can be fractionned into subfiles to ensure safe network transfer. 
		Internal organization is performed so as to rebuild bigger file from those subfiles.
		H5 files are stored in the H5 root directory which default value is the current working directory
		"""

		"""
		Create buffer and init first H5 file 
		"""
		log.info( ' .H5 init recording process...' )
		try:
			self._h5_dataset_number = int( self._h5_file_duration // self._h5_dataset_duration )
			self._h5_dataset_length = int( self._h5_dataset_duration * self._sampling_frequency )
			self._h5_buffer = np.zeros( shape=( self._channels_number -int( self._counter and self._counter_skip ), self._h5_dataset_length), dtype=np.int32 )
			self._h5_buffer_index = 0
			self.h5_init_file()
		except Exception as e:
			log.fatal( f"H5 init process failed: {e}" )
			raise


	def h5_init_file( self ):

		date = datetime.now()
		timestamp0 = date.timestamp()
		date0str = datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')
		abs_path = os.path.abspath( self._h5_rootdir )
		filename = os.path.join( abs_path, 'mu5h-' + f"{date.year}{date.month:02}{date.day:02}-{date.hour:02}{date.minute:02}{date.second:02}" + '.h5' )
		self._h5_current_file = h5py.File( filename, "w" )
		
		self._h5_current_group = self._h5_current_file.create_group( 'muh5' )
		self._h5_current_group.attrs['date'] = date0str
		self._h5_current_group.attrs['timestamp'] = timestamp0
		self._h5_current_group.attrs['dataset_number'] = 0
		self._h5_current_group.attrs['dataset_duration'] = self._h5_dataset_duration
		self._h5_current_group.attrs['dataset_length'] = self._h5_dataset_length
		self._h5_current_group.attrs['channels_number'] = self._channels_number -int( self._counter and self._counter_skip )
		self._h5_current_group.attrs['sampling_frequency'] = self._sampling_frequency
		self._h5_current_group.attrs['duration'] = 0
		self._h5_current_group.attrs['datatype'] = self._datatype
		self._h5_current_group.attrs['mems'] = np.array( self._mems )
		self._h5_current_group.attrs['mems_number'] = self._mems_number
		self._h5_current_group.attrs['analogs'] = np.array( self._analogs )
		self._h5_current_group.attrs['analogs_number'] = self._analogs_number
		self._h5_current_group.attrs['counter'] = self._counter
		self._h5_current_group.attrs['counter_skip'] = self._counter_skip
		self._h5_current_group.attrs['comment'] = ''
		if self._h5_compressing:
			self._h5_current_group.attrs['compression'] = self._h5_compression_algo
		else:
			self._h5_current_group.attrs['compression'] = False

		self._h5_dataset_index = 0
		log.info( f" .H5 create new file [{filename}]" )

	def h5_write_mems( self, signal, timestamp ):
		"""
		Write transfer buffer in local cache and tranfer local to H5 file 
		! Beware that this function is not thread safe !
		! it should be re-writen or writen outside the acquisition thread ! 
		"""

		if self._h5_buffer_index + self._buffer_length < self._h5_dataset_length:
			"""
			Buffer is not yet completed -> transfer whole signal in buffer
			"""
			if self._h5_buffer_index == 0:
				self._h5_timestamp = timestamp
			self._h5_buffer[:,self._h5_buffer_index:self._h5_buffer_index+self._buffer_length] = signal
			self._h5_buffer_index += self._buffer_length
			
		else:
			"""
			Not enough remainning place in buffer -> transfer first part of signal and save
			"""
			transf_samples_number = self._h5_dataset_length - self._h5_buffer_index
			self._h5_buffer[:, self._h5_buffer_index:self._h5_buffer_index+self._h5_dataset_length] = signal[:,:transf_samples_number]

			"""
			Save dataset. Create new file if dataset max number is reached
			"""
			if self._h5_dataset_index >= self._h5_dataset_number:
				self.h5_init_file()

			seq_group = self._h5_current_group.create_group( str( self._h5_dataset_index ) )
			seq_group.attrs['ts'] = self._h5_timestamp
			if self._h5_compressing:
				if self._h5_compression_algo == 'gzip':
					seq_group.create_dataset( 'sig', data=self._h5_buffer, compression=self._h5_compression_algo, compression_opts=self._h5_gzip_level )
				else:
					seq_group.create_dataset( 'sig', data=self._h5_buffer, compression=self._h5_compression_algo )
			else:
				seq_group.create_dataset( 'sig', data=self._h5_buffer )
			self._h5_dataset_index += 1
			self._h5_current_group.attrs['dataset_number'] = self._h5_dataset_index
			self._h5_current_group.attrs['duration'] = self._h5_dataset_index * self._h5_dataset_duration

			""" 
			Transfer remaining part of signal in buffer, reset index and set the new dataset timestamp
			"""
			self._h5_buffer[:, :self._buffer_length-transf_samples_number] = signal[:,transf_samples_number:self._buffer_length]
			self._h5_buffer_index = self._buffer_length-transf_samples_number
			self._h5_timestamp = timestamp + transf_samples_number / self._sampling_frequency
			

	def h5_close( self ):
		"""
		Nothing to do but closing H5 file
		"""
		self._h5_current_file.close()
