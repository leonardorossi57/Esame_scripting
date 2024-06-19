# Import useful libraries

import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State
import module as mod
# import plotly.express as px

# Style of the GUI
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

# Layout of the page
app.layout = html.Div([
    # Title
    html.H1(children = 'Simulation an data analysis for an optics experiment about spatial coherence'),

    # Text introduction
    html.Div([
        dcc.markdown("""
            The simulation is divided in two parts: first, the code generates a certain number of 2D speckle fields, and each field is 
            then spatially filtered to produce a partially coherent field. The number of fields and the type of filtering may be selected 
            in the boxes below. Since in the physical experiment the speckle field is produced by a rough glass surface which might have 
            a non-negligible correlation lenght, it's also possible to generate fields which take that into account.  
            In the second part, the code simulates the production of Young interference fringes by passage of the (filtered) field through 
            a double slit. It is expected that the visibility of the average pattern (i.e., the correlation length of the filtered field) should 
            be related to the amount of spatial filtering. 
        """)
    ]),
    
    # Input parameters for the first part of the simulation

    html.H2(children = 'First part: generation of a number of speckle fields'),

    html.Div(children = 'Choose the geometry of the set-up'),

    html.Div(children = 'Horizontal size of the source (cm)'),
    dcc.Slider(
        5,
        10,
        step = 0.5,
        value = 10,
        marks = {str(x): str(x) for x in np.arange(5, 10, 0.5)},
        id='hor-size'
    ),
    html.Div(children = 'Vertical size of the source (cm)'),
    dcc.Slider(
        5,
        10,
        step = 0.5,
        value = 10,
        marks = {str(x): str(x) for x in np.arange(5, 10, 0.5)},
        id='ver-size'
    ),
    html.Div(children = 'Distance from the source to the first image (cm)'),
    dcc.Slider(
        10,
        50,
        step = 0.5,
        value = 15,
        marks = {str(x): str(x) for x in np.arange(5, 10, 0.5)},
        id='dist'
    ),

    html.Div(children = 'Select the number of fields to produce, the number of "scatterers" and the correlation length of the rough glass surface'),

    html.Div(children = 'Number of speckle fields to produce'),
    dcc.Slider(
        10,
        1000,
        step = 1,
        value = 100,
        marks = {str(x): str(x) for x in np.arange(10, 1000, 1)},
        id='field-number'
    ),
    html.Div(children = 'Number of scatters per field'),
    dcc.Slider(
        100,
        2000,
        step = 1,
        value = 1000,
        marks = {str(x): str(x) for x in np.arange(100, 2000, 1)},
        id='scatterer-number'
    ),
    html.Div(children = 'Correlation length of the rough glass surface (micrometers)'),
    dcc.Slider(
        0,
        30,
        step = 1,
        value = 0,
        marks = {str(x): str(x) for x in np.arange(0, 30, 1)},
        id='correlation-length'
    ),
    html.Div(children = 'Start simulation'),
    html.Button(id='submit-button-state', n_clicks = 0, children='Enter'),

    html.Div(children = 'Type of filtering'),
    dcc.RadioItems(
        ['Rectangular', 'Gaussian'],
        'Rectangular',
        id='filtering-type',
        inline=True
    ),
    
])