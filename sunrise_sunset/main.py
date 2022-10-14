import re
from datetime import datetime

import requests
from dateutil import tz

from flask import Flask, request
from flask import render_template


app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    locations_json_url = 'https://raw.githubusercontent.com/flores-jacob/philippine-regions-provinces-cities-municipalities-barangays/master/philippine_provinces_cities_municipalities_and_barangays_2019v2.json'
    response = requests.get(locations_json_url)
    data = response.json()
    provinces_list =[]
    for region in data.keys():
        province_list = data[region]['province_list']
        for province in province_list.keys():
            provinces_list.append(province)
    provinces_list.sort()
    return render_template('base.html', prov=provinces_list)


def convert_location_to_coords(loc):
    api_url = f'https://nominatim.openstreetmap.org/search?q={loc.replace(" ", "+")}&format=geojson&countrycodes=PH'
    response = requests.get(api_url)
    data = response.json()
    lon = data['features'][0]['geometry']['coordinates'][0]
    lat = data['features'][0]['geometry']['coordinates'][1]
    return lat, lon


def convert_utc_to_local_time(sunrise, sunset):
    # extract date and time
    match_sr = re.search(r'([0-9]+-[0-9]+-[0-9]+)T([0-9]+:[0-9]+:[0-9]+)\+00:00', sunrise)
    match_ss = re.search(r'([0-9]+-[0-9]+-[0-9]+)T([0-9]+:[0-9]+:[0-9]+)\+00:00', sunset)
    # assign date and time to sunrise and sunset variables
    date_sr, date_ss = match_sr.group(1), match_ss.group(1)
    time_sr, time_ss = match_sr.group(2), match_ss.group(2)
    # get the relevant timezones
    from_zone, to_zone = tz.gettz('UTC'), tz.gettz('Asia/Manila')
    # combine date and time for both sunrise and sunset
    datetime_sr, datetime_ss = date_sr + ' ' + time_sr, date_ss + ' ' + time_ss
    format = "%Y-%m-%d %H:%M:%S"
    # create datetime objects
    dt_sr_utc, dt_ss_utc = datetime.strptime(datetime_sr, format), datetime.strptime(datetime_ss, format)
    # replace tz to UTC
    dt_sr_utc, dt_ss_utc = dt_sr_utc.replace(tzinfo=from_zone), dt_ss_utc.replace(tzinfo=from_zone)
    # convert UTC to local tz
    dt_sr_local, dt_ss_local = dt_sr_utc.astimezone(to_zone), dt_ss_utc.astimezone(to_zone)
    # format to desired datetime string
    local_time_sr, local_time_ss = dt_sr_local.strftime("%I:%M:%S %p"), dt_ss_local.strftime("%I:%M:%S %p")

    return local_time_sr, local_time_ss


@app.route('/times', methods=['POST'])
def get_the_time_data():
    if request.method == 'POST':
        location = request.form['location']
        lat, lon = convert_location_to_coords(location)
        sun_api = f'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0'
        response = requests.get(sun_api)
        data = response.json()
        sunrise_utc = data['results']['sunrise']
        sunset_utc = data['results']['sunset']
        local_sr, local_ss = convert_utc_to_local_time(sunrise_utc, sunset_utc)
        return render_template('result.html', sunrise=local_sr, sunset=local_ss, location=location)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)