# Import the dependencies.
import datetime as dt
import numpy as np

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.dialects import sqlite
from sqlalchemy import create_engine, func, cast, Date, text

from flask import Flask, jsonify

# Add this section to EVERY Python file that you want to run or Debug in VSCode
import os
os.chdir(os.path.dirname(__file__))


#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start<br/>"
        f"/api/v1.0/temp/start/end<br/>"
        f"<p>'start' and 'end' date should be in the format MMDDYYYY.</p>"

    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year"""
    # Calculate the date 1 year ago from last date in database
    prev_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Query for the date and precipitation for the last year
    precipitation = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= prev_year).all()

    session.close()
    # Dict with date as the key and prcp as the value
    precip = {date: prcp for date, prcp in precipitation}
    return jsonify(precip)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    results = session.query(Station.station).all()

    session.close()

    # Unravel results into a 1D array and convert to a list
    stations = list(np.ravel(results))
    return jsonify(stations=stations)


@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Return the temperature observations (tobs) for previous year."""
    # Calculate the date 1 year ago from last date in database
    prev_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Query the primary station for all tobs from the last year
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == 'USC00519281').\
        filter(Measurement.date >= prev_year).all()

    session.close()
    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))

    # Return the results
    return jsonify(temps=temps)


@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX."""

    # Select statement (If you didn't do this, but used the functions directly in your session.query,
    # that would be perfectly fine. This is just a different way to do it.)
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # start = dt.datetime.strptime(start, "%m/%d/%Y")
        # # calculate TMIN, TAVG, TMAX for dates greater than start
        # results = session.query(*sel).\
        #     filter(Measurement.date >= start).all()
        # # Unravel results into a 1D array and convert to a list
        # temps = list(np.ravel(results))
        # return jsonify(temps)

        # Be certain to convert the date you got from the URL to make sure it is a valid date
        # and in the format you expect. If you don't do this, you could get an error.
        # But then, you need to convert the date back to string in YYYY-MM-DD format
        # because SQLite doesn't actyally have a date type, it just stores dates as strings
        # in the format "YYYY-MM-DD". So, you need to convert the date to a string in that format
        # or the date comparison won't work the way you expect.
        start = dt.datetime.strptime(start, "%m%d%Y").strftime("%Y-%m-%d")
        results = session.query(*sel).\
            filter(Measurement.date >= start).all()

        session.close()

        temps = list(np.ravel(results))
        return jsonify(temps)

    # calculate TMIN, TAVG, TMAX with start and stop
    # see the comment in line 128 above
    start = dt.datetime.strptime(start, "%m%d%Y").strftime("%Y-%m-%d")
    end = dt.datetime.strptime(end, "%m%d%Y").strftime("%Y-%m-%d")

    # This works too: sql -= session.query(*sel).filter(Measurement.date >= start, Measurement.date <= end)
    # Here, we put the SQL Query object in a variable because we're going to use it in two places
    # the first place is to get the results, the second place is to get the SQL string
    sql = session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end)
    # Pull the results from the query
    results = sql.all()

    # Compile the query using the SQLite dialect
    sql_string = str(sql.statement.compile(dialect=sqlite.dialect()))
    
    # FYI, this is one way to get the structure of the table
    table_name = 'measurement'  # Replace with your table name
    result = session.execute(text(f"PRAGMA table_info({table_name});")).all()
    info = list(np.ravel(result))
    print(list)
    print(info)

    session.close()

    # Unravel results into a 1D array and convert to a list
    mytemps = {
     "temps": list(np.ravel(results)),
     # "SQL": sql_string - Uncomment this to view the SQL Query in the browser for debugging only
    }
    return jsonify(temps=mytemps)


if __name__ == '__main__':
    app.run()