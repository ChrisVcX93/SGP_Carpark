import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import assign

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


colorscale = ['red', 'yellow', 'green']  # rainbow
color_prop = 'density'

# Create a colorbar.
vmax = 20
colorbar = dl.Colorbar(colorscale=colorscale, width=20, height=150, min=0, max=vmax, unit='lots')
# Geojson rendering logic, must be JavaScript as it is executed in clientside.
# Geojson rendering logic, must be JavaScript as it is executed in clientside.
point_to_layer = assign("""function(feature, latlng, context){
    const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
    circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
    return L.circleMarker(latlng, circleOptions);  // sender a simple circle marker.
}""")
# Create geojson.
geojson = dl.GeoJSON(data=None, id="geojson", format="geobuf",
                     zoomToBounds=True,  # when true, zooms to bounds when data changes
                     options=dict(pointToLayer=point_to_layer),  # how to draw points
                     superClusterOptions=dict(radius=50),   # adjust cluster size
                     hideout=dict(colorProp=color_prop, circleOptions=dict(fillOpacity=1, stroke=False, radius=7),
                                  min=0, max=vmax, colorscale=colorscale))

layout1 = html.Div(
    [html.H1("Wheregot Carpark nearby ah?"),
     html.Div([
         dl.Map([dl.TileLayer(),
                 geojson, colorbar, dl.LocateControl(options={'locateOptions': {'enableHighAccuracy': True }})
                 ],
                id="map", style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block",
                                 "position": "relative"}),
         html.Div(id="text"),
         html.Div([
             dcc.Store(id="lat_lon2"),
             dcc.Store(id="lat_lon"),
             dcc.Store(id="x_y2"),
             dcc.Store(id="x_y"),
             dcc.Store(id="ranged"),
            html.P("Please select range"),
             dcc.Slider(500, 2000, step=None,
                        marks={
                                500: '500m',
                                1000: '1km',
                                1500: '1.5km',
                                2000: '2km',
                            },
                        value=500,
                        id='my-slider'
                        )])
     ])
     ])
