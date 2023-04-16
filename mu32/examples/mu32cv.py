# mu32cv.py python program example for MegaMicro Mu32 receiver 
#
# Copyright (c) 2022 DistalSense
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
Run the Mu32 system during one second and open a video window at the same time 

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
    > pip install opencv-python

See tutorail: https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
For video codec on Mac, see https://gist.github.com/takuma7/44f9ecb028ff00e2132e
For video streaming: https://www.linkedin.com/pulse/creating-live-video-streaming-app-using-python-ranjit-panda/
For audio and videao: https://github.com/JagerCox/tcp-streaming-multicast-client.server-audio.video
For audio web client/server, see https://pyshine.com/How-to-send-audio-from-PyAudio-over-socket/
Audio streaming with flask to audio HTML5: https://stackoverflow.com/questions/51079338/audio-livestreaming-with-python-flask
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 run program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import argparse
from warnings import catch_warnings
import numpy as np
import cv2 as cv
from mu32.core import Mu32, logging, log
from mu32.exception import MuException

MEMS = (0, 1, 2, 3, 4, 5, 6, 7)
DURATION = 5
VIDEO_DEVICE = 0
VIDEO_FILE_DURATION = 5

log.setLevel( logging.INFO )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-t", "--duration", help="set the time acquisition in seconds (default is: {DURATION}s)")
    parser.add_argument( "-d", "--device", help="set the video input device (default is: {VIDEO_DEVICE})")
    parser.add_argument( "-v", "--file_duration", help="set the video file(s) max duration (default is: {VIDEO_FILE_DURATION}s)")

    args = parser.parse_args()
    device = VIDEO_DEVICE
    duration = DURATION
    file_duration = VIDEO_FILE_DURATION
    if args.device:
        device = int( args.device )
        print( f"input video device set to {device}" )
    if args.duration:
        duration = int( args.duration )
        print( f"recording duration set to {duration}s" )
    if args.file_duration:
        file_duration = int( args.file_duration )
        print( f"video file(s) max duration set to {file_duration}s" )

    try:
        mu32 = Mu32()
        mu32.run(
            mems=list( range( 32 ) ), # 32 activated mems
            duration=duration,        # one second duration
            sampling_frequency=10000, # 10kHz
            h5_recording=True,        # H5 recording
            cv_monitoring=True,       # do video monitoring
            cv_device=device,         # device where to found camera 
            cv_file_duration=file_duration
        )

        mu32.wait()

    except MuException as e:
        print( 'error: ', e )


















if __name__ == "__main__":
	main()