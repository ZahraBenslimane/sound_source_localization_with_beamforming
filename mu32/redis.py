# mu32.redis.py Redis logging messages processing for MegaMicro Mu32 libraries
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
"""

from calendar import c
import logging
import string
from typing import Any
import redis

class RedisHandler( logging.Handler ):

	__streamkey: string
	__host: string
	__port: int
	__device: string
	__ready: bool = False
	__redis = None

	def __init__( self, host:string='localhost', port:int=6379, streamkey: str='log', password:string='', username='default', device:string='Unknown', **kwargs ):
		super().__init__( **kwargs )
		self.__streamkey = streamkey
		self.__host = host
		self.__port = port
		self.__device = device
		self.__redis = redis.Redis(host=self.__host, port=self.__port, decode_responses=True, password=password, username=username )
		if self.__redis.ping() == True:
			self.__ready = True
			self.__redis.xadd( self.__streamkey,  {'device': self.__device, 'message': 'Connected to Redis server'} )

	def emit( self, record: logging.LogRecord) :
		if self.__ready:
			try:
				self.__redis.xadd( self.__streamkey,  {
					'datetime': record.asctime,
					'device': self.__device, 
					'type': record.levelname,
					'message': record.getMessage()
				} )
			except Exception as e :
				"""
				Do nothing since it may due to a refused connection from the Redis server
				"""
				pass
