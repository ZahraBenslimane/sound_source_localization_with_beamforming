# -*- coding: utf-8 -*-
# AudioRecorder.py
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
from warnings import catch_warnings
import numpy as np
import cv2
import pyaudio
import wave
import threading
import time
import subprocess
import os


DEFAULT_AUDIO_SAMPLING_FREQUENCY    = 44100
DEFAULT_AUDIO_FRAME_PER_BUFFER      = 1024
DEFAULT_AUDIO_CHANNELS              = 2
DEFAULT_INPUT_DEVICE                = 1

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
        self.audio = pyaudio.PyAudio()
        print( "Opening audio stream..." )
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer = self.frames_per_buffer,
									  input_device_index = input_device_index
									  )
        self.audio_frames = []
        print( "ok" )

    def record(self):
        print( "Audio starts stream..." )
        self.stream.start_stream()
        print( "Audio recording..." )
        while self.open:
            try:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow = False)
            except Exception as e:
                print( "Exception  occured: ", e )
                self.open = False
                break
            else:
                self.audio_frames.append(data)

            if not self.open:
                break

    def stop(self):
        print( "Finishes the audio recording therefore the thread too" )
        if self.open:
            self.open = False
            print( "Stop stream..." )
            self.stream.stop_stream()
            print( "Close stream..." )
            self.stream.close()
            print( "Terminate audio..." )
            self.audio.terminate()
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

def start_audio_recording(filename="test"):
    global audio_thread
    audio_thread = AudioRecorder()
    audio_thread.start()
    return filename

def stop_audio_recording(filename="test"):
    audio_thread.stop() 

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
    start_audio_recording()
    time.sleep(5)
    stop_audio_recording()
    #file_manager()
