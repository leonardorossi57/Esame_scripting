# Import useful libraries

import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, exceptions
import module as mod # The plan is to put here the functions which do most of the work
# import plotly.express as px
import time

# The following imports are necessary for long callbacks
from dash.long_callback import DiskcacheLongCallbackManager

import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# Style of the GUI

app = Dash(__name__)

# Layout of the interface
app.layout = html.Div([
    # Title
    html.H1(children = 'Simulation an data analysis for an optics experiment about spatial coherence'),

    # Text introduction
    html.Div([
        html.Div([
        dcc.Markdown("""
            The simulation is divided in two parts: first, the code generates a certain number of 1D speckle fields, and each field is 
            then spatially filtered to produce a partially coherent field. The number of fields and the type of filtering may be selected 
            in the boxes below. Since in the physical experiment the speckle field is produced by a rough glass surface which might have 
            a non-negligible correlation length, it's also possible to generate fields which take that into account.  
            In the second part, the code simulates the production of Young interference fringes by passage of the (filtered) field through 
            a double slit. It is expected that the visibility of the average pattern (i.e., the correlation length of the filtered field) should 
            be related to the amount of spatial filtering. 
        """)
        ],
        className = 'inner')
    ],
    className = 'container'),
    
    # Input parameters for the first part of the simulation

    html.H2(children = 'First part: generation of a number of speckle fields'),

    html.Div(children = [
        html.Div(children = [
            html.H3(children = 'Choose the geometry of the set-up and the wavelength'),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Size of the source ($\mathrm{cm}$)', mathjax = True)
            ),
            # For now I consider only one transversal and one longitudinal dimension
            dcc.Slider(
                0.1,
                1,
                step = 0.05,
                value = 0.5,
                marks = {str(x): str(x) for x in np.arange(5, 10, 1)},
                id='hor-size'
            ),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Distance from the source to the first image ($\mathrm{cm}$)', mathjax = True)
            ),
            dcc.Slider(
                10,
                50,
                step = 5,
                value = 15,
                marks = {str(x): str(x) for x in np.arange(10, 50, 5)},
                id='dist'
            ),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Wavelength ($\mathrm{nm}$)', mathjax = True)
            ),
            # For now I consider only one transversal and one longitudinal dimension
            dcc.Slider(
                400,
                600,
                step = 5,
                value = 500,
                marks = {str(x): str(x) for x in np.arange(400, 600, 100)},
                id='wave-len'
            ),
        ],
        className = 'side'
        ),

        html.Div(children = [
            html.H3(children = 'Select the number of fields to produce, the number of "scatterers" and the correlation length of the rough glass surface'),
            html.Br(),
            html.Label(
                dcc.Markdown('Number of speckle fields to produce')
            ),
            dcc.Slider(
                10,
                1000,
                step = 1,
                value = 100,
                marks = {str(x): str(x) for x in np.arange(10, 1000, 200)},
                id='field-number'
            ),
            html.Br(),
            html.Label(
                dcc.Markdown('Number of scatters per field')
            ),
            dcc.Slider(
                100,
                2000,
                step = 1,
                value = 1000,
                marks = {str(x): str(x) for x in np.arange(100, 2000, 400)},
                id='scatterer-number'
            ),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Correlation length of the rough glass surface ($\mu\mathrm{m}$)', mathjax = True)
            ),
            dcc.Slider(
                0,
                30,
                step = 1,
                value = 0,
                marks = {str(x): str(x) for x in np.arange(0, 30, 3)},
                id='correlation-length'
            ),
        ],
        className = 'side'
        ),
    ],
    className = 'container'),
    
    html.Div(children = [
        html.H3(children = 'START SIMULATION'),
        html.Div([
            html.Button(id='part-one-button', children='Start'), 
            html.Button(id='cancel-one', children = 'Cancel'),
        ],
        className = 'start'
        ),
        html.Div([
            html.P(id='counter', children = 'Simulation number 1'),
            html.Progress(id='progress-bar-one')
        ],
        className = 'start'
        ),
    ],
    className = 'left'
    ),

    html.H2(children = 'Second part: propagation, spatial filtering and interference'), # Second part of the simulation

    html.Div(children = [
        html.Div(children = [
            html.H3(children = 'Select spatial filtering parameters'),
            html.Br(),
            html.Label(
                dcc.Markdown('Type of filtering')
            ),
            dcc.RadioItems(
                ['Rectangular', 'Gaussian'],
                'Rectangular',
                id='filtering-type',
                inline=True
            ),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Filtering ($\mathrm{cm}^{-1}$)', mathjax = True)
            ),
            # I'm going to have a "screen dimension" of about x_M = 10 cm, with a resolution of dx = 0.05 cm, so the bounds in k-space are
            # k_M = pi/dx = 62.8 cm^(-1) with step dk = pi/x_M = 0.314
            # Note that here k = 2pi/lambda.
            dcc.Slider( 
                0.314,
                62.8,
                step = 0.314,
                value = 10,
                marks = {str(x): str(x) for x in np.arange(1, 61, 20)},
                id='filter-width'
            ),
        ],
        className = 'side'
        ),

        html.Div(children = [
            html.H3('Choose set-up parameters'),
            html.Br(),
            html.Label(
                dcc.Markdown(r'Distance from slits to screen ($\mathrm{cm}$)', mathjax = True)
            ),
            dcc.Slider( 
                10,
                50,
                step = 5,
                value = 20,
                marks = {str(x): str(x) for x in np.arange(1, 500, 100)},
                id='dist-2'
            ),
        ],
        className = 'side'
        ),
    ],
    className = 'container'
    ),

    html.Div(children = [
        html.H3(children = 'START SIMULATION'),
        html.Div([
            html.Button(id='part-two-button', children='Start'), 
            html.Button(id='cancel-two', children = 'Cancel'),
        ],
        className = 'start'
        ),
        html.Div([
            html.P(id='counter-two', children = '\tSimulation number 1'),
            html.Progress(id='progress-bar-two')
        ],
        className = 'start'
        ),
    ],
    className = 'left'
    ),
    
    html.H2(children = 'Data Analysis') # Third part: data analysis

    # I didn't do anything yet here
],
className = 'layout')

# Here I should add the necessary callbacks

@app.long_callback(
    output = [
        Output('counter', 'children')
    ],
    inputs = [
        Input('part-one-button', 'n_clicks'),
        State('hor-size', 'value'),
        State('dist', 'value'),
        State('field-number', 'value'),
        State('scatterer-number', 'value'),
        State('correlation-length', 'value'),
        State('wave-len', 'value')
    ],
    running=[
        (Output('part-one-button', 'disabled'), True, False),
        (Output('cancel-one', 'disabled'), False, True),
        (
            Output('counter', 'style'),
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-one', 'style'),
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel=[Input('cancel-one', 'n_clicks')],
    progress=[Output('progress-bar-one', 'value'), Output('progress-bar-one', 'max')],
    manager=long_callback_manager
)
def generate_fields(set_progress, n_clicks, source_size, dist, field_num, scatt_num, corr, wavelen):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    for i in range(field_num):
        field, screen = mod.generate_speckle_field(corr, source_size, dist, scatt_num, wavelen)
        field_data = pd.DataFrame(np.stack((screen, field.real, field.imag), axis = -1), columns = ['screen', 'spec_re', 'spec_im'])
        field_data.to_csv('Speckles/speckle_num_{}.csv'.format(i))
        set_progress((str(i + 1), str(field_num)))
    return ['Simulation number {}'.format(n_clicks + 1)]

if __name__ == '__main__':
    app.run(debug=True)