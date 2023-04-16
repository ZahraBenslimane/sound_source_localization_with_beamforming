# mu32.core_types.py python program interface for MegaMicro transceiver 
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
MegaMicro main types used

Mu32 documentation is available on https://distalsense.io
See documentation on usb device programming with libusb on https://pypi.org/project/libusb1/1.3.0/#documentation
Examples are available on https://github.com/vpelletier/python-libusb1
"""

class H5Parameters:
    def __init__( self, date, timestamp, sampling_frequency, dataset_number, dataset_duration, dataset_length, channels_number, duration, datatype, mems, mems_number, counter, counter_skip, comment, compression):

        self._date = date
        self._timestamp = timestamp
        self._dataset_number = dataset_number
        self._dataset_duration = dataset_duration
        self._dataset_length = dataset_length
        self._channels_number = channels_number
        self._sampling_frequency = sampling_frequency
        self._duration = duration
        self._datatype: datatype
        self._mems = mems
        self._mems_number = mems_number
        self._counter = counter
        self._counter_skip = counter_skip
        self._compression = compression
        self._comment = comment

