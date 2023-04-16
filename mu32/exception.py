# mu32ia.exception.py exception class for MegaMicro Mu32 libraries 
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

class MuException( Exception ):
	value = None

	def __init__( self, value=None ):
		Exception.__init__( self )
		if value is not None:
			self.value = value

	def __str__(self):
		return '%s [%s]' % ( 'MuException: ', self.value )



class Mu32Exception( Exception ):
	value = None

	def __init__( self, value=None ):
		Exception.__init__( self )
		if value is not None:
			self.value = value

	def __str__(self):
		return '%s [%s]' % ( 'Mu32Exception: ', self.value )
