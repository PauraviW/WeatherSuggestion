from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, session)

from datetime import date, datetime
import requests
import os
import json
from math import sin, cos, sqrt, atan2, radians
import copy

# important variables.
api_key = '2c62ed2633df21a18d7700c436125852'
open_weather_api_endpoint = 'http://api.openweathermap.org/data/2.5/onecall'
param_dict = {'appid': api_key, 'lat': None, 'lon': None, 'units': 'imperial', 'exclude':'minutely,hourly,current,alerts'}
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
    """
    Method to check if distance between 2 places is within the range prescribed by the user
    :param user_latitude: User location - latitude
    :param user_longitude: User Location - longitude
    :param radius: Maximum miles user can travel
    :param park_latitude: Park Location - Latitude
    :param park_longitude: Park Location - Longitude
    :return: boolean - If a park is within the range specified by the user then return true else false.
    """
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
    """
    Method to obtain parameters from the request object
    :param request: form filled with user preferences
    :return: latitude, longitude - float
            radius : maximum miles surrounding the park
            weather : user's favourite weather
            user_obj : A dictionary containing all the above mentioned features to be passed to the template.
    """
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    radius = float(request.form['radius'])
    weather = request.form['weatherv']

    # construct user object
    user_obj = {}
    user_obj['latitude'] = latitude
    user_obj['longitude'] = longitude
    user_obj['radius'] = radius
    user_obj['favWeather'] = weather
    return latitude, longitude, radius, weather, user_obj


@bp.route('/', methods=['GET'])
def index():
    """
    Factory method that handles GET request on the first call and POST requests on click of the submit button
    :return:
    """
    showMessage = False
    return render_template('mainPage/index.html',  showMessage=showMessage)

@bp.route('/', methods=['POST'])
def find_best_park():
    """
    Method to handle POST requests
    :return: park details as per user preferences.
    """
    showMessage = False
    final_parks = []
    user_obj = {}
    if request.method == 'POST':
        showMessage = True
        parks = get_locations()

        # get user data from request object
        latitude, longitude, radius, weather, user_obj = get_request_data(request)

        # get probable locations
        # probable_locations = parks
        probable_locations = []
        for park in parks:
            distance, within_range = check_if_within_range(latitude, longitude, radius, park['lat'], park['lng'])
            park['distance'] = "About " + str(int(distance)) + ' miles'
            if within_range:
                probable_locations.append(park)



        # filter based on weather and date.
        for park in probable_locations:

            # generate parameters for the request
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

                    # segregate based on favourite weather
                    for day_info in data['daily']:
                        if day_info['weather'][0]['main'] == user_obj['favWeather']:
                            park['mainWeather'] = day_info['weather'][0]['main']
                            park['desc'] = day_info['weather'][0]['description']
                            park['temp_day'] = day_info['temp']['day']
                            park['temp_night'] = day_info['temp']['night']
                            park['feels_day'] = day_info['feels_like']['day']
                            park['feels_night'] = day_info['feels_like']['night']
                            park['idate'] = date.fromtimestamp(day_info['dt']).strftime("%A %d. %B %Y")

                            final_parks.append(copy.deepcopy(park))


            except:
                print('error happened')

                # sort based on distance
        final_parks = sorted(final_parks, key=lambda i: (datetime.strptime(i['idate'], "%A %d. %B %Y"), i['distance']))

    return render_template('mainPage/index.html', locations=final_parks, showMessage=showMessage, userData=user_obj,
                               todays_date=todays_date)
