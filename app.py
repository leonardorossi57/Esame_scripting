import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children = 'Grafico di una Gaussiana con parametri regolabili'),


    html.Div(children = 'Centro della distribuzione e deviazione standard'),
    dcc.Input(value = '0', type = 'text', id = 'dist-center'),
    dcc.Input(value = '1', type = 'text', id = 'std-dev'),
    dcc.Slider(min = 0, max = 10),

    html.Button(id='submit-button-state', n_clicks = 0, children='Invio'),

    dcc.Graph(id = 'gauss-function-plot', mathjax = True),
    html.Div(id = 'counter')
])

@callback(
    Output('gauss-function-plot', 'figure'),
    Output('counter', 'children'),
    Input('submit-button-state', 'n_clicks'),
    State('dist-center', 'value'),
    State('std-dev', 'value')
)
def plot_a_gaussian_function(n_clicks, mu = 0, sigma = 1):

    mu = float(mu)
    sigma = float(sigma)

    x = np.linspace(-100, 100, 1000)
    y = 1/(np.sqrt(2 * np.pi) * sigma) * np.exp(-(x - mu) ** 2 / (2 * sigma ** 2))

    data = pd.DataFrame({
        'x_data': x,
        'y_data': y
    })

    my_string = r'$\mu = {}, \, \sigma = {}$'.format(mu, sigma)
    fig = px.line(data, x = 'x_data', y = 'y_data', title = my_string)
    
    return fig, n_clicks


if __name__ == '__main__':
    app.run(debug=True)