


import os
import argparse
from operator import length_hint
import h5py
import datetime
import json
import matplotlib.dates as dates
import numpy as np
from mu32.exception import MuException
from mu32.log import logging, mulog as log, mu32log		# mu32log for backward compatibility


DEFAULT_SAMPLING_FREQUENCY = 50000
DEFAULT_SEQUENCE_DURATION = 1
DEFAULT_DATATYPE = 'int32'
DEFAULT_MEMS = [n for n in range(32)]
DEFAULT_MEMS_NUMBER = len( DEFAULT_MEMS )

DEFAULT_COMPRESSION_ALGO = 'gzip'
DEFAULT_GZIP_LEVEL = 9



"""
Faire des tests de création/lecture de fichiers H5
"""

welcome_msg = '-'*20 + '\n' + 'MegaMicro convert program for archipel data\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


#Sensibilité : -26dBFS pour 104 dB soit 3.17 Pa
FS = 2**23
S = FS*10**(-26/20.) / 3.17
po = 20e-6
Fs = 50000



def printcontent( msg ):
	print( msg ) 

def main():

	"""
	Organization of H5 file is as follows (fs of 50000Hz with 32 MEMs are values taken as reference):
	- H5 file should be viewed as a data generator. As such internal organization has nothing to do with the way those signal have been capted.
	For instance transfer buffer informations are not saved. Only time informations, data type, system informations are kept.
	- Data are fractionned into dataset of one second duration each exactly
	- Minimal group and subgroups are created :
	-- muh5/parameters (for general parameters)
	-- muh5/<dataset_num>/ts (for timestamp of dataset)
	-- muh5/<dataset_num>/sig (for signals)
	-- muh5/<dataset_num>/[fft|doa|...] (for other transformed data)
	"""


	parser = argparse.ArgumentParser()
	parser.add_argument( "-f", "--file", help=f"H5 archipel file to open" )
	parser.add_argument( "-c", "--compress", help=f"compression (ex: gzip)" )
	args = parser.parse_args()
	if args.file:
		filename = args.file
	else:
		log.error( 'argument file is mandatory' )
		exit()

	if args.compress:
		compression = args.compress
	else:
		compression = False

	print( welcome_msg )
	
	sequences = []
	with h5py.File( filename, "r" ) as f:

		SeqNames  = [n for n in f.keys() if n.startswith('Seq')]
		for Name in SeqNames:
			if f[Name].keys():
				Date = f[Name].attrs['Date']  
				Date = datetime.datetime.strptime(Date, '%Y-%m-%d %H:%M:%S.%f')
				Seconde = np.round(dates.date2num(Date)%1*24*3600)
				sequences.append((f, Name, int(Name[3:]), Seconde))
				#print( 'Sequence append -> date: ' + str(Date) + ', secondes: ' + str(Seconde) )

		sequences = sorted(sequences, key=lambda tup: tup[2])
		sequences_number = len(sequences)
		print( 'Collected sequences: ' + str(sequences_number) )
		key0 = sequences[0][1]
		Sec0 = f[key0 + '/Sig']
		Date0str = f[key0].attrs['Date']
		Date0 = datetime.datetime.strptime( Date0str, '%Y-%m-%d %H:%M:%S.%f')
		timestamp0 = Date0.timestamp()
		print( f"Date: {Date0.date()}, time: {Date0.time()}" )
		print( f"Timestamp: {timestamp0}" )

		(seq_samples_number, channels_number) = np.shape( Sec0 )
		print( f"Samples number per sequence: {seq_samples_number}" )
		print( f"Channels number: {channels_number}" )
		if channels_number== 33:
			mems_number = 32
			counter_skip = False
		else:
			mems_number = channels_number
			counter_skip = True

		"""
		Open ouput H5 file with a name of the form muh5-<original_name>.h5
		"""
		pathname, _ = os.path.splitext( filename )
		dt = f"{Date0.year}{Date0.month:02}{Date0.day:02}-{Date0.hour:02}{Date0.minute:02}{Date0.second:02}"
		output_filename = 'muh5-' + dt + '_' + pathname.split('/')[-1] + '.h5'
		print( f"Save to {output_filename}" )

		with h5py.File( output_filename, "w" ) as outf:
			group = outf.create_group( 'muh5' )
			group.attrs['date'] = Date0str
			group.attrs['timestamp'] = timestamp0
			group.attrs['dataset_number'] = sequences_number
			group.attrs['dataset_duration'] = DEFAULT_SEQUENCE_DURATION
			group.attrs['dataset_length'] = seq_samples_number
			group.attrs['channels_number'] = channels_number
			group.attrs['sampling_frequency'] = DEFAULT_SAMPLING_FREQUENCY
			group.attrs['duration'] = sequences_number * DEFAULT_SEQUENCE_DURATION
			group.attrs['datatype'] = DEFAULT_DATATYPE
			group.attrs['mems'] = [n for n in range( mems_number )]
			group.attrs['mems_number'] = mems_number
			group.attrs['counter'] = True
			group.attrs['counter_skip'] = counter_skip
			group.attrs['compression'] = compression
			group.attrs['comment'] = ''

			for seq_index, seq in enumerate( sequences ):
				signal = np.transpose( f[seq[1] + '/Sig'] )
				date = f[seq[1]].attrs['Date']
				ts = datetime.datetime.strptime( date, '%Y-%m-%d %H:%M:%S.%f').timestamp()
				seq_group = group.create_group( str( seq_index ) )
				seq_group.attrs['ts'] = ts

				if compression:
					if compression == 'gzip':
						seq_group.create_dataset( 'sig', data=signal, compression=compression, compression_opts=DEFAULT_GZIP_LEVEL )
					else:
						seq_group.create_dataset( 'sig', data=signal, compression=compression )
				else:
					seq_group.create_dataset( 'sig', data=signal )


if __name__ == "__main__":
    main()




