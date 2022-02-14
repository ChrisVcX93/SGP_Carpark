from app import app
import pandas as pd
import dash
import dash_table as dt
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import requests
import json
import dash_leaflet as dl
import dash_leaflet.express as dlx
from pyspark.sql import SparkSession
from pyspark.sql.functions import concat, concat_ws, when, lit, sum, split
from pyspark import SparkConf, SparkContext
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DoubleType, LongType
from pyspark.sql.functions import to_date, col, date_format, year, month, dayofmonth, array
import geocoder

spark = SparkSession.builder.master("local").appName("Sg_carpark").getOrCreate()


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    return text


# Get carpark slots available
# Carpark API input need be in 2022-02-05T06:22:51.593Z format
parameters = {"date_time": "2022-02-05T06:22:51.593Z"}
response = requests.get("https://api.data.gov.sg/v1/transport/carpark-availability", params=parameters)

print(f"car park real time {response}")
# print(jprint(response.json()))
x = response.json()['items'][0]['carpark_data']
df1 = spark.createDataFrame(x)
df1.printSchema()
# split columns into 3 as carpark_info is a dictionary
df1 = df1.withColumn("lots available", df1["carpark_info"][0]["lots_available"]).withColumn("total lots",
                                                                                            df1["carpark_info"][0][
                                                                                                "total_lots"]).withColumn(
    "lot type", df1["carpark_info"][0]["lot_type"])
# df1 = df1.sort(df1["lots available"], ascending=True)
# set color code to density based on the lots available
# density column created based on lots available , keep values as it if < 20 and more than or equal to 20 label as 20
df1 = df1.withColumn("density", when(
    (20 > df1["lots available"]), lit(df1["lots available"])).when((20 <= df1["lots available"]), lit(20)))
df1 = df1.withColumn("density", col("density").cast(LongType()))
df1.show(100)
# example = df1.select("carpark_info").collect()[0][0]
# print(example)

# get Information about HDB carparks such as operating hours, car park location (in SVY21), type of parking system, etc.
# then filter nearest XX km based on user current location
# then merge to carpark available table ?
parameters2 = {"resource_id": "139a3035-e624-4f56-b63f-89ae28d4ae4c",
               "limit": "2000"}
response = requests.get("https://data.gov.sg/api/action/datastore_search", params=parameters2)
print(f"car park area {response}")
y = response.json()["result"]["records"]
df2 = spark.createDataFrame(y)
df2 = df2.withColumn("x_coord", col("x_coord").cast(DoubleType())).withColumn("y_coord",
                                                                              col("y_coord").cast(DoubleType()))
df2.printSchema()

# just check location based on leaflet
# save it
@app.callback(
    Output("lat_lon2", "data"),
    Input("map", "location_lat_lon_acc"))
def current_location(location):
    if location is None:
        raise dash.exceptions.PreventUpdate
    print(location[0], location[1])
    return [location[0], location[1]]


# to out put lat and long in 3414(SVY21) format (X AND Y coordinates)
# SVY21 is in meters and used in singapore , its  a type of coordinates system fyi
@app.callback(
    Output("x_y2", "data"),
    Input("lat_lon2", "data"))
def current_location_xy(data):
    if not data:
        return None
    parameters3 = {
        "latitude": data[0],
        "longitude": data[1]
    }

    response3 = requests.get("https://developers.onemap.sg/commonapi/convert/4326to3414", params=parameters3)
    print(response3)
    x = response3.json()["X"]
    y = response3.json()["Y"]
    print(f"leaftlet of x is {x} and y is {y}")
    return x, y



# output slider value , default is 500
# save it
@app.callback(
    Output("ranged", "data"),
    Input("my-slider", "value"))
def current_location(value):
    print(f"slider is at {value}")
    # for default 500 value
    return value

# default check carparks across 500m radius first
@app.callback(
    Output("geojson", "data"),
    Input("ranged", "data"),
    Input("x_y2", "data")
    )
