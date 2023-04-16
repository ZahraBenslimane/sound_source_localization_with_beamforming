
import numpy as np
import json
import asyncio
import websockets

def main():
    asyncio.run( hello() )


async def hello():
    async with websockets.connect("ws://localhost:8001") as websocket:
        """
        Request connection
        """
        message = json.dumps( {'request': 'connection'} )
        await websocket.send( message )
        response = await websocket.recv()
        print( f"got response: {response}" )

        """
        Request running the mu32
        """
        mems = [i for i in range(32)]
        message = json.dumps( {
            'request': 'run',
            'parameters': {
                'sampling_frequency': 50000,
                'mems': mems,
                'analogs': [],
                'counter': True,
                'counter_skip': True,
                'status': False,
                'duration': 1,
                'buffer_length': 256,
                'buffers_number': 4,
            }
        } )
        await websocket.send( message )
        response = await websocket.recv()
        print( f"got response: {response}" )

        i = 0
        while True:
            data = await websocket.recv()
            input = np.frombuffer( data, dtype=np.int32 )
            if( input[0] == -251658481 ):
                print( 'end of transfer' )
                break
            print( '->', i )
            i += 1

#asyncio.run(hello())


if __name__ == "__main__":
	main()



