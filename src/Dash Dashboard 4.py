import pymongo
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from plotly.plotly import plotly as pltly
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, Event
import math
from pprint import pprint
from src.models.optimisation import deap_evolve
from collections import deque

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
collection = client['casebase']  # what should the database be called

cursor = collection['previous_designs'].find()

df = pd.DataFrame(list(cursor))
df.drop('_id', axis=1, inplace=True)

df = df.round(3)

features = df.columns

convergence_gens = deque()
convergence_accel = deque()
convergence_res = deque()  # TODO are these needed or should I just use CSV

app.layout = html.Div([
    html.H2('Step 1: filter & explore design database', style={'margin-left': '35%'}),
    html.Div([
        html.Div([
            html.H5('LWL (m)',
                    style={'text-align': 'center'}
                    ),
            dcc.RangeSlider(
                id='lwl-range',
                min=math.floor(min(df['lwl'])),
                max=math.ceil(max(df['lwl'])) + 1,
                marks={i: '{}'.format(i) for i in range(math.floor(min(df['lwl'])), math.ceil(max(df['lwl'])) + 1, 5)},
                value=[math.floor(min(df['lwl'])), math.ceil(max(df['lwl'])) + 1]
            )
        ], style={'width': '12%', 'display': 'inline-block', 'padding': 5, 'margin-left': '4%'}
        ),
        html.Div([
            html.H5('LOA (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='loa-range',
                min=math.floor(min(df['loa'])),
                max=math.ceil(max(df['loa'])) + 1,
                marks={i: '{}'.format(i) for i in range(math.floor(min(df['loa'])), math.ceil(max(df['loa'])) + 1, 5)},
                value=[math.floor(min(df['loa'])), math.ceil(max(df['loa'])) + 1]
            )
        ], style={'width': '12%', 'display': 'inline-block', 'padding': 5, 'margin-left': '4%'}
        ),
        html.Div([
            html.H5('BWL (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='bwl-range',
                min=math.floor(min(df['bwl'])),
                max=math.ceil(max(df['bwl'])) + 1,
                marks={i: '{}'.format(i) for i in range(math.floor(min(df['bwl'])), math.ceil(max(df['bwl'])) + 1, 1)},
                value=[math.floor(min(df['bwl'])), math.ceil(max(df['bwl'])) + 1]
            )
        ], style={'width': '12%', 'display': 'inline-block', 'padding': 5, 'margin-left': '4%'}
        ),
        html.Div([
            html.H5('BOA (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='boa-range',
                min=math.floor(min(df['boa'])),
                max=math.ceil(max(df['boa'])) + 1,
                marks={i: '{}'.format(i) for i in range(math.floor(min(df['boa'])), math.ceil(max(df['boa'])) + 1, 1)},
                value=[math.floor(min(df['boa'])), math.ceil(max(df['boa'])) + 1]
            )
        ], style={'width': '12%', 'display': 'inline-block', 'padding': 5, 'margin-left': '4%'}
        ),
        html.Div([
            html.H5('Draft (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='draft-range',
                min=math.floor(min(df['draft'])),
                max=math.ceil(max(df['draft'])) + 1,
                marks={i: '{}'.format(i) for i in
                       range(math.floor(min(df['draft'])), math.ceil(max(df['draft'])) + 1, 1)},
                value=[math.floor(min(df['draft'])), math.ceil(max(df['draft'])) + 1]
            )
        ], style={'width': '12%', 'display': 'inline-block', 'padding': 5, 'margin-left': '4%'}
        )]),
    html.Div([
        # In here put the operational things: speed, displacement, etc.
        html.Div([
            html.H5('Design speed (kts)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='velocity-range',
                min=math.floor(min(df['velocity'])),
                max=math.ceil(max(df['velocity'])) + 1,
                marks={i: '{}'.format(i) for i in
                       range(math.floor(min(df['velocity'])), math.ceil(max(df['velocity'])) + 1, 1)},
                value=[math.floor(min(df['velocity'])), math.ceil(max(df['velocity'])) + 1]
            )
        ], style={'width': '25%', 'display': 'inline-block', 'margin-left': '10%', 'padding': 30}
        ),
        html.Div([
            html.H5('Volumetric displacement (m^3)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='vol-disp-range',
                min=math.floor(min(df['vol_disp'])),
                max=math.ceil(max(df['vol_disp'])) + 1,
                marks={i: '{}'.format(i) for i in
                       range(math.floor(min(df['vol_disp'])), math.ceil(max(df['vol_disp'])) + 1, 1000)},
                value=[math.floor(min(df['vol_disp'])), math.ceil(max(df['vol_disp'])) + 1]
            )
        ], style={'width': '25%', 'display': 'inline-block', 'margin-left': '10%', 'padding': 30}
        )
    ]),

    html.Div([
        dcc.Graph(id='casebase-parallel-coords', style={'width': '80%', 'margin-left': '10%'})
    ]),
    html.Div([
        dcc.Dropdown(id='xaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='max_vert_acceleration')
    ], style={'width': '15%', 'display': 'inline-block', 'padding': 5, 'margin-left': '25%'}),
    html.Div([
        dcc.Dropdown(id='yaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='total_resistance')
    ], style={'width': '15%', 'display': 'inline-block', 'padding': 5}),
    html.Div([
        dcc.Graph(id='casebase-scatter', style={'width': '70%', 'height': '800px', 'margin-left': '15%'})
    ]),
    html.Div([
        html.H2('Step 2: select basis ship', style={'margin-left': '40%', 'padding': 30}),
        html.Div(dcc.Input(), style={'display': 'none'}),
        dash_table.DataTable(
            id='datatable1',
            columns=[
                {'name': i, 'id': i, 'deletable': False} for i in df.columns
            ],
            data=df.to_dict('rows'),
            editable=False,
            filtering=False,
            sorting=True,
            sorting_type="multi",
            row_selectable="single",
            row_deletable=False,
            selected_rows=[],
            style_table={
                'maxHeight': '300',
                'overflowY': 'scroll',
                'width': '90%',
                'margin-left': '5%'
            }
        )
    ]),
    html.Div([
        html.Pre(id='selected-ships', style={'display': 'none'})
    ]),
    html.Div(html.H2('Step 3: enter design speed, LCG and displacement for optimisation',
                     style={'margin-left': '25%', 'padding': 30})),
    html.Div([
        dcc.Input(id='optimisation-speed', type='number', placeholder='Speed (kts)',
                  style={'padding': 10, 'margin-left': '20%'}),
        dcc.Input(id='optimisation-lcg', type='number', placeholder='LCG as % LWL aft of midships',
                  style={'padding': 10, 'margin-left': '10%'}),
        dcc.Input(id='optimisation-displacement', type='number', placeholder='Volumetric disp. (cubic m)',
                  style={'padding': 10, 'margin-left': '10%'})
    ]),
    html.Div([
        html.Button('Optimise selected ship', id='optimise-button')
    ], style={'margin-left': '40%', 'padding': 20}),
    html.Div([
        dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1 * 1000  # milliseconds
            # n_intervals=0
        ),
    ]),
    html.Div([
        dcc.Graph(id='optimisation-results')

    ])
])


# features = df.columns


@app.callback(
    Output('casebase-scatter', 'figure'),
    [Input('xaxis', 'value'),
     Input('yaxis', 'value'),
     Input('lwl-range', 'value'),
     Input('loa-range', 'value'),
     Input('boa-range', 'value'),
     Input('bwl-range', 'value'),
     Input('draft-range', 'value'),
     Input('velocity-range', 'value'),
     Input('vol-disp-range', 'value')
     ]
)
def update_scatter(xaxis_name, yaxis_name, lwl_range, loa_range, boa_range, bwl_range, draft_range, velocity_range,
                   disp_range):
    dff = df[(df['loa'] > loa_range[0]) & (df['loa'] < loa_range[1]) &
             (df['lwl'] > lwl_range[0]) & (df['lwl'] < lwl_range[1]) &
             (df['boa'] > boa_range[0]) & (df['boa'] < boa_range[1]) &
             (df['bwl'] > bwl_range[0]) & (df['bwl'] < bwl_range[1]) &
             (df['draft'] > draft_range[0]) & (df['draft'] < draft_range[1]) &
             (df['velocity'] > velocity_range[0]) & (df['velocity'] < velocity_range[1]) &
             (df['vol_disp'] > disp_range[0]) & (df['vol_disp'] < disp_range[1])
             ]
    return {'data': [go.Scatter(x=dff[xaxis_name],
                                y=dff[yaxis_name],
                                mode='markers',
                                marker={'size': 15}
                                )
                     ],
            'layout': go.Layout(title='First ship database viz',
                                xaxis={'title': xaxis_name},
                                yaxis={'title': yaxis_name}
                                )
            }


@app.callback(
    Output('casebase-parallel-coords', 'figure'),
    [  # Input('lwl-range', 'value'),
        Input('loa-range', 'value'),
        Input('boa-range', 'value'),
        # Input('bwl-range', 'value'),
        Input('draft-range', 'value'),
        Input('velocity-range', 'value'),
        Input('vol-disp-range', 'value')
    ]
)
def update_parcoords(loa_range, boa_range, draft_range, velocity_range,
                     disp_range):
    dff = df[(df['loa'] > loa_range[0]) & (df['loa'] < loa_range[1]) &
             # (df['lwl'] > lwl_range[0]) & (df['lwl'] < lwl_range[1]) &
             (df['boa'] > boa_range[0]) & (df['boa'] < boa_range[1]) &
             # (df['bwl'] > bwl_range[0]) & (df['bwl'] < bwl_range[1]) &
             (df['draft'] > draft_range[0]) & (df['draft'] < draft_range[1]) &
             (df['velocity'] > velocity_range[0]) & (df['velocity'] < velocity_range[1]) &
             (df['vol_disp'] > disp_range[0]) & (df['vol_disp'] < disp_range[1])
             ]

    return {'data': [go.Parcoords(
        dimensions=
        [
            # dict(label='LWL', values=dff['lwl']),
            dict(label='LOA', values=dff['loa']),
            # dict(label='BWL', values=dff['bwl']),
            dict(label='BOA', values=dff['boa']),
            dict(label='Draft', values=dff['draft']),
            dict(label='Vol. displacement', values=dff['vol_disp']),
            dict(label='Resistance', values=dff['total_resistance'])
        ]
    )]}


@app.callback(
    Output('datatable1', 'data'),
    [Input('lwl-range', 'value'),
     Input('loa-range', 'value'),
     Input('boa-range', 'value'),
     Input('bwl-range', 'value'),
     Input('draft-range', 'value'),
     Input('velocity-range', 'value'),
     Input('vol-disp-range', 'value')
     ]
)
def update_table(lwl_range, loa_range, boa_range, bwl_range, draft_range, velocity_range,
                 disp_range):
    dff = df[(df['loa'] > loa_range[0]) & (df['loa'] < loa_range[1]) &
             (df['lwl'] > lwl_range[0]) & (df['lwl'] < lwl_range[1]) &
             (df['boa'] > boa_range[0]) & (df['boa'] < boa_range[1]) &
             (df['bwl'] > bwl_range[0]) & (df['bwl'] < bwl_range[1]) &
             (df['draft'] > draft_range[0]) & (df['draft'] < draft_range[1]) &
             (df['velocity'] > velocity_range[0]) & (df['velocity'] < velocity_range[1]) &
             (df['vol_disp'] > disp_range[0]) & (df['vol_disp'] < disp_range[1])
             ]
    return dff.to_dict('rows')


@app.callback(
    Output('selected-ships', 'children'),
    [Input('datatable1', 'derived_virtual_data'),
     Input('datatable1', 'selected_rows')]
)
def selected_table_data(rows, selected_rows):
    if rows is None:
        dff = df
    else:
        dff = pd.DataFrame(rows)

    pprint(selected_rows)
    # pprint(rows)
    # TODO this is currently changin the stored data when the row indices change. so if the data is filtered so less rows are shown then this will change the values from the already saved rows
    return dff.iloc[selected_rows].to_json()


@app.callback(
    Output('optimisation-results', 'figure'),
    [Input('datatable1', 'derived_virtual_data'),
     Input('datatable1', 'selected_rows'),
     Input('optimise-button', 'n_clicks')],
    [State('optimisation-speed', 'value'),
     State('optimisation-lcg', 'value'),
     State('optimisation-displacement', 'value')]
)
def optimise_selected(rows, selected_rows, n_clicks, V, LCB, vol_disp):
    # TODO currently this needs to be changed to loop through all ships in the json (or does min just take the minimum value for each?) and it needs an if statement so it only happens when n_clicks is greater than 0

    if n_clicks is not None:
        print('optimisation triggered')
        ships = pd.DataFrame(rows).iloc[selected_rows]
        loB = min(ships['bwl']) * 0.9
        loLWL = min(ships['lwl']) * 0.9
        loT = min(ships['draft']) * 0.9
        loVolDisp = vol_disp * 0.9
        loCwp = min(ships['c_wp']) * 0.9
        hiLWL = max(ships['lwl']) * 1.1
        hiB = max(ships['bwl']) * 1.1
        hiT = max(ships['draft']) * 1.1
        hiVolDisp = vol_disp * 1.1
        hiCwp = max(ships['c_wp']) * 1.1
        popsize = 100
        maxgen = 50
        V = V
        LCB = LCB

        record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(
            loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, LCB, V, popsize, maxgen)

        # deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs)

        # print(record)
        # time.sleep(2)
        fig = {'data': [go.Scatter(x=resFitAll,
                                   y=stabFitAll,
                                   # customdata=([df['_id']]),
                                   # text=df['_id'],
                                   mode='markers',
                                   marker={'size': 15}
                                   )
                        ],
               'layout': go.Layout(title='Optimisation results Pareto plot',
                                   xaxis={'title': 'Resistance'},
                                   yaxis={'title': 'Maximum vertical acceleration'}
                                   )
               }

    return fig


@app.callback(
    Output('live-graph', 'figure'),
    events=[Event('graph-update', 'interval')])
def convergence_plot():
    df = pd.read_csv('../src/static/data/convergence.csv')
    avg_res = list(df['min_res'])
    avg_accel = list(df['min_accel'])
    gen = list(df['gen'])


    # print(min_res)
    # print(min_accel)

    fig = pltly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2, print_grid=False)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    fig['layout']['xaxis'] = {'range': [0, max(gen)]}

    fig.append_trace({
        'x': gen,
        'y': avg_res,
        'name': 'Minimum resistance',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)

    fig.append_trace({
        'x': gen,
        'y': avg_accel,
        'name': 'Minimum acceleration',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 2, 1)


    return fig  # {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
#                                     yaxis=dict(range=[min(Y), max(Y)]), )}

if __name__ == '__main__':
    app.run_server(debug=True)
