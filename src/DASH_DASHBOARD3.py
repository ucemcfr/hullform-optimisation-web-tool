import pymongo
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import json
from pprint import pprint
from src.models.optimisation import deap_evolve, deap_save
import time

app = dash.Dash(__name__)

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
collection = client['casebase']  # what should the database be called

cursor = collection['previous_designs'].find()

df = pd.DataFrame(list(cursor))
df.drop('_id', axis=1, inplace=True)

features = df.columns

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H5('LWL (m)',
                    style={'text-align': 'center'}
                    ),
            dcc.RangeSlider(
                id='lwl-range',
                min=min(df['lwl']),
                max=max(df['lwl']),
                marks={i: '{}'.format(i) for i in range(int(min(df['lwl'])), int(max(df['lwl'])))},
                step=0.1,
                value=[int(min(df['lwl'])), int(max(df['lwl']))]
                # TODO check this is giving the correct values for the marks. Why is the max not showing a mark?
            )], style={'width': '18%', 'display': 'inline-block', 'padding': '1%'}
        ),
        html.Div([
            html.H5('LOA (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='loa-range',
                min=min(df['loa']),
                max=max(df['loa']),
                marks={i: '{}'.format(i) for i in range(int(min(df['loa'])), int(max(df['loa'])))},
                step=0.1,
                value=[int(min(df['loa'])), int(max(df['loa']))]
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '1%'}
        ),
        html.Div([
            html.H5('BWL (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='bwl-range',
                min=min(df['bwl']),
                max=max(df['bwl']),
                marks={i: '{}'.format(i) for i in range(int(min(df['bwl'])), int(max(df['bwl'])))},
                step=0.1,
                value=[int(min(df['bwl'])), int(max(df['bwl']))]
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '1%'}
        ),
        html.Div([
            html.H5('BOA (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='boa-range',
                min=min(df['boa']),
                max=max(df['boa']),
                marks={i: '{}'.format(i) for i in range(int(min(df['boa'])), int(max(df['boa'])))},
                step=0.1,
                value=[int(min(df['boa'])), int(max(df['boa']))]
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '1%'}
        ),
        html.Div([
            html.H5('Draft (m)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='draft-range',
                min=min(df['draft']),
                max=max(df['draft']),
                marks={i: '{}'.format(i) for i in range(int(min(df['draft'])), int(max(df['draft'])))},
                step=0.1,
                value=[int(min(df['draft'])), int(max(df['draft']))]
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '1%'}
        )]),
    html.Div([
        # In here put the operational things: speed, displacement, etc.
        html.Div([
            html.H5('Design speed (kts)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='velocity-range',
                min=min(df['velocity']),
                max=max(df['velocity']),
                marks={i: '{}'.format(i) for i in range(int(min(df['velocity'])), int(max(df['velocity'])), 1)},
                step=0.1,
                value=[int(min(df['velocity'])), int(max(df['velocity']))]
            )
        ], style={'width': '25%', 'display': 'inline-block', 'padding': '1%'}
        ),
        html.Div([
            html.H5('Volumetric displacement (m^3)',
                    style={'text-align': 'center'}),
            dcc.RangeSlider(
                id='vol-disp-range',
                min=min(df['vol_disp']),
                max=max(df['vol_disp']),
                marks={i: '{}'.format(i) for i in range(int(min(df['vol_disp'])), int(max(df['vol_disp'])),
                                                        int((max(df['vol_disp']) - min(df['vol_disp'])) / 10)
                                                        )
                       },
                step=100,
                value=[int(min(df['vol_disp'])), int(max(df['vol_disp']))]
            )
        ], style={'width': '25%', 'display': 'inline-block', 'padding': '1%'}
        )
    ]),

    html.Div([
        dcc.Graph(id='casebase-parallel-coords')
    ]),
    html.Div([
        dcc.Dropdown(id='xaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='lwl')
    ], style={'width': '15%', 'display': 'inline-block', 'padding': 5}),
    html.Div([
        dcc.Dropdown(id='yaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='loa')
    ], style={'width': '15%', 'display': 'inline-block', 'padding': 5}),
    html.Div([
        dcc.Graph(id='casebase-scatter')
    ]),
    html.Div([
        html.Div(dcc.Input(), style={'display': 'none'}),
        dash_table.DataTable(
            id='datatable1',
            columns=[
                {'name': i, 'id': i, 'deletable': True} for i in df.columns
            ],
            data=df.to_dict('rows'),
            editable=True,
            filtering=True,
            sorting=True,
            sorting_type="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_rows=[],
        )
    ]),
    html.Div([
        html.Pre(id='selected-ships')
    ]),
    html.Div([
        html.Button(id='optimise-button')
    ]),
    html.Div([
        dcc.Graph(id='optimisation-results')
    ])
])


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
    [Input('lwl-range', 'value'),
     Input('loa-range', 'value'),
     Input('boa-range', 'value'),
     Input('bwl-range', 'value'),
     Input('draft-range', 'value'),
     Input('velocity-range', 'value'),
     Input('vol-disp-range', 'value')
     ]
)
def update_parcoords(lwl_range, loa_range, boa_range, bwl_range, draft_range, velocity_range,
                     disp_range):
    dff = df[(df['loa'] > loa_range[0]) & (df['loa'] < loa_range[1]) &
             (df['lwl'] > lwl_range[0]) & (df['lwl'] < lwl_range[1]) &
             (df['boa'] > boa_range[0]) & (df['boa'] < boa_range[1]) &
             (df['bwl'] > bwl_range[0]) & (df['bwl'] < bwl_range[1]) &
             (df['draft'] > draft_range[0]) & (df['draft'] < draft_range[1]) &
             (df['velocity'] > velocity_range[0]) & (df['velocity'] < velocity_range[1]) &
             (df['vol_disp'] > disp_range[0]) & (df['vol_disp'] < disp_range[1])
             ]

    return {'data': [go.Parcoords(
        dimensions=
        [
            dict(label='LWL', values=dff['lwl']),
            dict(label='LOA', values=dff['loa']),
            dict(label='BWL', values=dff['bwl']),
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
    pprint(rows)
    # TODO this is currently changin the stored data when the row indices change. so if the data is filtered so less rows are shown then this will change the values from the already saved rows
    return dff.iloc[selected_rows].to_json()


@app.callback(
    Output('optimisation-results', 'figure'),
    [Input('datatable1', 'derived_virtual_data'),
     Input('datatable1', 'selected_rows'),
     Input('optimise-button', 'n_clicks')]
)
def optimise_selected(rows, selected_rows, n_clicks):
    #TODO currently this needs to be changed to loop through all ships in the json (or does min just take the minimum value for each?) and it needs an if statement so it only happens when n_clicks is greater than 0
    if n_clicks is not None:
        ships = pd.DataFrame(rows)
        loB = min(ships['bwl']) * 0.9
        loLWL = min(ships['lwl']) * 0.9
        loT = min(ships['draft']) * 0.9
        loVolDisp = min(ships['vol_disp']) * 0.9
        loCwp = min(ships['c_wp']) * 0.9
        hiLWL = max(ships['lwl']) * 1.1
        hiB = max(ships['bwl']) * 1.1
        hiT = max(ships['draft']) * 1.1
        hiVolDisp = max(ships['vol_disp']) * 1.1
        hiCwp = max(ships['c_wp']) * 1.1
        popsize = 100
        maxgen = 10

        record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(
            loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize, maxgen)
        deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs)

        time.sleep(2)

    return {'data': [go.Scatter(x=resFitAll,
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


if __name__ == '__main__':
    app.run_server(debug=True)
