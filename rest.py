from flask import Flask, jsonify, request, Response, make_response,  current_app
from flask_cors import CORS
import time
import threading
from timer_settings import TIMER_SETTINGS

import server

app = Flask(__name__)
CORS(app)


def add_headers(response, http_code, token=None):
    '''
    Wraps a Http response and a given http code into CORS and JSON headers
    :param response: The response to wrap
    :param http_code: The http code to wrap
    :param token: JWT token
    :return: the wrapped HTTP response with headers
    '''
    response = jsonify(response), http_code
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['content-type'] = "application/json"
    if token is not None:
        response.headers['Authorization'] = token
    return response


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
        return add_headers("Error wrong day name, try: Monday, Tuesday etc...", 500)
    except IndexError:
        return add_headers("Error wrong hour or minute(hours 0-23, minutes: 0-59)", 500)


@app.route("/settings", methods=['POST'])
def post_settings():
    pass

if __name__ == '__main__':
    server_thread = threading.Thread(target=server.run)
    server_thread.start()

    app.run(host='0.0.0.0')

