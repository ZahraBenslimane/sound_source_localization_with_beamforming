
# -*- coding: utf-8 -*-
# AudioVideoRecorder.py
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


#from __future__ import print_function, division
import argparse
import numpy as np
import cv2
import pyaudio
import wave
import threading
import time
import subprocess
import os

from mu32.core import main

welcome_msg = '-'*20 + '\n' + 'Mu32 run program\n \
Copyright (C) 2022  distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


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

#DEFAULT_AUDIO_SAMPLING_FREQUENCY    = 44100
DEFAULT_AUDIO_SAMPLING_FREQUENCY    = 16000
DEFAULT_AUDIO_FRAME_PER_BUFFER      = 8192
DEFAULT_AUDIO_CHANNELS              = 2
DEFAULT_INPUT_DEVICE                = 0
DEFAULT_DURATION                    = 5



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument( "-i", "--indev", help=f"Audio input device {DEFAULT_INPUT_DEVICE}" )
    parser.add_argument( "-f", "--sf", help=f"Sampling frequency. Default is {DEFAULT_AUDIO_SAMPLING_FREQUENCY}" )
    parser.add_argument( "-d", "--duration", help=f"Duration Default is {DEFAULT_DURATION}s" )
    parser.add_argument( "-p", "--fpb", help=f"Frame per buffer  {DEFAULT_AUDIO_FRAME_PER_BUFFER}s" )

    args = parser.parse_args()
    indev = DEFAULT_INPUT_DEVICE
    sf = DEFAULT_AUDIO_SAMPLING_FREQUENCY
    duration = DEFAULT_DURATION
    fpb = DEFAULT_AUDIO_FRAME_PER_BUFFER
    if args.indev:
        indev = int( args.indev )
    if args.sf:
        sf = int( args.sf )
    if args.duration:
        duration = int( args.duration )
    if args.fpb:
        fpb = int( args.fpb )

    print( welcome_msg )

    start_AVrecording( indev=indev, sf=sf, fpb=fpb )
    time.sleep( duration )
    stop_AVrecording()
    #file_manager()




class VideoRecorder():  
    "Video class based on openCV"
    def __init__(self, name="temp_video.avi", fourcc=DEFAULT_CV_CODEC, sizex=DEFAULT_CV_WIDTH, sizey=DEFAULT_CV_HEIGHT, camindex=DEFAULT_CV_DEVICE, fps=DEFAULT_CV_SAMPLING_FREQUENCY):
        print( "Open videoCam" )
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



class AudioRecorder():
    "Audio class based on pyAudio and Wave"
    def __init__(self, filename="temp_audio.wav", rate=DEFAULT_AUDIO_SAMPLING_FREQUENCY, fpb=DEFAULT_AUDIO_FRAME_PER_BUFFER, channels=DEFAULT_AUDIO_CHANNELS, input_device_index=DEFAULT_INPUT_DEVICE):
        print( "Opening audio device..." )
        self.open = True
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_filename = filename
        try:
            self.audio = pyaudio.PyAudio()
            print( "Opening audio stream on inpu device ", input_device_index )
            print( "Sampling frequency: ", self.rate  )
            print( "Frames perbuffer: ", self.frames_per_buffer )
            print( "Channels: ", self.channels )
            print( "Output audio filename: ", self.audio_filename )
            self.stream = self.audio.open(format=self.format,
                                        channels=self.channels,
                                        rate=self.rate,
                                        input=True,
                                        frames_per_buffer = self.frames_per_buffer,
                                        input_device_index = input_device_index
                                        )
            self.audio_frames = []
            print( "ok" )
        except Exception as e:
            print( "Failed to open pyaudio stream: ", e )

    def record(self):
        print( "Audio starts stream..." )
        try:
            self.stream.start_stream()
        except Exception as e:
            print( "Failed" )
        else:
            print( "Success" )

        print( "Audio recording..." )
        bytes = 0
        while self.open:
            try:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow = False)
            except Exception as e:
                print( "Exception  occured: ", e )
                self.open = False
                break
            else:
                self.audio_frames.append( data )

            if not self.open:
                break

    def stop(self):
        print( "Finishes the audio recording therefore the thread too" )
        if self.open:
            self.open = False
            print( "Stop pyaudio stream..." )
            self.stream.stop_stream()
            print( "Close pyaudio stream..." )
            self.stream.close()
            print( "Terminate audio..." )
            try:
                self.audio.terminate()
            except Exception as e:
                print("failed")
            else:
                print( "Success")

            print( "open output audio file and write data" )
            waveFile = wave.open(self.audio_filename, 'wb')
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(self.audio.get_sample_size(self.format))
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b''.join(self.audio_frames))
            waveFile.close()
            print( 'done' )

    def start(self):
        print( "Launches the audio recording function using a thread" )
        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()


def start_AVrecording( indev=DEFAULT_INPUT_DEVICE, sf=DEFAULT_AUDIO_SAMPLING_FREQUENCY, fpb=DEFAULT_AUDIO_FRAME_PER_BUFFER, filename="test"):
    global video_thread
    global audio_thread
    video_thread = VideoRecorder()
    audio_thread = AudioRecorder( input_device_index=indev, rate=sf, fpb=fpb )
    audio_thread.start()
    video_thread.start()
    return filename

def start_video_recording(filename="test"):
    global video_thread
    video_thread = VideoRecorder()
    video_thread.start()
    return filename

def start_audio_recording(filename="test"):
    global audio_thread
    audio_thread = AudioRecorder()
    audio_thread.start()
    return filename

def stop_AVrecording(filename="test"):
    audio_thread.stop() 
    frame_counts = video_thread.frame_counts
    elapsed_time = time.time() - video_thread.start_time
    recorded_fps = frame_counts / elapsed_time
    print("total frames " + str(frame_counts))
    print("elapsed time " + str(elapsed_time))
    print("recorded fps " + str(recorded_fps))
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
    main()

