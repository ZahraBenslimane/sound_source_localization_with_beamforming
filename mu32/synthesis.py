# mu32.synthesis.py python synthesis program for MegaMicro Mu32 
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

import numpy as np
import math
from scipy.io import wavfile

from .logging import mu32log as log
from .exception import Mu32Exception
from .beamformer import antenna_linear_2D 

DEFAULT_SAMPLING_FREQUENCY = 50000
DEFAULT_DURATION = 1
SOUND_SPEED = 340.29


def gen_wav( spec: list, sf=DEFAULT_SAMPLING_FREQUENCY, duration=DEFAULT_DURATION,  outputfile: str=None ):
    """
    Generate an additive synthesis sound and save it in outputfile, if given
    
    Parameters
    ----------
    spec: list with sound specification of the forme [ [f1, f2, ...], [m1, m2, ...], [p1, p2, ...] ]

    Return 
    ------
    The resulting sound 

    Example
    mu32ia.core.synthesizer( [ [440], [1], [0] ], 16000, 1, '../datasets/sources/sound.wav' )
    mu32ia.core.synthesizer( [ [440, 1000, 2000], [1, 0.5, 0.8], [0, 0.5, 2.14] ], 16000, 1, '../datasets/sources/sound2.wav' )
    """

    sp = 1/sf
    n_samples: int = int( duration*sf )
    frequencies = spec[0]
    magnitudes = spec[1]
    phases = spec[2]

    signal = np.zeros( n_samples )
    for q in range( n_samples ):
        signal[q] = 0
        for j in range( len( frequencies) ):
            signal[q] = signal[q] + magnitudes[j] * math.sin( 2 * math.pi * frequencies[j] * q * sp + phases[j] )

    if outputfile is not None:
        wavfile.write( outputfile, sf, signal )

    return signal


def freefield_record( source, antenna: np.array, locations: np.array, sf=DEFAULT_SAMPLING_FREQUENCY, outputfile: str=None ):
    """
    Build a data set of antenna signals comming from a sound recorded in a free field environment

    Parameters
    ----------
    source: the wav file name of the original wav source (mono source) or numpy array data
    outputfile: name of the file where to save data. File extension is not mandatory (will be .npy)
    antenna: list of antenna characteristics: [[x,y,z], mics number, angle with x-axis, distance between mics]. Default is [[2, 1.5, 1.2], 2, 0, 0.1],
    locations: numpy array defining the sources positions in meters

    Return
    ------
    Recorded signals in a list of arrays (one per source)
    """

    # if wav filename is given, read data
    if type( source ) is str:
        sf, source = wavfile.read( source )

    # get 1D positions of microphones on the linear antenna
    center, n_mics, angle, inter_space = antenna
    microphones = antenna_linear_2D( antenna )[0]

    signals = []
    for location in locations:
        # compute time propagation between source and microphones and convert into samples number 
        delay = np.sqrt( np.sum( (np.outer(location, np.ones(n_mics)) - microphones)**2,0) ) / SOUND_SPEED
        n_samples = np.rint( delay*sf ).astype(int)
        total_samples = np.size( source ) + np.amax( n_samples )
        signal = []
        for mic in range( n_mics ):
            signal.append( np.append( np.zeros( n_samples[mic] ), np.append( source, np.zeros( total_samples - np.size( source ) - n_samples[mic]) ) ) )
        signals.append( np.array( signal) ) 

        print( f"microphones delays are: {n_samples} samples" )

    if outputfile is not None:
        np.save( outputfile, signals )

    return signals