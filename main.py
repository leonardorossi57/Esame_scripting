# Import useful libraries

import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, exceptions
import module as mod # The plan is to put here the functions which do most of the work
import plotly.express as px
import plotly.graph_objects as go
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
                        > The simulation is divided in two parts: 
                                 
                        > First, the code generates a certain number of 1D speckle fields, and each field is 
                        then spatially filtered to produce a partially coherent field. The number of fields and the type of filtering may be selected 
                        in the boxes below. Since in the physical experiment the speckle field is produced by a rough glass surface which might have 
                        a non-negligible correlation length, it's also possible to generate fields which take that into account.  
                                 
                        > In the second part, the code simulates the production of Young interference fringes by passage of the (filtered) field through 
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
                    html.H3(children = 'PLOT A SAMPLE FIELD'),
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('Choose sample field to plot')
                    ),
                    dcc.Dropdown(os.listdir('Speckles')[:10], id = 'select-field-plot'),
                    html.Div([
                        html.Button(id='plot-field', children='Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-field-plot', children = 'Plot number 1')
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
                dcc.Graph(id = 'sample-speckle', style={'width': '1400px', 'height': '800px'}, mathjax = True),
            ],
            className = 'graph'
            ),

            html.Div(children = [ 
                # Input parameters for the first part of the simulation
                html.Div(children = [
                    html.H3(children = 'Geometry of the set-up and wavelength'),
                    html.Br(),
                    html.Div(
                        # Input the size of the "source", the source being essentially the portion of the rough glass surface on which the laser shines
                        dcc.Markdown(r'> We suppose that the beam is initially collimated, with a diameter of $0.5 \, \mathrm{cm}$', mathjax = True) 
                    ),
                    # For now I consider only one transversal and one longitudinal dimension

                    html.Br(),
                    html.Label(
                        # Input the distance over which the field propagates (forming a speckle field in the process) before the filtering
                        dcc.Markdown(r'> The speckle field is formed $15 \, \mathrm{cm}$ away from the rough glass surface', mathjax = True)
                    ),

                    html.Br(),
                    html.Label(
                        # Input laser wavelength
                        dcc.Markdown(r'> The wavelength is chosen to be $500 \, \mathrm{nm}$)', mathjax = True)
                    ),
                    html.Br(),
                    # Show chosen value on screeen
                ],
                className = 'left'
                ),

                html.Div(children = [
                    html.H3(children = 'Number of fields produced, number of "scatterers" and correlation length of the rough glass surface'),
                    html.Br(),
                    html.Label(
                        # Input the number of speckle fields to produce 
                        dcc.Markdown(r"""
                                     $200$ speckle fields are generated by default for statistics. 
                                     If the correlation length of the source (i.e. the rough glass surface) is not zero, 
                                     more statistics could be necessary ($\sim 1000$)
                                     """, mathjax = True)
                    ),
                    dcc.Slider(
                        200,
                        2000,
                        step = 100,
                        value = 200,
                        marks = {str(x): str(x) for x in np.arange(200, 2000, 200)},
                        id='field-number'
                    ),
                    html.Br(),
                    html.Div([
                        dcc.Markdown(id = 'field-number-out',  mathjax = True)
                    ]),
                    html.Br(),
                    html.Label(
                        # Input the number of "scatterers" which produce the field. Essentialy, this number is the number of points of the source.
                        # I found it not practical to randomize the points for the interference part too, but it is possible to do it at least for the 
                        # first part, and this should minimize spurious effects due to the source form and sharp edges. 
                        dcc.Markdown(r'The speckle field is generated with a monte carlo randomization, with $1000$ points on the source', mathjax = True)
                    ),
                    html.Br(),
                    html.Label(
                        # Input the correlation length of the surface. 
                        dcc.Markdown(r'Input the correlation length of the rough glass surface ($\mu\mathrm{m}$)', mathjax = True)
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
                    html.Div([
                        dcc.Markdown(id = 'correlation-length-out', mathjax = True)
                    ]),
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
                    html.H3(children = 'Spatial filtering parameters'),
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
                        dcc.Markdown(r'Filtering range ($\mathrm{cm}^{-1}$)', mathjax = True)
                    ),
                    # I'm going to have a "screen dimension" of about x_M = 10 cm, with a resolution of dx = 0.02 cm, so the bounds in k-space are
                    # k_M = pi/dx = 62.8 cm^(-1) with step dk = pi/x_M = 0.314
                    # Note that here k = 2pi/lambda.
                    dcc.RangeSlider( 
                        0.3,
                        60.3,
                        step = 2,
                        value = [0.3, 10],
                        marks = {str(x): str(x) for x in np.arange(10, 60, 10)},
                        id='filter-width'
                    ),
                    html.Br(),
                    # Show the chosen value on screen
                    html.Div([
                        dcc.Markdown(id = 'filter-width-out', mathjax = True)
                    ]),
                ],
                className = 'left_green'
                ),

                html.Div(children = [
                    html.H3('Set-up parameters'),
                    html.Br(),
                    html.Label(
                        # Input the distance from the interference slits and the screen on which the pattern appears. 
                        dcc.Markdown(r'The interference patterns are calculated in a far field approximation', mathjax = True)
                    ),
                    html.Br(),
                    html.Label(
                        # Input slits spacing
                        dcc.Markdown(r'Distance between slits range ($\mathrm{mm}$)', mathjax = True)
                    ),
                    dcc.RangeSlider( 
                        2,
                        20,
                        step = 0.5,
                        value = [4, 10],
                        marks = {str(x): str(x) for x in np.arange(5, 20, 5)},
                        id='slits-dist'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div([
                        dcc.Markdown(id = 'slits-dist-out', mathjax = True)
                    ]),
                    html.Br(),
                    # Input slit width 
                    html.Label(
                        dcc.Markdown(r'The slits are 1 $\mathrm{mm}$ wide', mathjax = True)
                    ),
                ],
                className = 'right_green'
                ),
            ],
            className = 'container_green'
            ),

            html.Div(children = [
                # Show the pattern which results form the simulation, averaged over all the speckle fields
                dcc.Graph(id = 'pattern', style={'width': '1400px', 'height': '800px'}),
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
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('Choose pattern to view')
                    ),
                    dcc.Dropdown(os.listdir('Patterns'), id = 'select-pattern'),
                    html.H3(children = 'PLOT'),
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
                    html.H3(children = 'PRELIMINAR ANALYSIS'),
                    html.Div(children = [
                        html.Div([
                            html.Label(
                                dcc.Markdown('Guess fit parameter (visibility)')
                            ),
                            html.Br(),
                            dcc.Slider(
                                0.1, 
                                1,
                                step = 0.1,
                                value = 0.5, 
                                marks = {str(x/10): str(x/10) for x in np.arange(0, 10, 2)},
                                id = 'fit-guess'
                            )
                        ],
                        className = 'smol_l_pink'
                        ),
                        html.Div([
                            html.Label(
                                dcc.Markdown('Options for preliminar analysis')
                            ),
                            html.Br(),
                            dcc.Checklist( # CONSIDER REPLACING WITH RADIO ITEMS
                                ['Fit guess', 'Extremal points'],
                                [],
                                id = 'pre-options',
                                inline = True
                            )
                        ],
                        className = 'smol_r_pink'
                        ),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.Button(id='preprocess-button', children='Run')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-preprocessing', children = 'Run number 1')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'PROCESSING'),
                    html.Div([
                        html.Button(id='process-button', children='Process')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-processing', children = 'Processing number 1')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
                html.Div([
                # Text introduction
                dcc.Markdown("""
                    > Once generated a bunch of patterns with different filterings with the functions above, refresh the page *only once* before starting the analysis.
                """)
                ],
                className = 'box_pink')
            ],
            className = 'container_pink'
            ),

            # I should add ginput-like options to interact with the graph and extract data manually form it

            html.Div(children = [
                dcc.Graph(id = 'pattern-analysis', style={'width': '700px', 'height': '400px'}, mathjax = True),
                dcc.Graph(id = 'patt-preprocess', style={'width': '700px', 'height': '400px'}, mathjax = True),
            ],
            style = {'width': '1400px', 'height': '400px', 'display': 'flex', 'background-color': '#000000', 'padding-top': '10px', 'padding-right': '10px', 'padding-bottom': '10px', 'padding-left': '10px', 'margin-bottom': '10px'}
            ),

            html.Div(children = [
                    dcc.Markdown(id = 'patt-param', mathjax = True)
            ]),

            html.Div(children = [
                dcc.Graph(id = 'patt-prof', style={'width': '700px', 'height': '400px'}, mathjax = True),
                dcc.Graph(id = 'patt-norm', style={'width': '700px', 'height': '400px'}, mathjax = True),
            ],
            style = {'width': '1400px', 'height': '400px', 'display': 'flex', 'background-color': '#000000', 'padding-top': '10px', 'padding-right': '10px', 'padding-bottom': '10px', 'padding-left': '10px', 'margin-top': '10px'}
            ),

            html.Div(children = [
                    dcc.Markdown(id = 'visibility', mathjax = True)
            ]),

            html.Div([
                html.Div([
                dcc.Markdown("""
                    > The analysis consists of the calculation of the visibility of the interference patterns, which corresponds to the absolute value of the *field* 
                    correlation function of the speckle field (absolute value of the *complex degree of coherence*). In addition, the center of the pattern could be a 
                    local maximum, in which case the phase of the correlation function is +1, or a local minimum, in which case the phase is -1.
                """)
                ],
                className = 'inner_pink')
            ],
            className = 'container_pink'),

            html.Div(children = [
                html.Div(children = [
                    html.H3(children = 'ANALYZE ALL PATTERNS WITH THE SAME FILTERING AS SELECTED'),
                    html.Div([
                        # This buttons let the user start or stop the analysis (I did not yet add the callback so for the time being the buttons actually do nothing)
                        html.Button(id='part-three-one-button', children='Start analysis'), 
                        html.Button(id='cancel-three-one', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Counter and progress bar
                        html.P(id='counter-three-one', children = 'Analysis number 1'),
                        html.Progress(id='progress-bar-three-one')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'ANALYZE ALL PATTERNS WITH THE SAME SLIT SEPARATION AS SELECTED'),
                    html.Div([
                        # This buttons let the user start or stop the analysis (I did not yet add the callback so for the time being the buttons actually do nothing)
                        html.Button(id='part-three-two-button', children='Start analysis'), 
                        html.Button(id='cancel-three-two', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Counter and progress bar
                        html.P(id='counter-three-two', children = 'Analysis number 1'),
                        html.Progress(id='progress-bar-three-two')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
                html.Div(children = [
                    html.H3(children = 'GENERAL ANALYSIS'),
                    html.Div([
                        # This buttons let the user start or stop the analysis (I did not yet add the callback so for the time being the buttons actually do nothing)
                        html.Button(id='part-three-button', children='Start analysis'), 
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
            className = 'container_pink'
            ),
            html.Div(children = [
                dcc.Graph(id = 'graph-partial-an', style={'width': '1400px', 'height': '800px'}, mathjax = True),
            ],
            className = 'graph'
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
    Output('field-number-out', 'children'),
    Output('correlation-length-out', 'children'),
    Output('filter-width-out', 'children'),
    Output('slits-dist-out', 'children'),
    Input('field-number', 'value'),
    Input('correlation-length', 'value'),
    Input('filter-width', 'value'),
    Input('slits-dist', 'value'),
)
def update_values(a, b, c, d): 
    return ['Generating {} fields'.format(a)], ['Rough glass with correlation length {}'.format(b) + r'$\, \mu\mathrm{m}$'], ['Filter width between {} and {}'.format(c[0], c[1]) + r'$\, \mathrm{cm}^{-1}$'], ['Slit separation between {} and {}'.format(d[0], d[1]) + r'$\, \mathrm{mm}$']

@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter', 'children') # Only output is the counter
    ],
    inputs = [
        Input('part-one-button', 'n_clicks'), # The only input is the click of the 'start' button
        # The other parameters are passed as states, so changing them does not trigger the start of the simulation,
        State('field-number', 'value'),
        State('correlation-length', 'value'),
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
def generate_fields(set_progress, n_clicks, field_num, corr):
    if n_clicks is None:
        raise exceptions.PreventUpdate() # This is necessary in order for the simulation not to start automatically upon launching the app
    
    source_size = 0.5
    dist = 15
    scatt_num = 1000
    wavelen = 500
    avg_intensity = 0

    for i in range(field_num):
        field, screen = mod.generate_speckle_field(corr, source_size, dist, scatt_num, wavelen) # Generate a field
        avg_intensity += np.mean(np.abs(field).real ** 2)
        field_data = pd.DataFrame({
            'screen': screen, 
            'spec_re': field.real, 
            'spec_im': field.imag
        }) # Create a data frame
        field_data.to_csv('Speckles/speckle_num_{}.csv'.format(i)) # Store in csv
        set_progress((str(i + 1), str(field_num))) # Update progress bar

    with open('numbers.txt', 'w') as f:
        f.write(str(avg_intensity))

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
        State('slits-dist', 'value'),
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
def filter_and_interfere(set_progress, n_clicks, filter_type, filter_width_ext, slits_dist_ext):
    if n_clicks is None:
        raise exceptions.PreventUpdate()

    slit_width = 1
    dist_2 = 1e4
    wavelen = 500
    screen_size = 20 # [cm] 
    dx = 0.01 # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays

    filter_width_step = 2
    slits_dist_step = 0.5

    vect = os.listdir('Speckles')
    
    num = (filter_width_ext[1] + filter_width_step - filter_width_ext[0]) * (slits_dist_ext[1] + slits_dist_step - slits_dist_ext[0]) / (filter_width_step * slits_dist_step)
    counter = 1

    for filter_width in np.arange(filter_width_ext[0], filter_width_ext[1] + filter_width_step, filter_width_step):
        for slits_dist in np.arange(slits_dist_ext[0], slits_dist_ext[1] + slits_dist_step, slits_dist_step):

            pattern = np.zeros(dim) # Array containing the interference pattern

            for i in vect:
                field_data = pd.read_csv('Speckles/' + i) # Read the csv with the speckle field 
                field = field_data['spec_re'].to_numpy() + field_data['spec_im'].to_numpy() * 1j # Convert to ndarray
                screen = field_data['screen'].to_numpy() 
                filt_field = mod.filter(filter_type, field, filter_width) # Spatially filter the field

                # Add the pattern generated by the speckle field to the average
                pattern += mod.create_pattern(filt_field, dist_2, slits_dist, slit_width, screen, dim, wavelen) 

            pattern_data = pd.DataFrame({
                'screen': screen,
                'pattern': pattern,
                'filter_type': [filter_type for i in range(len(screen))],
                'filter_width': [filter_width for i in range(len(screen))],
                'slits_dist': [slits_dist for i in range(len(screen))]
            }) # Convert to data frame

            # fig = px.line(pattern_data.melt(id_vars = 'screen', value_vars = ['profile', 'pattern']), x = 'screen', y = 'value', title = 'Averaged interference pattern', line_group = 'variable', color = 'variable') 
            fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = 'Averaged interference pattern') # Create the figure of the graph
            pattern_data.to_csv('Patterns/Pattern_{}_{}.csv'.format(n_clicks, counter)) # Store the pattern to csv

            counter += 1
            set_progress((str(counter), str(num))) # Update progress bar

    return ['Simulation number {}'.format(n_clicks + 1)], fig # Return the number of clicks and the last pattern computed

@callback(
    # This is the callback for the plot of an individual pattern in the data analysis part. A long callback isn't necessary here
    Output('pattern-analysis', 'figure'), # Output a counter, the graph and the parameters of the pattern
    Output('counter-plot', 'children'),
    Output('patt-param', 'children'),
    Input('plot-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-pattern', 'value')
)
def plot_pattern(n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv
    fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = 'Interference pattern') # Create the figure

    return fig, ['Plot number {}'.format(n_clicks + 1)], ['Filter type: ' + pattern_data['filter_type'][0] + ', filter width: {}'.format(pattern_data['filter_width'][0]) + r'$\, \mathrm{cm}^{-1}$' + ', slit separation: {}'.format(pattern_data['slits_dist'][0]) + r'$\, \mathrm{mm}$']

@callback(
    # This is the callback for the plot of an individual pattern in the data analysis part. A long callback isn't necessary here
    Output('sample-speckle', 'figure'), # Output a counter, the graph and the parameters of the pattern
    Output('counter-field-plot', 'children'),
    Input('plot-field', 'n_clicks'), # Input the button click, other parameters are states
    State('select-field-plot', 'value')
)
def plot_field(n_clicks, field_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    field_data = pd.read_csv('Speckles/' + field_name) # Read the pattern from csv
    data_spec = pd.concat([field_data['screen'], (field_data['spec_re'] ** 2 + field_data['spec_im'] ** 2).rename('spec')], axis = 1)

    fig = px.line(data_spec, x = 'screen', y = 'spec', title = 'Speckle field') # Create the figure

    return fig, ['Plot number {}'.format(n_clicks + 1)],

@callback(
    # Callback for analysis of a single field
    Output('visibility', 'children'),
    Output('patt-prof', 'figure'),
    Output('patt-norm', 'figure'),
    Output('counter-processing', 'children'),
    Input('process-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-pattern', 'value')
)
def analyze(n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    slit_width = 1 # [mm]
    wavelen = 500 # [nm]
    dist_2 = 1e4 # [cm]

    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv

    patt_data_proc, vis_vect = mod.process_pattern(pattern_data, slit_width, wavelen, dist_2)
    
    fig_1 = px.line(patt_data_proc.melt(id_vars = 'screen', value_vars = ['pattern', 'prof_up', 'prof_down']), x = 'screen', y = 'value', title = 'Interference pattern', line_group = 'variable', color = 'variable')
    fig_2 = px.line(patt_data_proc, x = 'screen', y = 'patt_norm', title = 'Normalized interference pattern')

    return  ['Visibility = {}'.format(vis_vect[-1])], fig_1, fig_2, ['Processing number {}'.format(n_clicks + 1)]

@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter-three-one', 'children'), 
        Output('graph-partial-an', 'figure')
    ],
    inputs = [
        Input('part-three-one-button', 'n_clicks'), # The only input is the click of the 'start' button
        # The other parameters are passed as states, so changing them does not trigger the start of the simulation,
        State('select-pattern', 'value')
    ],
    running=[ # When the simulation is running,
        (Output('part-three-one-button', 'disabled'), True, False), # The start button is disabled
        (Output('cancel-three-one', 'disabled'), False, True), # And it is possible to cancel the operation
        (
            Output('counter-three-one', 'style'), # Show or hid the counter (visible when not running, hidden when running)
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-three-one', 'style'), # Show or hid the progress bar (hidden when not running, visible when running)
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-three-one', 'n_clicks')], # Link to cancel button id
    progress = [Output('progress-bar-three-one', 'value'), Output('progress-bar-three-one', 'max')], # Link to progress bar id
    manager = long_callback_manager
)
def analyze_one(set_progress, n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()

    pattern_data = pd.read_csv('Patterns/' + patt_name) 
    filter_width = pattern_data['filter_width'][0]

    vect = os.listdir('Patterns')
    num = len(vect)

    visib = []
    slits_dist = []
    
    counter = 1
    for i in vect:
        data_temp = pd.read_csv('Patterns/' + i)
        if data_temp['filter_width'][0] == filter_width:
            slits_dist.append(data_temp['slits_dist'][0])
            patt_data_norm, vis = mod.process_pattern(data_temp)
            visib.append(vis)

        set_progress((str(counter), str(num)))
                     
    data = pd.DataFrame({
        'slits_dist': slits_dist,
        'vis': visib
    })
    
    fig = px.scatter(data, x = 'slits_dist', y = 'vis')

    return 'Analysis number {}'.format(n_clicks + 1), fig



@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter-three-two', 'children') # Only output is the counter
    ],
    inputs = [
        Input('part-three-two-button', 'n_clicks'), # The only input is the click of the 'start' button
        # The other parameters are passed as states, so changing them does not trigger the start of the simulation,
        State('select-pattern', 'value')
    ],
    running=[ # When the simulation is running,
        (Output('part-three-two-button', 'disabled'), True, False), # The start button is disabled
        (Output('cancel-three-two', 'disabled'), False, True), # And it is possible to cancel the operation
        (
            Output('counter-three-two', 'style'), # Show or hid the counter (visible when not running, hidden when running)
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-three-two', 'style'), # Show or hid the progress bar (hidden when not running, visible when running)
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-three-two', 'n_clicks')], # Link to cancel button id
    progress = [Output('progress-bar-three-two', 'value'), Output('progress-bar-three-two', 'max')], # Link to progress bar id
    manager = long_callback_manager
)
def analyze_two(set_progress, n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()

    pattern_data = pd.read_csv('Patterns/' + patt_name) 
    slits_dist = pattern_data['slits_dist'][0]

    pattern_fix_filt = pd.DataFrame({
        'screen': pattern_data['screen']
    })

    vect = os.listdir('Patterns')
    num = len(vect)

    visib = []
    filter_width = []
    
    counter = 1
    for i in vect:
        data_temp = pd.read_csv('Patterns/' + i)
        if data_temp['slits_dist'][0] == slits_dist:
            filter_width.append(data_temp['filter_width'][0])
            patt_data_norm, vis = mod.process_pattern(data_temp)
            visib.append(vis)

        set_progress((str(counter), str(num)))
                     
    data = pd.DataFrame({
        'fiter_width': filter_width,
        'vis': visib
    })
    
    fig = px.line(data, x = 'slits_dist', y = 'vis')

    return 'Analysis number {}'.format(n_clicks + 1), fig

@callback( # Callback for the preliminary analysis
    Output('patt-preprocess', 'figure'),
    Output('counter-preprocessing', 'children'),
    Input('preprocess-button', 'n_clicks'),
    State('pre-options', 'value'),
    State('fit-guess', 'value'),
    State('select-pattern', 'value')
)
def pre_process(n_clicks, options, guess, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    # CONSIDER WRITING ANOTHER FUNCTION IN THE MODULE IN ORDER TO DO ALL THIS

    slit_width = 1 # [mm]
    wavelen = 500 # [nm]
    dist_2 = 1e4 # [cm]

    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv

    fig_data = mod.pre_process(pattern_data, slit_width, wavelen, dist_2, options, guess)

    fig = go.Figure(data = fig_data)

    return fig, 'Run number {}'.format(n_clicks + 1)


if __name__ == '__main__':
    app.run(debug=True)