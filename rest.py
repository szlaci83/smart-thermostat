import logging
import threading

from flask import Flask, request
from flask_cors import CORS
import copy

import server
from errors import *
from forceheating import ForceHeating
from properties import FORCE_ON_DEFAULT, SERVER_REST_PORT, SERVER_HOST, SERVER_LOG, SERVER_MQTT_PORT, LOGGING_LEVEL, \
    HTTP_OK, BANNER
from utils import add_headers, validate_req

app = Flask(__name__)
CORS(app)


@app.route("/state", methods=['GET'])
def get_state():
    logging.info(request.args)
    logging.debug(request)
    state = server.current_state.get_json_repr()
    logging.info(state)
    return add_headers(state, HTTP_OK)


@app.route("/detailed-weather", methods=['GET'])
def get_weather():
    logging.info(request.args)
    logging.debug(request)
    weather = server.current_state.weather_data
    logging.info(weather)
    return add_headers(weather, HTTP_OK)


@app.route("/sys-info", methods=['GET'])
def get_sys_info():
    logging.info(request.args)
    logging.debug(request)
    return add_headers({"status": "Future use"}, HTTP_OK)


@app.route("/settings", methods=['GET'])
def get_settings():
    logging.info(request.args)
    logging.debug(request)
    settings = server.get_main_settings()
    return add_headers(settings, HTTP_OK)


@app.route("/settings", methods=['POST'])
def post_settings():
    logging.info(request.args)
    logging.debug(request)
    current_settings_fields = list(server.get_main_settings().keys())
    if not validate_req(request, current_settings_fields):
        logging.error(JSON_ERROR)
        return add_headers(JSON_ERROR, JSON_ERROR['code'])
    server.change_main_setting(request.json)
    res = copy.copy(request.json)
    res["status"] = "changed settings"
    return add_headers(res, HTTP_OK)


@app.route("/heating-settings", methods=['GET'])
def get_heating_settings():
    logging.info(request.args)
    logging.debug(request)
    day = request.args.get('day')
    hour = request.args.get('hour')
    minute = request.args.get('minute')
    # if hour is present, day has to be present, if minute is present, hour and day has to be present
    if (day is None and hour is not None) or (minute is not None and (hour is None or day is None)):
        logging.error(PARAM_ERROR)
        return add_headers(PARAM_ERROR, PARAM_ERROR['code'])
    try:
        result = server.current_state.get_setting_for_time(day=day, hour=hour, minute=minute, target_date=None)
        logging.info(result)
        return add_headers(result, HTTP_OK)
    except KeyError:
        logging.error(DAY_ERROR)
        return add_headers(DAY_ERROR, DAY_ERROR['code'])
    except IndexError:
        logging.error(TIME_ERROR)
        return add_headers(TIME_ERROR, TIME_ERROR['code'])


@app.route("/heating-settings", methods=['POST'])
def post_heating_settings():
    logging.info(request.args)
    logging.debug(request)
    fields = ['day', 'start_hour', 'start_min', 'end_hour', 'end_min', 'desired_temp']
    if not validate_req(request, fields):
        logging.error(JSON_ERROR)
        return add_headers(JSON_ERROR, JSON_ERROR['code'])
    setting = request.json
    server.change_timer_setting(**setting)
    return add_headers({"status": "changed heating settings"}, HTTP_OK)


@app.route("/switch-heating", methods=['POST'])
def switch_heating():
    logging.info(request.args)
    logging.debug(request)
    heating = ForceHeating.OFF if "off" in request.json and request.json["off"] is True else ForceHeating.ON
    force_minutes = FORCE_ON_DEFAULT if "minutes" not in request.json else request.json['minutes']
    server.forced_switch(heating, period=force_minutes)
    result = "Forcing heating: %s for %d minute(s)" % (heating, force_minutes)
    logging.debug(result)
    return add_headers({"status": str(result)}, HTTP_OK)


if __name__ == '__main__':
    print(BANNER)
    print("Server started see %s for details!" % SERVER_LOG)
    print("MQTT port: %d" % SERVER_MQTT_PORT)
    print("REST API port: %d" % SERVER_REST_PORT)
    if SERVER_LOG and SERVER_LOG != '':
        logging.basicConfig(filename=SERVER_LOG, level=LOGGING_LEVEL, format="%(asctime)s:%(levelname)s:%(message)s")

    server_thread = threading.Thread(target=server.run)
    server_thread.start()

    app.run(host=SERVER_HOST, port=SERVER_REST_PORT)
