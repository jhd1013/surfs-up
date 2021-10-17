import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

# Connect to the database
engine = create_engine("sqlite:///hawaii.sqlite")

# Setup the sqlalchemy classes, reflect the databases and the tables
# we'll be using, and create the session.
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

# Setup flask and the routes to the web pages

# Create a new flask instance
app = Flask(__name__)

# Create the root path (route) for the web site
@app.route('/')
def welcome():
    return (''' Welcome to the Climate Analysis API!
                Available Routes:
                /api/v1.0/precipitation
                /api/v1.0/stations
                /api/v1.0/tobs
                /api/v1.0/temp/start/end ''')

@app.route('/api/v1.0/precipitation')
# Return the precipitation data for the last year of data available in the database
def precipitation():
    with Session(engine) as session:
        # Find the date of the most recent measurement
        latest_measurement = session.query(Measurement.date).order_by(Measurement.date.desc()).limit(1).all()
        latest_measurement = dt.datetime.strptime(latest_measurement[0][0], '%Y-%m-%d')

        # Calculate the date one year from the last date in data set.
        prev_year = latest_measurement - dt.timedelta(days=365)

        # Perform a query to retrieve the data and precipitation scores for last available year
        precipitation = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= prev_year).all()

    # Convert to a dictionary where the date is the key and the precip is the value
    precip_dict = {date:prcp for date, prcp in precipitation}

    return jsonify(precip_dict)

@app.route('/api/v1.0/stations')
def stations():
    with Session(engine) as session:
        # Query the database for all unique (distinct) station IDs.
        station_list = session.query(Station.station).order_by(Station.station.desc()).all()
    station_list = list(np.ravel(station_list))
    return jsonify(station_list=station_list)

@app.route('/api/v1.0/tobs')
def temp_monthly():
    with Session(engine) as session:
        # Find the date of the most recent measurement
        latest_measurement = session.query(Measurement.date).order_by(Measurement.date.desc()).limit(1).all()
        latest_measurement = dt.datetime.strptime(latest_measurement[0][0], '%Y-%m-%d')

        # Calculate the date one year from the last date in data set.
        prev_year = latest_measurement - dt.timedelta(days=365)

        temp_results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == 'USC00519281').\
            filter(Measurement.date >= prev_year).all()
        # Convert to a dictionary where the date is the key and the precip is the value
    temps_dict = {date:tobs for date, tobs in temp_results}
    return jsonify(temps_dict)

@app.route('/api/v1.0/temp/<start>/')
@app.route('/api/v1.0/temp/<start>/<end>')
def stats(start=None, end=None):
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    # If no "end" parameter is provided, get data from start to end of available dataset.
    with Session(engine) as session:
        if not end:
            # Asterisk (*) operator in this context is to unpack a list.
            results=session.query(*sel).filter(Measurement.date >= start).all()
            temps=list(np.ravel(results))
        else:
            results = session.query(*sel).filter(Measurement.date >= start).\
                filter(Measurement.date <= end).all()
            temps=list(np.ravel(results))

    return jsonify(temps=temps)

# Main routine
if __name__ == "__main__":
    app.run(debug=True)