from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, session)
from werkzeug.exceptions import abort
from geopy.geocoders import Nominatim
import datetime as dt
from datetime import date, datetime
import requests
import os
import json
from math import sin, cos, sqrt, atan2, radians

geolocator = Nominatim(user_agent="WeatherApplication")
api_key = '2c62ed2633df21a18d7700c436125852'
open_weather_api_endpoint = 'http://api.openweathermap.org/data/2.5/onecall'
param_dict = {'appid': api_key, 'lat': None, 'lon': None, 'units': 'imperial'}
basedir = os.path.abspath(os.path.dirname(__file__))
location_file_path = 'static/locations.json'
bp = Blueprint('suggest', __name__)
todays_date = date.today().isoformat()


def get_locations():
    '''
    Function to read the park details.
    :return: list of all the parks with details.
    '''

    data_file = os.path.join(basedir, location_file_path)
    with open(data_file, 'r') as f:
        locations = json.load(f)
        return locations


def check_if_within_range(user_latitude, user_longitude, radius, park_latitude, park_longitude):
    lat1 = radians(user_latitude)
    lon1 = radians(user_longitude)
    lat2 = radians(float(park_latitude))
    lon2 = radians(float(park_longitude))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    R = 6373.0
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    conversion_factor = 0.621371
    distance = R * c * conversion_factor

    if distance <= float(radius):
        return distance, True
    else:
        return distance, False


def get_request_data(request):
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    radius = float(request.form['radius'])
    weather = request.form['weatherv']
    userDate = request.form['date']

    # construct user object
    user_obj = {}
    user_obj['latitude'] = latitude
    user_obj['longitude'] = longitude
    user_obj['radius'] = radius
    user_obj['favWeather'] = weather
    return latitude, longitude, radius, weather, userDate, user_obj


@bp.route('/', methods=['GET', 'POST'])
def index():
    showMessage = False
    parks = []
    final_parks = []
    user_obj = {}
    if request.method == 'POST':
        showMessage = True
        parks = get_locations()

        # get user data from request object
        latitude, longitude, radius, weather, userDate, user_obj = get_request_data(request)

        # get probable locations
        # probable_locations = parks
        probable_locations = []
        for park in parks:
            distance, within_range = check_if_within_range(latitude, longitude, radius, park['lat'], park['lng'])
            park['distance'] = "About " + str(int(distance)) + ' miles'
            if within_range:
                probable_locations.append(park)

        # sort based on distance
        probable_locations = sorted(probable_locations, key=lambda i: i['distance'])

        # filter based on weather and date.

        # number of days from today.
        forDate = datetime.fromisoformat(userDate).date()

        for park in probable_locations:
            param_dict['lat'] = float(park['lat'])
            param_dict['lon'] = float(park['lng'])
            param_dict['exclude'] = 'current,minutely,hourly,alerts'
            try:
                response = requests.get(open_weather_api_endpoint, params=param_dict)
                if response.status_code != 200:
                    flash("Sorry No park matches for your criteria!")
                else:
                    data = response.json()
                    park['lat'] = data['lat']
                    park['lon'] = data['lon']

                    for day_info in data['daily']:
                        respDate = datetime.fromtimestamp(day_info['dt']).date()
                        if respDate == forDate:
                            if day_info['weather'][0]['main'] == user_obj['favWeather']:
                                park['mainWeather'] = day_info['weather'][0]['main']
                                park['desc'] = day_info['weather'][0]['description']
                                park['temp_day'] = day_info['temp']['day']
                                park['temp_night'] = day_info['temp']['night']
                                park['feels_day'] = day_info['feels_like']['day']
                                park['feels_night'] = day_info['feels_like']['night']

                                final_parks.append(park)

            except:
                print('error happened')
    return render_template('mainPage/index.html', locations=final_parks, showMessage=showMessage, userData=user_obj,
                           todays_date=todays_date)
