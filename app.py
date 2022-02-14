import dash
import dash_bootstrap_components as dbc
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # js lib used for colors

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_scripts=[chroma], external_stylesheets=['https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css',dbc.themes.LITERA])
server = app.server