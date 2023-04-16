# mu32dash.py python program example for MegaMicro Mu32 transceiver using Dash
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
Run the Mu32 system during one second for getting and ploting signals comming from
activated microphones. Use Dash plotting framework

Documentation is available on https://distalsense.io

Please, note that the following packages should be installed before using this program:
	> pip install libusb1
	> pip install matplotlib
"""

welcome_msg = '-'*20 + '\n' + 'Mu32 plot program\n \
Copyright (C) 2022  Distalsense\n \
This program comes with ABSOLUTELY NO WARRANTY; for details see the source code\'.\n \
This is free software, and you are welcome to redistribute it\n \
under certain conditions; see the source code for details.\n' + '-'*20


#https://stackoverflow.com/questions/63589249/plotly-dash-display-real-time-data-in-smooth-animation
#https://dash.plotly.com/live-updates
#https://plotly.com/python/animations/
#https://pythonprogramming.net/live-graphs-data-visualization-application-dash-python-tutorial/
#https://jackylishi.medium.com/build-a-realtime-dash-app-with-websockets-5d25fa627c7a

# pip install werkzeug==2.0.0 (la version 2.1.0 installée par dash ne fonctionne pas)

# for delay shorter than 100ms, result is not smooth. Laybe because every callback has to create the figure.
# here is an example using 'extendData': https://stackoverflow.com/questions/63589249/plotly-dash-display-real-time-data-in-smooth-animation/63681810#63681810
# Also question is how the callback could be on the client side...: see https://dash.plotly.com/clientside-callbacks


from re import M
from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd


from dash.dependencies import Input, Output

import argparse
import queue
import numpy as np
from mu32.core import Mu32, logging, mu32log


mu32log.setLevel( logging.INFO )

MEMS=(0, 1, 2, 3)
MEMS_NUMBER = len( MEMS )
DURATION = 1
BUFFER_LENGTH = 512


# >>>>>>>>>>>><
# see https://plotly.com/javascript/plotlyjs-function-reference/#plotlyextendtraces.
# see https://javascript-conference.com/blog/real-time-in-angular-a-journey-into-websocket-and-rxjs/



figure = dict(
    data=[{'x': [], 'y': []}],
    layout=dict(
        xaxis=dict(range=[0, BUFFER_LENGTH]), 
        yaxis=dict(range=[-1, 1])
    )
)

app = Dash(__name__, update_title=None)  # remove "Updating..." from title
app.layout = html.Div( [
    dcc.Graph(
        id='graph', 
        figure=figure
    ), 
    dcc.Interval(
        id="interval",
        interval=1*25
    )
])


parser = argparse.ArgumentParser()
parser.parse_args()
print( welcome_msg )

try:
    mu32 = Mu32()
    mu32.run( 
        mems=MEMS,                          # activated mems
        duration=DURATION,
        buffer_length = BUFFER_LENGTH
    )

    #app.run_server(debug=True)
    input( 'Press [Return] key to stop...' )
    mu32.stop()

    #mu32.wait()

except Exception as e:
    print( 'aborting: ', e )



@app.callback(Output('graph', 'extendData'), 
            [Input('interval', 'n_intervals')])
def update_data( n_intervals ):

    global mu32

    """
    get last queued signal and plot it
    """
    try:
        data = mu32.signal_q.get_nowait()
    except queue.Empty:
        return dict(
            x=[],
            y=[]
        ), [0], 0

    t = [i for i in range( BUFFER_LENGTH )]
    data = data[0,:] * mu32.sensibility

    # tuple is (dict of new data, target trace index, number of points to keep)
    return dict(
        x=[t],
        y=[data.tolist()]
    ), [0], BUFFER_LENGTH



if __name__ == '__main__':
    app.run_server(debug=True)




"""
app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

#fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")


app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Signal plotting.
    '''),

    dcc.Graph(
        id='signal-graph'
    ),

    dcc.Interval(
        id='interval-component',
        interval=1*30, # in milliseconds
        n_intervals=0
    )
])

@app.callback(Output('signal-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph( n ):

    t = np.array( range( 1000 ))
    y = np.random.rand( 1000 )
    fig = go.Figure( data=[go.Scatter( x=t, y=y )] )

    return fig

app.run_server(debug=True)
"""