def fivehundren(data2, data3):
    print(data2, data3)
    if data3 is None:
        raise dash.exceptions.PreventUpdate
    else:
        # df2f is filtered version of df2 based on the range selected with lat and lon (converted based on x and y coordinates)
        # converted using the one map API

        # filter within 500m in x first
        df2f = df2.filter((data3[0] - data2 < df2["x_coord"]) & (df2["x_coord"] < data3[0] + data2))
        # filter within 500m in y first
        df2f = df2f.filter((data3[1] - data2 < df2f["y_coord"]) & (df2f["y_coord"] < data3[1] + data2))
        # These are the carparks within 500m X and Y direction
        df2f.sort("x_coord", "y_coord")

        # need find lat and lon  of each of the carpark so
        # merge x and y and id into 1 column
        # tip:use array so that value of x coord and y coord merge to an array in each row
        df2f = df2f.withColumn("x_y", array("x_coord", "y_coord", "_id"))
        df2f.show(1000)
        # carparkxy is a list of arrays
        carparkxy = df2f.select("x_y").collect()
        # print(type(carparkxy))
        # print(carparkxy[0])
        # print(carparkxy[0][0])
        # empty list
        carparklatlon = []
        # for every element in carparkxy , need to convert to lat and lon from x and y
        for n in range(len(carparkxy)):
            # print(f"X is {carparkxy[n][0][0]} and Y is {carparkxy[n][0][1]}")
            # use onemap api to convert
            parameters4 = {
                "X": carparkxy[n][0][0],
                "Y": carparkxy[n][0][1]
            }

            response3 = requests.get("https://developers.onemap.sg/commonapi/convert/3414to4326", params=parameters4)
            # print(response3)
            lat = response3.json()["latitude"]
            lon = response3.json()["longitude"]
            # append the lat and lon and id to carparklatlon
            carparklatlon.append([lat, lon, carparkxy[n][0][2]])
        print(carparklatlon)
        # create scheme so when create DF later values will fall under the respective columns defined
        Schema = StructType([
            StructField('lat', DoubleType(), True),
            StructField('lon', DoubleType(), True),
            StructField('_id', FloatType(), True)
        ])
        # df3 contains lat and lon converted from x and y values
        # create dataframe based on the list carparklatlon and also the Schema
        df3 = spark.createDataFrame(data=carparklatlon, schema=Schema)
        # change data type from float to long
        df3 = df3.withColumn("_id", col("_id").cast(LongType()))
        df3.printSchema()

        # then merge df3 to df2f to see lat and lon of each carpark along with the details
        dfm = df2f.join(df3, df2f["_id"] == df3["_id"], "inner")
        # rename address to name for tooltip later
        dfm = dfm.withColumn("name", dfm["address"])

        # merge with df1 so can lots available real time, inner join on the carpark_number/id
        # forming df_final
        df_final = dfm.join(df1, dfm["car_park_no"] == df1["carpark_number"], "inner")

        df_final.show(10)

        dfm = df_final.select("lat", "lon", "name", "density")
        # convert to pd df so can change to dictionary later
        dfm = dfm.toPandas()
        dicts = dfm.to_dict('rows')
        print(dicts)

        for item in dicts:
            item["tooltip"] = "{} ({:.1f})".format(item['name'], item['density'])

        print(dicts)

        print("Hi")
        # to add tooltip to the dictionary example
        # dicts2 = [{'city': 'Aalborg', 'lat': 1.3207472024589295, 'lng': 103.86617287009032, 'density': 5,
        # 'tooltip': 'Aalborg (5.0)'}]

        # can be any order
        # so data2 gives location of car parks within 500m
        geojson = dlx.dicts_to_geojson(dicts)  # convert to geojson
        geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf
        # 2/8 show color dots to show if got space available , red dun have , green have alot , yellow middle
        # merge dfm with df1 through inner join
        # then do categorize for space with color
        # use leaflet example
        # data2 = dlx.dicts_to_geojson([{**c, **dict(tooltip=c['name'])} for c in countries])
        return geobuf

