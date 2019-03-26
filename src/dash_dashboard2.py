import time

import pymongo
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import json
from textwrap import dedent as d
from src.models.optimisation import deap_evolve, deap_save

app = dash.Dash()

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
collection = client['casebase']  # what should the database be called

cursor = collection['previous_designs'].find()

df = pd.DataFrame(list(cursor))

print(df['id'])

features = df.columns

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app.layout = html.Div([
    html.Div([
        dcc.Dropdown(id='xaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='lwl')
    ], style={'width': '48%', 'display': 'inline-block'}),
    html.Div([
        dcc.Dropdown(id='yaxis',
                     options=[{'label': i, 'value': i} for i in features],
                     value='loa')
    ], style={'width': '48%', 'display': 'inline-block'}),



    dcc.Graph(id='feature-graphic'),
    html.Div([
        dcc.Graph(id='optimisation-results')
    ])
], style={'padding': 10})


@app.callback(Output('feature-graphic', 'figure'),
              [Input('xaxis', 'value'),
               Input('yaxis', 'value')
               ]
              )
def update_graph(xaxis_name, yaxis_name):
    return {'data': [go.Scatter(x=df[xaxis_name],
                                y=df[yaxis_name],
                                #customdata=([df['_id']]),
                                #text=df['_id'],
                                mode='markers',
                                marker={'size': 15}
                                )
                     ],
            'layout': go.Layout(title='First ship database viz',
                                xaxis={'title': xaxis_name},
                                yaxis={'title': yaxis_name}
                                )
            }


# TODO add interaction on clicked datapoint https://community.plot.ly/t/solution-persistent-click-events/6590 and
# https://dash.plot.ly/interactive-graphing
# TODO see https://dash.plot.ly/sharing-data-between-callbacks for how to save data from click event

@app.callback(
    Output('optimisation-results', 'figure'),
    [Input('feature-graphic', 'clickData')])
def display_click_data(clickData):
    if clickData is not None:
        print('clicked')
        clicked_data = clickData['points']
        clicked_index = clicked_data[0]['pointIndex']
        id_number = df['_id'][clicked_index] # TODO check this is accessing the correct ID, this all got a bit strange and confusing. Anyway this isn't even neede! just used clicked index to look up value in the dataframe.
        print(id_number)
        loLWL = df['lwl'][clicked_index]*0.9
        loB = df['bwl'][clicked_index]*0.9
        loT = df['draft'][clicked_index]*0.9
        loVolDisp = df['vol_disp'][clicked_index]*0.9
        loCwp = df['c_wp'][clicked_index]*0.9
        hiLWL = df['lwl'][clicked_index]*1.1
        hiB = df['bwl'][clicked_index]*1.1
        hiT = df['draft'][clicked_index]*1.1
        hiVolDisp = df['vol_disp'][clicked_index]*1.1
        hiCwp = df['c_wp'][clicked_index]
        popsize = 100
        maxgen = 10
        #
        record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize, maxgen)
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
    app.run_server()
