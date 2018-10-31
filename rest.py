from flask import Flask, request
from flask_cors import CORS
import time
from utils import add_headers, validate_req
from errors import *
import threading
from timer_settings import TIMER_SETTINGS

import server

app = Flask(__name__)
CORS(app)


@app.route("/status", methods=['GET'])
def get_status():
    status = {'epoch': str(time.time()),
              'outside_temp': server.weather_data['main']['temp'],
              'outside_humidity': server.weather_data['main']['humidity'],
              'heating_status': "ON" if server.HEATING else "OFF",
              'humidity': server.normalise_dict(server.humidities),
              'temp': server.normalise_dict(server.temperatures),
              'target_temp': server.current_target_temperature}
    return add_headers(status, 200)


@app.route("/settings", methods=['GET'])
def get_settings():
    day = request.args.get('day')
    hour = request.args.get('hour')
    minute = request.args.get('minute')
    try:
        result = TIMER_SETTINGS
        if day:
            result = result[day]
        if hour:
            result = result[int(hour)]
        if minute:
            result = result[int(int(minute) / 15)]
        return add_headers(result, 200)
    except KeyError:
        return add_headers(DAY_ERROR, DAY_ERROR['code'])
    except IndexError:
        return add_headers(TIME_ERROR, TIME_ERROR['code'])


@app.route("/settings", methods=['POST'])
def post_settings():
    fields = ['day', 'start_hour', 'start_min', 'end_hour', 'end_min', 'desired_temp']
    if not validate_req(request, fields):
        return add_headers(JSON_ERROR, JSON_ERROR['code'])
    setting = request.json
    server.change_setting(setting['day'],
                          setting['start_hour'],
                          setting['start_min'],
                          setting['end_hour'],
                          setting['end_min'],
                          setting['desired_temp'])
    return add_headers(True, 200)


if __name__ == '__main__':
    server_thread = threading.Thread(target=server.run)
    server_thread.start()

    app.run(host='0.0.0.0')

