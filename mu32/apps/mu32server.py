# mu32server.py python server MegaMicro Mu32 receiver 
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
Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install h5py
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 save program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20

import asyncio
import argparse
import numpy as np
from mu32.core_server import MegaMicroServer, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MEGAMICRO_SYSTEM, DEFAULT_MAX_CONNECTIONS, DEFAULT_CONFIG_PATH
from mu32.core import logging, log
from mu32.exception import MuException


log.setLevel( logging.INFO )


async def main():
    """
    Default simple server
    """
    global log

    parser = argparse.ArgumentParser()
    parser.add_argument( "-n", "--host", help=f"set the server listening host. Default is {DEFAULT_HOST}" )
    parser.add_argument( "-p", "--port", help=f"set the server listening port. Default is {DEFAULT_PORT}" )
    parser.add_argument( "-s", "--system", help=f"set the MegaMicro receiver type system (Mu32, Mu256, Mu1024, MuH5). Default is {DEFAULT_MEGAMICRO_SYSTEM}" )
    parser.add_argument( "-c", "--maxconnect", help=f"set the server maximum simultaneous connections. Default is {DEFAULT_MAX_CONNECTIONS}" )
    parser.add_argument( "-f", "--file", help=f"set the server in H5 file reader mode on specified file or directory. Default is None" )
    parser.add_argument( "-d", "--debug", help=f"set the debug mode: DEBUG, INFO, WARNING, ERROR, CRITICAL" )
    parser.add_argument( "-i", "--conf", help=f"set the configuration file path. Default is {DEFAULT_CONFIG_PATH}" )

    args = parser.parse_args()
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    megamicro_system = DEFAULT_MEGAMICRO_SYSTEM
    maxconnect = DEFAULT_MAX_CONNECTIONS
    filename = None
    config_path = DEFAULT_CONFIG_PATH
    
    if args.host:
        host = args.host
    if args.port:
        port = args.port
    if args.system:
        megamicro_system = args.system
    if args.maxconnect:
        maxconnect = args.maxconnect
    if args.file:
        filename = args.file
    if args.debug:
        if args.debug=='DEBUG':
            log.setLevel( logging.DEBUG )
        elif args.debug=='INFO':
            log.setLevel( logging.INFO )
        elif args.debug=='WARNING':
            log.setLevel( logging.WARNING )
        elif args.debug=='ERROR':
            log.setLevel( logging.ERROR )
        elif args.debug=='CRITICAL':
            log.setLevel( logging.CRITICAL )
        else:
            print( 'Unknown debug level' )
            exit()
    if args.conf:
        config_path = args.conf    

    print( welcome_msg )

    try:
        server = MegaMicroServer( maxconnect=maxconnect, filename=filename, config_path=config_path )
        result = await server.run(
            megamicro_system=megamicro_system,
            host=host,
            port=port
        )
    except MuException as e:
        log.error( f"Server abort due to internal error: {e}" )
    except Exception as e:
        log.error( f"Server abort due to unknown error: {e}" )


def async_main():
    asyncio.run( main() )

if __name__ == "__main__":
    asyncio.run( main() )
