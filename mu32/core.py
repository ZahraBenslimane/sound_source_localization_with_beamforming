# mu32.core.py python program interface for MegaMicro Mu32 transceiver 
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
	> pip install libusb1
"""


__VERSION__ = 1.0

#from sys import path 
#path.append('./mu32')

import numpy as np
from ctypes import addressof, byref, sizeof, create_string_buffer, CFUNCTYPE
from math import ceil as ceil

from mu32.log import logging, mulog as log, mu32log						# mu32log for backward compatibility
from mu32.exception import Mu32Exception, MuException
from mu32.core_base import MegaMicro, MU32_SYSTEM_NAME, MU32USB2_SYSTEM_NAME, MU256_SYSTEM_NAME, MU1024_SYSTEM_NAME
from mu32.core_ws import MegaMicroWS


"""
Mu32 receiver properties
"""
MU32_BEAMS_NUMBER				= 4										# Max number of pluggable beams 

"""
Mu32 USB-2 properties
"""
MU32_USB2_VENDOR_ID				= 0xFE27
MU32_USB2_VENDOR_PRODUCT		= 0xAC00
MU32_USB2_BUS_ADDRESS			= 0x81									# seen 0x82 in some python libraries but the doc says 0x81...

"""
Mu32 USB-3 properties
"""
MU32_USB3_VENDOR_ID				= 0xFE27
MU32_USB3_VENDOR_PRODUCT		= 0xAC03
MU32_USB3_BUS_ADDRESS			= 0x81

"""
Mu256 properties
"""
MU256_BEAMS_NUMBER				= 32									# Max number of pluggable beams
MU256_USB3_VENDOR_ID			= 0xFE27
MU256_USB3_VENDOR_PRODUCT		= 0xAC01
MU256_USB3_BUS_ADDRESS			= 0x81

"""
Mu1024 properties
"""
MU1024_BEAMS_NUMBER				= 128									# Max number of pluggable beams 								
MU1024_USB3_VENDOR_ID			= 0xFE27
MU1024_USB3_VENDOR_PRODUCT		= MU256_USB3_VENDOR_PRODUCT				# Not known 
MU1024_USB3_BUS_ADDRESS			= 0x81	



class Mu32( MegaMicro ):
	"""
	MegaMicro 32 channels implementation
	"""
	def __init__( self ):
		self._system = MU32_SYSTEM_NAME
		super().__init__( 
			usb_vendor_id=MU32_USB3_VENDOR_ID, 
			usb_vendor_product=MU32_USB3_VENDOR_PRODUCT,
			usb_bus_address = MU32_USB3_BUS_ADDRESS,
			pluggable_beams_number = MU32_BEAMS_NUMBER
		)

	def __del__( self ):
		super().__del__()


	def ctrlMems( self, handle, request, mems='all' ):
		"""
		Activate or deactivate MEMs
		"""
		super().ctrlMems( handle, request, MU32_BEAMS_NUMBER, mems )



class Mu32usb2( MegaMicro ):
	"""
	Should be refactorized for USB-2 adapting (see the doc)
	"""
	def __init__( self ):
		self._system = MU32USB2_SYSTEM_NAME
		super().__init__( 
			usb_vendor_id=MU32_USB2_VENDOR_ID, 
			usb_vendor_product=MU32_USB2_VENDOR_PRODUCT,
			usb_bus_address = MU32_USB2_BUS_ADDRESS,
			pluggable_beams_number = MU32_BEAMS_NUMBER
		)

	def __del__( self ):
		super().__del__()


	def ctrlMems( self, handle, request, mems='all' ):
		"""
		Activate or deactivate MEMs
		"""
		super().ctrlMems( handle, request, MU32_BEAMS_NUMBER, mems )


class Mu256( MegaMicro ):

	def __init__( self ):
		self._system = MU256_SYSTEM_NAME
		super().__init__( 
			usb_vendor_id=MU256_USB3_VENDOR_ID, 
			usb_vendor_product=MU256_USB3_VENDOR_PRODUCT,
			usb_bus_address = MU256_USB3_BUS_ADDRESS,
			pluggable_beams_number = MU256_BEAMS_NUMBER
		)

	def __del__( self ):
		super().__del__()


	def ctrlMems( self, handle, request, mems='all' ):
		"""
		Activate or deactivate MEMs
		"""
		super().ctrlMems( handle, request, MU256_BEAMS_NUMBER, mems )


class Mu1024( MegaMicro ):

	def __init__( self ):
		self._system = MU1024_SYSTEM_NAME
		super().__init__( 
			usb_vendor_id=MU1024_USB3_VENDOR_ID, 
			usb_vendor_product=MU1024_USB3_VENDOR_PRODUCT,
			usb_bus_address = MU1024_USB3_BUS_ADDRESS,
			pluggable_beams_number = MU1024_BEAMS_NUMBER
		)

	def __del__( self ):
		super().__del__()


	def ctrlMems( self, handle, request, mems='all' ):
		"""
		Activate or deactivate MEMs
		"""
		super().ctrlMems( handle, request, MU1024_BEAMS_NUMBER, mems )


class Mu32ws ( MegaMicroWS ):
	"""
	!TO DO
	some controls about activated mems number or analogic activated channels number should be done here by run() method overloading 
	"""
	pass

class Mu256ws ( MegaMicroWS ):
	"""
	!TO DO
	some controls about activated mems number or analogic activated channels number should be done here by run() method overloading 
	"""
	pass

class Mu1024ws ( MegaMicroWS ):
	"""
	!TO DO
	some controls about activated mems number or analogic activated channels number should be done here by run() method overloading 
	"""
	pass




def main():
	print( 'This is the main function of the module Mu32. Performs autotest' )
	mu32 = Mu32()
	mu32.run( 
		mems=[i for i in range(32)],
		post_callback_fn=mu32.autotest,
	)


def __main__():
	main()


if __name__ == "__main__":
	main()



