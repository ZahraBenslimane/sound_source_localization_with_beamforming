# mu32.beamformer.py python beamforming program for MegaMicro Mu32 transceiver 
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
import matplotlib.pyplot as plt

from .log import mu32log as log
from .exception import Mu32Exception

DEFAULT_SAMPLING_FREQUENCY = 50000
DEFAULT_BFWIN_DURATION = 0.1
SOUND_SPEED = 340.29


def das_doa( beamformer, signals, sf=DEFAULT_SAMPLING_FREQUENCY, bfwin_duration=DEFAULT_BFWIN_DURATION ):
    """
    process beamforming on input signal

    Parameters
    ----------
    beamformer: the beamformer parameters by using the bm_beamformer() function
    signals: numpy.array() the signals to beamform comming from microphones 

    Return
    ------
    beamformed signals and beams number
    """

    n_bfwin_samples = int( sf*bfwin_duration )
    ans, n_beams, n_mics = np.shape( beamformer )

    if np.size( signals, 0 ) != n_mics:
        raise Mu32Exception( f"Cannot process beamforming: signals dimensions are not compatible with beamformer parameters (microphone's number do not corresponds: {n_mics}<->{np.size( signals, 0 )})" )
    
    n_samples = np.size( signals, 1 )
    if n_samples < n_bfwin_samples:
        raise Mu32Exception( f"Cannot process beamforming: signals are shorter than window processing size ({n_samples}<{n_bfwin_samples})" )

    n_win = int( n_samples//n_bfwin_samples )

    BF = []
    signals = signals.T
    for i in range( n_win ):
        Spec = np.fft.rfft( signals[i*n_bfwin_samples + np.arange( n_bfwin_samples )], axis=0 )
        SpecG = Spec[:, None, :]*beamformer
        BFSpec = np.sum( SpecG, -1 )/n_mics
        BFSig = np.fft.irfft( BFSpec, axis=0 )
        BF.append( np.mean( np.abs( BFSig )**2,0 ) )

    BF = np.array( BF ).T

    return BF, np.size( BF, 0)


def das_former( antenna, beams_number, sf=DEFAULT_SAMPLING_FREQUENCY, bfwin_duration=DEFAULT_BFWIN_DURATION ):
    """
    Get channels parameters for beamforming. Note that only 1D antenna are solved so far
    
    Parameters
    ----------
    antenna: list of antenna microphones : array of microphone's coordinates (1D, 2D or 3D) 
    beams_number: number of channels to design
    sf: sampling fequency (default is 50000 Hz)
    bfwin_duration: processing window duration in seconds (default is 0,1 (100ms))

    Return
    ------
    G: Preformed channels 
    """

    antenna = antenna_linear_2D( antenna )
    n_mics = np.size( antenna, 1)
    antenna = antenna[0]

    # set microphone's positions relative to the antenna center
    xm = antenna
    xm = xm - ( np.amax(xm) + np.amin(xm) )/2

    # channels organization
    dth = int( 180//beams_number)                       # angle value of a beam in degrees 
    thd = np.array([np.arange(-90,90,dth)]).T           # angular positions of beams in degrees
    thr = thd*np.pi/180                                 # angular positions of beams in radians
    n_th = len(thd)                                     # number of angualr positions (should be equal to the beam's number)
    thmin = -np.pi/2
    thmax = np.pi/2
    th = np.linspace(thmin, thmax, n_th)                # regular sampling of angular positions between -pi/2 and +pi/2

    # Compute preformed channels
    deltam = np.sin( thr )*xm                           # distances distribution of beams on every microphones relative to the DOA and antenna center 
    dtm = deltam/SOUND_SPEED                            # delays distribution
    dim = ( np.round( dtm*sf ) ).astype( 'int32' )      # samples distribution
    dim -= np.min( dim )                                # same relative to the DOA 

    n_bfwin_samples = int( sf*bfwin_duration )
    t = np.arange( n_bfwin_samples )/sf                 # time axis in seconds
    f = np.fft.rfftfreq( n_bfwin_samples, 1/sf )        # frequency axis in Hz
    G = np.outer( f, dtm ).reshape( f.shape[0], dtm.shape[0], dtm.shape[1] )
    G = np.exp( 1j*2*np.pi*G )                          # preformed channels

    # print results
    log.info( '-'*40 )
    log.info( "beamformer parameters:" )
    log.info( f" .set {beams_number} beams every {dth} degrees" )
    log.info( f" .processing window duration: {bfwin_duration} s" )
    log.info( f" .processing window samples: {n_bfwin_samples}" )
    log.info( f" .generate {np.size(f)} X {beams_number} X {n_mics} beamformer" )
    log.info( '-'*40 )

    return G


def room_cues( antenna, locations, sf=DEFAULT_SAMPLING_FREQUENCY, room_size=None ):
    """
    Compute some limits on cues inside room relatively to the antenna dimension
    """

    center, n_mics, angle, inter_space = antenna
    microphones = antenna_linear_2D( antenna )

    locations = np.array(locations).T
    n_locations = np.size( locations, 1 )

    max_diff_samples = 0
    diff_min_delay = []
    diff_min_samples = []
    max_dist = 0
    min_dist = 0
    for src in range( n_locations ):
        dists = np.sqrt( np.sum( ( np.outer( locations[:,src], np.ones( n_mics ) ) - microphones )**2, 0 ) )
        min_dists = np.amin( dists )
        max_dists = np.amax( dists )
        if src==0:
            min_dist = max_dist = min_dists
        else:
            if min_dists < min_dist:
                min_dist = min_dists
            if max_dists > max_dist:
                max_dist = max_dists
        diff_min_dists = np.abs( dists - np.outer( min_dists, np.ones( n_mics ) ) )[0]
        diff_min_delay.append( diff_min_dists/SOUND_SPEED )
        dms = np.array( (diff_min_dists*sf)//SOUND_SPEED, 'int')
        diff_min_samples.append( dms )
        if np.amax( dms ) > max_diff_samples:
            max_diff_samples = np.amax( dms )
        
    diff_min_delay = np.array( diff_min_delay )
    diff_min_samples = np.array( diff_min_samples )

    #print( f" .Arrival time differences between microphones (ms): \n {np.array( diff_min_delay*1000000, 'int')/1000}")
    print( f" .Arrival differences in samples between microphones: \n {diff_min_samples}")
    print( f" .Maximum delay in samples number is: {max_diff_samples} samples")
    print( f" .Signals can be fully localized for frequencies less than {int(sf//max_diff_samples)} Hz (due to microphones inter-distances)")
    print( f" .Map phases is coherent for frequencies less than {int(SOUND_SPEED/(max_dist - min_dist))} Hz (due to antenna dimensions" ) 



def antenna_linear_2D( antenna ):
    """
    Get (x, y, z) coordinates of antenna microphones

    Parameters
    ----------
    antenna: list of antenna characteristics: [[x,y,z], mics number, angle with x-axis, distance between mics]
    """

    center, n_mics, angle, inter_space = antenna
    dim = len( center )

    if dim == 2 or ( dim==3 and ( not isinstance(angle, list) ) or ( isinstance(angle, list) and len(angle)==1 ) ):
        """
        accept 2D antenna or 3D antenna only defined in the 2D space
        """
        if isinstance( angle, list ):
            angle = angle[0]

        if dim == 2:
            central_pos_x, central_pos_y = center
        else:
            central_pos_x, central_pos_y, central_pos_z= center

        len_array = (n_mics-1) * inter_space
        array = np.array( range( n_mics ) ) * inter_space - len_array/2
        array = ( np.append( [array], [array], 0 ).T * np.array( [np.cos(angle), np.sin(angle)] ) ).T

        if dim == 2:
            array = array + np.outer( np.array([central_pos_x, central_pos_y]), np.ones( n_mics ))
        else:
            # for 3D antenna, add as third dimension the z-coordinate of the antena center
            array = np.append( array, np.full( ( 1, n_mics ), 0 ), 0 )
            array = array + np.outer( np.array([central_pos_x, central_pos_y, central_pos_z]), np.ones( n_mics ))
    
    else:
        raise Mu32Exception( f"Failed to extract microphones 2D coordinates: antenna dimensions are not correct ({len( center )})")

    return array