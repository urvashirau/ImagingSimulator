#!/usr/bin/env python

"""simmer.py: Create a dash/plotly GUI for an interferometric imaging simulator."""

__author__      = "Urvashi R.V."
__email__ = "rurvashi@nrao.edu"

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
#import dash_daq as daq
#import pandas as pd
import plotly.graph_objs as go

import numpy as np
import copy
import time

from calcsim import CalcSim

tel = CalcSim()
#prevconfig='YConfig'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#### Set up the Layout
app.layout = html.Div([
    html.Div(
        children=[
            html.Div( [ 
                html.H6(children='Array configuration'),
                dcc.Dropdown(
                    id='config-dropdown',
                    options=[
                        {'label': 'Y', 'value': 'YConfig'},
                        {'label': 'Spiral', 'value': 'SpiralConfig'},
                        {'label': 'Circle', 'value': 'CircleConfig'},
                        {'label': 'Random', 'value': 'RandomConfig'},
                        {'label': 'Random with Compact Core', 'value': 'RandomCoreConfig'}
                    ],
                    value='YConfig'
                ),
                dcc.Dropdown(
                    id='nant-dropdown',
                    options=[
                        #                                {'label': '2 antennas', 'value': '2'},
                        {'label': '12 antennas', 'value': '12'},
                        {'label': '30 antennas', 'value': '30'},
                        {'label': '60 antennas', 'value': '60'}
                    ],
                    value='12'
                ),
            ] , style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}), 
            
            html.Div( [ 
                #html.H6(children='Set up the observatory and sky geometry'),
                
                #                    html.H6(children='Source Declination'),
                #                    dcc.Input(
                #                        id = 'declination-picker',
                #                        placeholder='Enter a declination value...',
                #                        value='+60.0'
                #                    ),
                #                    html.H6(children='Observatory Latitude'),
                #                    dcc.Input(
                #                        id = 'latitude-picker',
                #                        placeholder='Enter a latitude value...',
                #                        value='34.0'
                #                    )
                
                html.H6(children='Source Declination'), #,style={'fontSize': 14}),
                dcc.Slider(
                    id='declination-picker',
                    min=-90,
                    max=+90,
                    value=60,
                    marks={str(dec):str(dec) for dec in np.arange(-90,+91, 30)},
                    step=1,
                    included=False,
                    updatemode='mouseup'
                ) ,
                html.Br(),
                html.H6(children='Observatory Latitude'),
                dcc.Slider(
                    id='latitude-picker',
                    min=-90,
                    max=+90,
                    value=34,
                    marks={str(lat):str(lat) for lat in np.arange(-90,+91, 30)},
                    step=1,
                    included=False,
                    updatemode='mouseup'
                ) 
                
                #                        daq.NumericInput(
                #                            id = 'declination-picker',
                #                            label='Source Declination (deg)',
                #                            labelPosition='left',
                #                            size=120,
                #                            min=-30,
                #                            max=90,
                #                            value=+50.0
                #                            ),
                #                        daq.NumericInput(
                #                            id = 'latitude-picker',
                #                            label='Observatory Latitude (deg)',
                #                            labelPosition='left',
                #                            size=120,
                #                            min=-90,
                #                            max=+90,
                #                           value=+34.0
                #                            )
            ],  style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}) ,
            
            html.Div( [
                html.H6(children='Object to observe'),
                dcc.Dropdown(
                    id='source-dropdown',
                    options=[
                        {'label': 'Few Compact Sources', 'value': 'im1'},
                        {'label': 'One Point Source', 'value': 'im2'},
                        {'label': 'Multi-scale Structure', 'value': 'im3'}
                    ],
                    value='im1'
                ) ] , style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'})
            
        ], 
    ),
    
    
    html.Div(
        children=[
            html.Div( [ dcc.Graph(id='antenna-layout') ], 
                      style={'width': '33%', 'display': 'inline-block','vertical-align':'top'}),
            html.Div( [ dcc.Graph(id='uvcov-image') ], 
                      style={'width': '33%', 'display': 'inline-block','vertical-align':'top'}),
            html.Div( [ dcc.Graph(id='observed-image') ], 
                      style={'width': '33%', 'display': 'inline-block','vertical-align':'top'})
        ],
    ),
    
    html.Div(
        children=[
            html.Div( [
                html.H6(children='Expand or shrink the array layout'),
                dcc.Slider(
                    id='zoom-slider',
                    min=-1,
                    max=1,
                    value=0.0,
                    marks={
                        -0.5: { 'label': 'more compact', 'style': {'color': 'black'}},
                        0.0: {'label': 'normal', 'style': {'color': 'black'}},
                        0.5: {'label': 'more extended' , 'style': {'color': 'black'}}
                    },
                    step=0.25,
                    included=False,
                    updatemode='mouseup'
                ) 
            ], style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}), 
            html.Div( [
                html.H6(children='Pick data weighting scheme'),
                dcc.RadioItems(
                    id='weighting-picker',
                    options=[
                        {'label': 'Natural', 'value': 'natural'},
                        {'label': 'Robust', 'value': 'robust'},
                        {'label': 'Uniform', 'value': 'uniform'}
                    ],
                    value='natural',
                    labelStyle={'display': 'inline-block'}
                )
            ], style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}),
            html.Div( [ 
                html.H6(children='Select the observation hour-angle range'),
                dcc.RangeSlider(
                    id='timerange-slider',
                    count=1,
                    min=-6.0,
                    max=+6.0,
                    value=[-1.0,+1.0],
                    marks={str(ha): str(ha) for ha in range(-6,7,1)},
                    step=0.5
                ) ], style={'width': '30%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}),
        ], 
    )
    
]) #, style={'columnCount': 2})

