# Import useful libraries

import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, exceptions
import module as mod # The plan is to put here the functions which do most of the work
import plotly.express as px
import os

# The following imports are necessary for long callbacks
from dash.long_callback import DiskcacheLongCallbackManager

import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# Create the app
app = Dash(__name__)

# Layout of the interface; I define the layout as a function, as this allows the layout to be updated upon refreshing the page.
def serve_layout():
    return html.Div([
        # Title
        html.H1(children = 'Simulation and data analysis for an optics experiment about spatial coherence'),
        
        dcc.Tabs(id = 'select-tab', 
            value = 'intro',
            children = [
                dcc.Tab(label = 'Introduction', value = 'intro'),
                dcc.Tab(label = 'Generate speckle fields', value = 'simu-1'),
                dcc.Tab(label = 'Filter and generate interference pattern', value = 'simu-2'),
                dcc.Tab(label = 'Data analysis', value = 'data-an')
            ]
        ),
        
        # First tab
        html.Div(children = [
            html.H2(children = 'Introduction'),
            html.Div([ 
                html.Div([
                    html.Img(src = 'assets/part_12.png', width = '700px')
                ],
                className = 'box_blue'),
                # Text introduction
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
                className = 'box_blue'),
            ],
            className = 'container_blue'
            ),
        ],
        style = {'dispay': 'none'}, # The style is updated by the callback when the tab is selected or deselected
        id = 'first-tab'
        ),

        # Second tab
        html.Div(children = [
            html.H2(children = 'First part: generation of the speckle fields'),
    
            html.Div(children = [
                html.Div(children = [
                    html.Img(src = 'assets/part_1.png', width = '700px')
                ],
                className = 'box'
                ),
                html.Div(children = [
                    html.H3(children = 'START SIMULATION'),
                    html.Div([
                        # These buttons let the user start or stop the simulation
                        html.Button(id='part-one-button', children='Start'), 
                        html.Button(id='cancel-one', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # This is just a counter of the number of times the simulation has been ran
                        html.P(id='counter', children = 'Simulation number 1'),
                        # Progress bar
                        html.Progress(id='progress-bar-one')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box'
                ),
            ],
            className = 'container'
            ),
            html.Div(children = [ 
                # Input parameters for the first part of the simulation
                html.Div(children = [
                    html.H3(children = 'Choose the geometry of the set-up and the wavelength'),
                    html.Br(),
                    html.Label(
                        # Input the size of the "source", the source being essentially the portion of the rough glass surface on which the laser shines
                        dcc.Markdown(r'Size of the source ($\mathrm{cm}$)', mathjax = True) 
                    ),
                    # For now I consider only one transversal and one longitudinal dimension
                    dcc.Slider(
                        0.1,
                        1,
                        step = 0.05,
                        value = 0.5,
                        marks = {str(x): str(x) for x in [0.5, 1]},
                        id='hor-size'
                    ),
                    html.Br(),
                    # Here the chosen value for the size of the source is shown on screen
                    html.Div(id = 'hor-size-out'),
                    html.Br(),
                    html.Label(
                        # Input the distance over which the field propagates (forming a speckle field in the process) before the filtering
                        dcc.Markdown(r'Distance from the source to the first image ($\mathrm{cm}$)', mathjax = True)
                    ),
                    dcc.Slider(
                        10,
                        50,
                        step = 5,
                        value = 15,
                        marks = {str(x): str(x) for x in np.arange(10, 60, 10)},
                        id ='dist'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div(id = 'dist-out'),
                    html.Br(),
                    html.Label(
                        # Input laser wavelength
                        dcc.Markdown(r'Wavelength ($\mathrm{nm}$)', mathjax = True)
                    ),
                    dcc.Slider(
                        400,
                        600,
                        step = 5,
                        value = 500,
                        marks = {str(x): str(x) for x in np.arange(400, 700, 100)},
                        id='wave-len'
                    ),
                    html.Br(),
                    # Show chosen value on screeen
                    html.Div(id = 'wave-len-out'),
                ],
                className = 'left'
                ),

                html.Div(children = [
                    html.H3(children = 'Select the number of fields to produce, the number of "scatterers" and the correlation length of the rough glass surface'),
                    html.Br(),
                    html.Label(
                        # Input the number of speckle fields to produce 
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
                    # Show chosen value on screen
                    html.Div(id = 'field-number-out'),
                    html.Br(),
                    html.Label(
                        # Input the number of "scatterers" which produce the field. Essentialy, this number is the number of points of the source.
                        # I found it not practical to randomize the points for the interference part too, but it is possible to do it at least for the 
                        # first part, and this should minimize spurious effects due to the source form and sharp edges. 
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
                    # Show chosen value on screen
                    html.Div(id = 'scatterer-number-out'),
                    html.Br(),
                    html.Label(
                        # Input the correlation length of the surface. 
                        dcc.Markdown(r'Correlation length of the rough glass surface ($\mu\mathrm{m}$)', mathjax = True)
                    ),
                    dcc.Slider(
                        0,
                        30,
                        step = 1,
                        value = 0,
                        marks = {str(x): str(x) for x in np.arange(0, 30, 10)},
                        id='correlation-length'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div(id = 'correlation-length-out'),
                ],
                className = 'right'
                ),
            ],
            className = 'container'
            ),
        ],
        style = {'display': 'none'},
        id = 'second-tab'
        ),

        # Third tab
        html.Div(children = [
            html.H2(children = 'Second part: propagation, spatial filtering and interference'), # Second part of the simulation
            html.Div(children = [
                html.Div(children = [
                    html.Img(src = 'assets/part_2.png', width = '700px')
                ],
                className = 'box_green'
                ),
                html.Div(children = [
                    html.H3(children = 'START SIMULATION'),
                    html.Div([
                        # These buttons let the user start or stop the simulation
                        html.Button(id='part-two-button', children='Start'), 
                        html.Button(id='cancel-two', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Just a counter
                        html.P(id='counter-two', children = 'Simulation number 1'),
                        # Progress bar
                        html.Progress(id='progress-bar-two')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_green'
                ),
            ],
            className = 'container_green'
            ),
            html.Div(children = [
                html.Div(children = [
                    html.H3(children = 'Select spatial filtering parameters'),
                    html.Br(),
                    html.Label(
                        # Input the type of filtering, which should give different statistics of the filtered field (i.e., sinc or gaussian correlation function)
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
                        # Input how much the spatial spectrum should be filtered
                        dcc.Markdown(r'Filtering ($\mathrm{cm}^{-1}$)', mathjax = True)
                    ),
                    # I'm going to have a "screen dimension" of about x_M = 10 cm, with a resolution of dx = 0.02 cm, so the bounds in k-space are
                    # k_M = pi/dx = 62.8 cm^(-1) with step dk = pi/x_M = 0.314
                    # Note that here k = 2pi/lambda.
                    dcc.Slider( 
                        0.314,
                        62.8,
                        step = 0.314,
                        value = 10,
                        marks = {str(x): str(x) for x in np.arange(10, 60, 10)},
                        id='filter-width'
                    ),
                    html.Br(),
                    # Show the chosen value on screen
                    html.Div(id = 'filter-width-out'),
                ],
                className = 'left_green'
                ),

                html.Div(children = [
                    html.H3('Choose set-up parameters'),
                    html.Br(),
                    html.Label(
                        # Input the distance from the interference slits and the screen on which the pattern appears. 
                        dcc.Markdown(r'Distance from slits to screen ($\mathrm{cm}$)', mathjax = True)
                    ),
                    dcc.Slider( 
                        5000,
                        10000,
                        step = 50,
                        value = 7000,
                        marks = {str(x): str(x) for x in np.arange(5000, 10000, 1000)},
                        id='dist-2'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div(id = 'dist-2-out'),
                    html.Br(),
                    html.Label(
                        # Input slits spacing
                        dcc.Markdown(r'Distance between slits ($\mathrm{mm}$)', mathjax = True)
                    ),
                    dcc.Slider( 
                        4,
                        20,
                        step = 0.5,
                        value = 4,
                        marks = {str(x): str(x) for x in np.arange(5, 20, 5)},
                        id='slits-dist'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div(id = 'slits-dist-out'),
                    html.Br(),
                    # Input slit width 
                    html.Label(
                        dcc.Markdown(r'Slit width ($\mathrm{mm}$)', mathjax = True)
                    ),
                    dcc.Slider( 
                        1,
                        4,
                        step = 0.2,
                        value = 1,
                        marks = {str(x): str(x) for x in np.arange(1, 4, 1)},
                        id='slit-width'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div(id = 'slit-width-out'),
                ],
                className = 'right_green'
                ),
            ],
            className = 'container_green'
            ),

            html.Div(children = [
                # Show the pattern which results form the simulation, averaged over all the speckle fields
                dcc.Graph(id = 'pattern', style={'width': '1400px', 'height': '800px', 'top': '50%', 'left': '50%', 'margin-left': '-10px', 'margin-top': '-10px'}),
            ],
            className = 'graph'
            ),
        ],
        style = {'display': 'none'},
        id = 'third-tab'
        ),

        # Fourth tab
        html.Div(children = [
            html.H2(children = 'Data Analysis'), # Third part: data analysis

            html.Div(children = [
                html.Div(children = [
                    html.H3(children = 'PLOT'),
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('Choose pattern to plot')
                    ),
                    dcc.Dropdown(os.listdir('Patterns'), id = 'select-pattern'),
                    html.Div([
                        html.Button(id='plot-button', children='Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-plot', children = 'Plot number 1')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
                html.Div([
                # Text introduction
                dcc.Markdown("""
                    Once generated a bunch of patterns with different filterings with the functions above, refresh the page *only once* before 
                    starting the analysis.
                """)
                ],
                className = 'box_pink')
            ],
            className = 'container_pink'
            ),

            # I should add ginput-like options to interact with the graph and extract data manually form it

            html.Div(children = [
                dcc.Graph(id = 'pattern-analysis', style={'width': '1400px', 'height': '800px', 'top': '50%', 'left': '50%', 'margin-left': '-10px', 'margin-top': '-10px'}, mathjax = True),
            ],
            className = 'graph'
            ),

            html.Div([
                html.Div([
                dcc.Markdown("""
                    The analysis consists of the calculation of the visibility of the interference patterns, which corresponds to the absolute value of the *field* 
                    correlation function of the speckle field (absolute value of the *complex degree of coherence*). In addition, the center of the pattern could be a 
                    local maximum, in which case the phase of the correlation function is +1, or a local minimum, in which case the phase is -1.
                """)
                ],
                className = 'inner_pink')
            ],
            className = 'container_pink'),

            html.Div(children = [
                html.Div(children = [
                    html.H3(children = 'START ANALYSIS'),
                    html.Div([
                        # This buttons let the user start or stop the analysis (I did not yet add the callback so for the time being the buttons actually do nothing)
                        html.Button(id='part-three-button', children='Start'), 
                        html.Button(id='cancel-three', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Counter and progress bar
                        html.P(id='counter-three', children = 'Analysis number 1'),
                        html.Progress(id='progress-bar-three')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
                ],
            className = 'container_2_pink'
            ),
        ],
        style = {'display': 'none'},
        id = 'fourth-tab'
        )
    ],
    className = 'layout'
    )

app.layout = serve_layout

# Callbacks

@callback( # This is the callback for the tabs
    Output('first-tab', 'style'),
    Output('second-tab', 'style'),
    Output('third-tab', 'style'),
    Output('fourth-tab', 'style'),
    Input('select-tab', 'value')
)
def render(tab):
    on = {'display': 'block'}
    off = {'display': 'none'}

    if tab == 'intro':
        return on, off, off, off
    elif tab == 'simu-1':
        return off, on, off, off
    elif tab == 'simu-2':
        return off, off, on, off
    elif tab == 'data-an':
        return off, off, off, on

@callback( # This serves to return the values selected in the sliders
    Output('hor-size-out', 'children'),
    Output('dist-out', 'children'),
    Output('wave-len-out', 'children'),
    Output('field-number-out', 'children'),
    Output('scatterer-number-out', 'children'),
    Output('correlation-length-out', 'children'),
    Output('filter-width-out', 'children'),
    Output('dist-2-out', 'children'),
    Output('slits-dist-out', 'children'),
    Output('slit-width-out', 'children'),
    Input('hor-size', 'value'),
    Input('dist', 'value'),
    Input('wave-len', 'value'),
    Input('field-number', 'value'),
    Input('scatterer-number', 'value'),
    Input('correlation-length', 'value'),
    Input('filter-width', 'value'),
    Input('dist-2', 'value'),
    Input('slits-dist', 'value'),
    Input('slit-width', 'value'),
)
def update_values(a, b, c, d, e, f, g, h, i, l): 
    return a, b, c, d, e, f, g, h, i, l

@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter', 'children') # Only output is the counter
    ],
    inputs = [
        Input('part-one-button', 'n_clicks'), # The only input is the click of the 'start' button
        State('hor-size', 'value'), # The other parameters are passed as states, so changing them does not trigger the start of the simulation
        State('dist', 'value'),
        State('field-number', 'value'),
        State('scatterer-number', 'value'),
        State('correlation-length', 'value'),
        State('wave-len', 'value')
    ],
    running=[ # When the simulation is running,
        (Output('part-one-button', 'disabled'), True, False), # The start button is disabled
        (Output('cancel-one', 'disabled'), False, True), # And it is possible to cancel the operation
        (
            Output('counter', 'style'), # Show or hid the counter (visible when not running, hidden when running)
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-one', 'style'), # Show or hid the progress bar (hidden when not running, visible when running)
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-one', 'n_clicks')], # Link to cancel button id
    progress = [Output('progress-bar-one', 'value'), Output('progress-bar-one', 'max')], # Link to progress bar id
    manager = long_callback_manager
)
def generate_fields(set_progress, n_clicks, source_size, dist, field_num, scatt_num, corr, wavelen):
    if n_clicks is None:
        raise exceptions.PreventUpdate() # This is necessary in order for the simulation not to start automatically upon launching the app
    
    for i in range(field_num):
        field, screen = mod.generate_speckle_field(corr, source_size, dist, scatt_num, wavelen) # Generate a field
        field_data = pd.DataFrame(np.stack((screen, field.real, field.imag), axis = -1), columns = ['screen', 'spec_re', 'spec_im']) # Create a data frame
        field_data.to_csv('Speckles/speckle_num_{}.csv'.format(i)) # Store in csv
        set_progress((str(i + 1), str(field_num))) # Update progress bar

    return ['Simulation number {}'.format(n_clicks + 1)] # Return counter

@app.long_callback(
    # This is the callback for the second simulation. 
    output = [
        Output('counter-two', 'children'), # Counter
        Output('pattern', 'figure') # Graph
    ],
    inputs = [
        Input('part-two-button', 'n_clicks'), # As before, the only input is the click on the button and the other parameters are states.
        State('filtering-type', 'value'),
        State('filter-width', 'value'),
        State('dist-2', 'value'),
        State('slits-dist', 'value'),
        State('slit-width', 'value'),
        State('wave-len', 'value')
    ],
    running=[ # This is identical to above
        (Output('part-two-button', 'disabled'), True, False),
        (Output('cancel-two', 'disabled'), False, True),
        (
            Output('counter-two', 'style'),
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-two', 'style'),
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel=[Input('cancel-two', 'n_clicks')],
    progress=[Output('progress-bar-two', 'value'), Output('progress-bar-two', 'max')],
    manager=long_callback_manager
)
def filter_and_interfere(set_progress, n_clicks, filter_type, filter_width, dist_2, slits_dist, slit_width, wavelen):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    screen_size = 20 # [cm] 
    dx = 0.02 # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays
    pattern = np.zeros(dim) # Array containing the interference pattern
    
    vect = os.listdir('Speckles')
    
    k = 1
    for i in vect:
        field_data = pd.read_csv('Speckles/' + i) # Read the csv with the speckle field
        field = field_data['spec_re'].to_numpy() + field_data['spec_im'].to_numpy() * 1j # Convert to ndarray
        screen = field_data['screen'].to_numpy() 
        filt_field = mod.filter(filter_type, field, filter_width) # Spatially filter the field

        # Add the pattern generated by the speckle field to the average
        pattern += mod.create_pattern(filt_field, dist_2, slits_dist, slit_width, screen, dim, wavelen) 
        set_progress((str(k), str(len(vect)))) # Update progress bar
        k = k + 1


    pattern_data = pd.DataFrame(np.stack((screen, pattern), axis = -1), columns = ['screen', 'pattern']) # Convert to data frame
    fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = 'Pattern di interferenza mediato') # Create the figure of the graph
    pattern_data.to_csv('Patterns/Pattern_filt_{}.csv'.format(filter_width)) # Store the pattern to csv

    return ['Simulation number {}'.format(n_clicks + 1)], fig # Return the outputs

@callback(
    # This is the callback for the plot of an individual pattern in the data analysis part. A long callback isn't necessary here
    Output('pattern-analysis', 'figure'), # Output a counter and the graph
    Output('counter-plot', 'children'),
    Input('plot-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-pattern', 'value')
)
def plot_pattern(n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv
    filter_width = patt_name.split('_')[-1].split('.')[0] # Obtain the filter width from the csv file name
    my_string = r'Interference pattern, filtering = {} '.format(filter_width) 
    fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = my_string) # Create the figure

    return fig, ['Plot number {}'.format(n_clicks + 1)]
    
if __name__ == '__main__':
    app.run(debug=True)