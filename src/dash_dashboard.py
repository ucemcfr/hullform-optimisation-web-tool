import pymongo
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import plotly.offline as pyo

app = dash.Dash()

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
collection = client['casebase'] # what should the database be called

cursor = collection['previous_designs'].find()

df = pd.DataFrame(list(cursor))

print(df)

app.layout = html.Div([dcc.Graph(id='scatter1',
                                 figure={'data': [
                                     go.Scatter(
                                         x=df['lwl'],
                                         y=df['loa'],
                                         mode='markers'
                                     )
                                 ],
                                     'layout': go.Layout(title='First scatter')
                                 })])

if __name__ == '__main__':
    app.run_server()