#### Define all the callbacks here. 

### Update the Antenna Layout plot
@app.callback(
    [Output('antenna-layout', 'figure'),
     Output('uvcov-image', 'figure'),
     Output('observed-image', 'figure')],
    [Input('config-dropdown', 'value'),
     Input('timerange-slider', 'value'),
     Input('source-dropdown', 'value'),
     Input('nant-dropdown', 'value'),
     Input('zoom-slider', 'value'),
     Input('declination-picker', 'value'),
     Input('latitude-picker', 'value'),
     Input('weighting-picker','value')
     ])
def update_figure(selected_config, 
                  selected_has, 
                  selected_im, 
                  selected_nant, 
                  selected_zoom,
                  selected_declination, 
                  selected_latitude,
                  selected_weighting):

    ctx = dash.callback_context
 #   print 'Trig : ', ctx.triggered
#    print 'States : ', ctx.states
#    print 'Inputs : ', ctx.inputs
    
    #Trig :  [{'prop_id': u'config-dropdown.value', 'value': u'RandomConfig'}]

    thischanged=None
    if ctx.triggered[0]['prop_id'].count('config-dropdown'):
        thischanged = 'config'
    if ctx.triggered[0]['prop_id'].count('source-dropdown'):
        thischanged = 'source'
    if ctx.triggered[0]['prop_id'].count('timerange-slider'):
        thischanged = 'timerange'
    if ctx.triggered[0]['prop_id'].count('zoom-slider'):
        thischanged = 'antzoom'
    if ctx.triggered[0]['prop_id'].count('nant-dropdown'):
        thischanged = 'nant'
    if ctx.triggered[0]['prop_id'].count('declination-picker'):
        thischanged = 'declination'
    if ctx.triggered[0]['prop_id'].count('latitude-picker'):
        thischanged = 'latitude'
    if ctx.triggered[0]['prop_id'].count('weighting-picker'):
        thischanged = 'weighting'
        
    #print 'This changed : ', thischanged

    tim1 = time.time()
    if thischanged=='config' or thischanged=='antzoom' or thischanged=='nant':
        changeseed=True
        if thischanged=='antzoom' or thischanged=='nant':
            changeseed=False
        if eval(selected_nant)==2:
            selected_config='RandomConfig'
            print("Using random locations for 2 antennas")
        tel.calcAntList(configtype = selected_config, 
                        zoom=2**selected_zoom, 
                        changeseed=changeseed, 
                        nant=eval(selected_nant))

