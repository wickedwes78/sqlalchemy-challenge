import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f'Available Routes:<br/>'
        '<br/>'    
        f'View the most recent year of precipitation data:<br/>'          
        f'/api/v1.0/precipitation<br/>'
        '<br/>'
        f'View all station data:<br/>' 
        f'/api/v1.0/stations<br/>'
        '<br/>'
        f'View the most recent year of temperature observations for the most active station:<br/>' 
        f'/api/v1.0/tobs<br/>'
        '<br/>'
        f'View the min/max/avg temperatures from date chosen, date format shown below (date range is 2016-08-23 to 2017-08-23):<br/>' 
        f'/api/v1.0/temperature/yyyy-mm-dd<br/>'
        '<br/>'
        f'View the min/max/avg temperatures between dates chosen, date format shown below (date range is 2016-08-23 to 2017-08-23):<br/>' 
        f'/api/v1.0/temperature/yyyy-mm-dd/yyyy-mm-dd<br/>'
    )

#query to determine most recent year and the date one year from that
#to be used for multiple routes

#create session from Python to the DB
session = Session(engine)

#query to find most recent date
recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
#add most recent date to list
recent_date_list = [date for date in recent_date]

#list ready to add date from one year prior to most recent date
one_year = []

#calculate the date one year from most recent date
for date in recent_date_list:
    #format date ready for timedelta calc
    date_format = dt.datetime.strptime(date, '%Y-%m-%d').date()
    #timedelta calc
    oneyearago = date_format - dt.timedelta(days=365)
    #add to list
    one_year.append(oneyearago)

session.close()

#precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)
  
    #query to get all date&prcp data
    #use date from query outside app.route to capture the date 12mths from recent
    results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date.asc()).filter(Measurement.date>=oneyearago).all() 

    #create list for display
    precip = []
    for date, prcp in results:
        #create and add to dictionary
        rain_dict = {}
        rain_dict[date] = prcp
        #add results to list
        precip.append(rain_dict)

    session.close()

    return jsonify(precip)

#stations route
@app.route("/api/v1.0/stations")
def stations():
    #create session from Python to the DB
    session = Session(engine)

    #query to get all station details
    results = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    #create list for display
    station_list = []
    for id, station, name, latitude, longitude, elevation in results:
        #create and add to dictionary
        station_dict = {} 
        station_dict[f"{id} Station"] = station #use ID to keep station at top of dictionary
        station_dict["Name"] = name
        station_dict["Lat"] = latitude
        station_dict["Long"] = longitude
        station_dict["Elevation"] = elevation
        #add results to the list
        station_list.append(station_dict)

    session.close()    
    
    return jsonify(station_list)

#tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    #create session from Python to the DB
    session = Session(engine)

    #to find most active station count number of results for each station and order desc
    stations = session.query(Measurement.station,func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    most_active = stations[0][0]
    
    #query to retrieve date and temperature for one year from most recent for the most active station
    #use date from query outside app.route to capture the date 12mths from recent 
    results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date>=oneyearago).filter(Measurement.station == most_active).all()
    
    #save the query results as a list to return
    #although not required, include the station detail for visibility
    tobs = [{"Station": most_active, "Date": result[0], "Temperature": result[1]} for result in results]
    
    session.close()
    
    return jsonify(tobs)

#start route
@app.route("/api/v1.0/temperature/<start>")
def startdate(start):
    #create session from Python to the DB
    session = Session(engine)    
    
    #convert date given to required datetime format
    startdate = dt.datetime.strptime(start, '%Y-%m-%d').date()
  
    #query on date range to capture above function details
    function_results = session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date >= startdate).all()

    #query results formatted for viewing
    #although not required start date included as first dictionary item for visibility
    temp_results = [{"1.Start Date": startdate, "Min": results[0], "Avg": results[1], "Max": results[2]} for results in function_results]
    
    session.close()

    return jsonify(temp_results)

#start end route
@app.route("/api/v1.0/temperature/<start>/<end>")
def startend(start,end):
    #create session from Python to the DB
    session = Session(engine)
    
    #convert dates given to required datetime format
    firstdate = dt.datetime.strptime(start, '%Y-%m-%d').date()
    lastdate = dt.datetime.strptime(end, '%Y-%m-%d').date()

    #query on date range to capture above function details
    function_results = session.query(func.min(Measurement.tobs),func.max(Measurement.tobs),func.avg(Measurement.tobs)).filter(and_(Measurement.date >= firstdate, Measurement.date <= lastdate)).all()

    #query results formatted for viewing
    #although not required start & end date included as first & second dictionary item for visibility
    temp_results = [{"1. Start Date": firstdate, "2. End Date": lastdate,"Min": results[0], "Avg": results[1], "Max": results[2]} for results in function_results]

    session.close()
    
    return jsonify(temp_results)

if __name__ == '__main__':
    app.run(debug=True)
