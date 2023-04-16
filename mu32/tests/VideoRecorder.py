# -*- coding: utf-8 -*-
# VideoRecorder.py
#
# Sous Linux/Ubuntu:
# sudo apt install libportaudio2
# sudo apt install libasound-dev
# sudo apt install portaudio19-dev
# sudo apt install libportaudiocpp0
# sudo apt install python3-pyaudio
#
# pip install opencv-python numpy pyaudio
#
# apt install pulseaudio pulseaudio-utils
# start alsa audio daemon: 
# 	pulseaudio -D
# stop: 
# 	pulseaudio -k
#
# Sous MAC
# brew install portaudio
# pip install pyaudio

# source: https://github.com/ohidurbappy/ScriptKiddy/blob/main/python/opencv-audio-video-recording.py

from __future__ import print_function, division
import numpy as np
import cv2
import threading
import time
import os

DEFAULT_CV_MONITORING				= False									# Whether video monitoring is On or Off
#DEFAULT_CV_CODEC					= 'mp4v'								# Video codec (OS/platform dependant)
DEFAULT_CV_CODEC					= 'MJPG'								# Video codec (OS/platform dependant)
DEFAULT_CV_DEVICE					= 0										# Default camera device (0, 1, 2,... depending on connected devices)
DEFAULT_CV_DIRECTORY				= './'									# The default directory where video files are saved
DEFAULT_CV_COLOR_MODE				= cv2.COLOR_BGR2GRAY						# Default set to grey frames
DEFAULT_CV_SAMPLING_FREQUENCY		= 20.0									# Frame number per seconds
DEFAULT_CV_SHOW						= False									# Whether frames are showed or not 
DEFAULT_CV_WIDTH					= 640									# Frame size (width)
DEFAULT_CV_HEIGHT					= 480									# Frame size (height)
DEFAULT_CV_FILE_DURATION			= 15*60									# Time duration of a complete Video file in seconds

class VideoRecorder():  
    "Video class based on openCV"
    def __init__(self, name="temp_video.avi", fourcc=DEFAULT_CV_CODEC, sizex=DEFAULT_CV_WIDTH, sizey=DEFAULT_CV_HEIGHT, camindex=DEFAULT_CV_DEVICE, fps=DEFAULT_CV_SAMPLING_FREQUENCY):
        print( "Open videoCam on device " + str( camindex )  )
        self.open = True
        self.device_index = camindex
        self.fps = fps                  # fps should be the minimum constant rate at which the camera can
        self.fourcc = fourcc            # capture images (with no decrease in speed over time; testing is required)
        self.frameSize = (sizex, sizey) # video formats and sizes also depend and vary according to the camera used
        self.video_filename = name
        self.video_cap = cv2.VideoCapture(self.device_index)
        if not self.video_cap.isOpened():
            print( f"Video camera initialization failed" )
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 1
        self.start_time = time.time()

    def record(self):
        print( "Video starts being recorded" )
        # counter = 1
        timer_start = time.time()
        timer_current = 0
        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                # print(str(counter) + " " + str(self.frame_counts) + " frames written " + str(timer_current))
                self.frame_counts += 1
                # counter += 1
                # timer_current = time.time() - timer_start
                time.sleep(1/self.fps)
                # gray = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)
                # cv2.imshow('video_frame', gray)
                # cv2.waitKey(1)
            else:
                break

    def stop(self):
        print( "Finishes the video recording therefore the thread too" )
        if self.open:
            self.open=False
            self.video_out.release()
            self.video_cap.release()
            cv2.destroyAllWindows()

    def start(self):
        print( "Launches the video recording function using a thread" )
        video_thread = threading.Thread(target=self.record)
        video_thread.start()


def start_video_recording(filename="test"):
    global video_thread
    video_thread = VideoRecorder()
    video_thread.start()
    return filename


def stop_video_recording(filename="test"):

    video_thread.stop() 

    # Makes sure the threads have finished
    while threading.active_count() > 1:
        time.sleep(1)

    # Merging audio and video signal
    #if abs(recorded_fps - 6) >= 0.01:    # If the fps rate was higher/lower than expected, re-encode it to the expected
    #    print("Re-encoding")
    #    cmd = "ffmpeg -r " + str(recorded_fps) + " -i temp_video.avi -pix_fmt yuv420p -r 6 temp_video2.avi"
    #    subprocess.call(cmd, shell=True)
    #    print("Muxing")
    #    cmd = "ffmpeg -y -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video2.avi -pix_fmt yuv420p " + filename + ".avi"
    #    subprocess.call(cmd, shell=True)
    #else:
    #    print("Normal recording\nMuxing")
    #    cmd = "ffmpeg -y -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video.avi -pix_fmt yuv420p " + filename + ".avi"
    #    subprocess.call(cmd, shell=True)
    #    print("..")

def file_manager(filename="test"):
    "Required and wanted processing of final files"
    local_path = os.getcwd()
    if os.path.exists(str(local_path) + "/temp_audio.wav"):
        os.remove(str(local_path) + "/temp_audio.wav")
    if os.path.exists(str(local_path) + "/temp_video.avi"):
        os.remove(str(local_path) + "/temp_video.avi")
    if os.path.exists(str(local_path) + "/temp_video2.avi"):
        os.remove(str(local_path) + "/temp_video2.avi")
    # if os.path.exists(str(local_path) + "/" + filename + ".avi"):
    #     os.remove(str(local_path) + "/" + filename + ".avi")

if __name__ == '__main__':
    start_video_recording()
    time.sleep(5)
    stop_video_recording()
    #file_manager()