#    if thischanged=='antzoom':
#        tel.scaleAntList(zoom=selected_zoom)

    antlist = tel.getAntList()
    
    antlocsX = antlist['EastLoc']
    antlocsY = antlist['NorthLoc']

    tim2 = time.time()

#    print antlocsX, antlocsY

    ### Prepare contents of antenna layout plot

    traces1=[]
    traces1.append( go.Scatter(
            x=antlocsX,
            y=antlocsY,
            text=selected_config,
            mode='markers',
            opacity=0.7,
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
        ))
    tim3 = time.time()


    ### Prepare contents of observed image.
    ### Slider callback too
    if thischanged=='config' or  thischanged=='timerange' or  thischanged=='antzoom' or     thischanged=='nant' or  thischanged=='declination' or   thischanged=='latitude' or thischanged=='weighting':
        tel.makeUVcov(has=selected_has, 
                      dec=selected_declination,
                      obslatitude=selected_latitude,
                      weighting=selected_weighting)
    tim4 = time.time()

    traces3=[]
    traces3.append( go.Heatmap(
            z=tel.getUVcov() ))


    ## sky callback
    if thischanged=='source':
        tel.setsky(imtype=selected_im)
    tim5 = time.time()
    ## Sim
    tel.makeImage()
    tim6 = time.time()
    
    traces2=[]
    traces2.append( go.Heatmap(
            z=tel.getImage() ))

    tim7=time.time()

#    print 'Ant read time : ', tim2-tim1
#    print 'Ant plot time : ', tim3-tim2
#    print 'UVcov time : ', tim4-tim3
#    print 'Source time : ', tim5-tim4
#    print 'Observe time :', tim6-tim5
#    print 'Make raster : ', tim7-tim6

#    print 'Total time in callback : ', tim7-tim1, ' sec'

    ### Return list of outputs, sync'd with specification above

    dispsize = 400

    return [{
        'data': traces1,
        'layout': go.Layout(
            xaxis={'title': 'X Position (m)','range':[-1000,1000]},
            yaxis={'title': 'Y Position (m)','range':[-1000,1000]},
            title="ARRAY CONFIGURATION",
            width = dispsize, height = dispsize,
            autosize = True
        ) 
    },
    {
        'data': traces3,
        'layout': go.Layout(
            xaxis={'title': 'Spatial frequency : U (pixels)'},
            yaxis={'title': 'Spatial frequency : V (pixels)'},
            title="SPATIAL FREQUENCY COVERAGE",
            width = dispsize, height = dispsize,
            autosize = True
        ) 
    },
    {
        'data': traces2,
        'layout': go.Layout(
            xaxis={'title': 'Right Ascension (pixels)'},
            yaxis={'title': 'Declination (pixels)'},
            title="OBSERVED IMAGE",
            width = dispsize, height = dispsize,
            autosize = True
        ) 
    }
    ]



#
#### Update the Observed Image
#@app.callback(
#    Output('observed-image', 'figure'),
#    [Input('timerange-slider', 'value')])
#def update_figure(timran):
#
#    ### Slider callback too
#    tel.makeUVcov(has=timran, dec=+50.0,obslatitude=34.0)
#    ## sky callback
#    tel.setsky()
#    ## Sim
#    tel.makeImage()
#    
#
#    traces=[]
#    traces.append( go.Heatmap(
#            z=tel.getImage() ))
#
#    return {
#        'data': traces,
#        'layout': go.Layout(
#            xaxis={'title': 'Right Ascension'},
#            yaxis={'title': 'Declination'},
#            width = 500, height = 500,
#            autosize = False,
#
# #           margin={'l': 10, 'b': 20, 't': 0, 'r': 0},
##            legend={'x': 0, 'y': 1},
#            hovermode='closest'
#        ) 
#    }


#### Start the App

if __name__ == '__main__':
    app.run_server(debug=True)
