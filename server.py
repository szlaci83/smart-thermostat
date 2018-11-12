#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import datetime
import requests
import collections
from pprint import pprint

from multiprocessing import Queue
import threading

from db import *
from settings import *
from credentials import *
from utils import *

import mock_relay as HEATING_RELAY
import logging

current_humidity = 0
current_temperature = 0
current_target_temperature = 0

HEATING = False
FORCE_HEATING = ForceHeating.UNSET

q = Queue()
db = DatabaseManager()

humidities = {}
temperatures = {}
weather_data = {}
TIMER_SETTINGS = {}


def on_connect(client, userdata, flags, rc):
    logging.debug("Connected with result code %d" %rc)
    client.subscribe(TOPIC)
    logging.debug("Subscribed to topic %s" % TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        data['epoch'] = str(time.time())
        q.put(data)
    except Exception as e:
        logging.error(e)
    logging.debug("received data: %s" % str(data))


def weather_worker():
    global weather_data
    query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
    try:
        weather_data = requests.get(query, headers=JSON_HEADER).json()
    except:
        logging.error("Could not get data from %s" % query)
    logging.debug("WeatherAPI temp: %d" % weather_data['main']['temp'])
    logging.debug("WeatherAPI humidity: %d" % weather_data['main']['humidity'])
    #pprint(weather_data)
    # enough sleep for free tier usage
    time.sleep(10 * 60 + 1)


def timer_worker():
    while True:
        apply_setting()
        time.sleep(TIMER_REFRESH)


def force_worker(switch_setting, period):
    logging.debug("Forcing %s for %s minutes." % (str(switch_setting), period))
    global FORCE_HEATING
    FORCE_HEATING = switch_setting
    time.sleep(period * 60)
    logging.debug("Force over")
    FORCE_HEATING = ForceHeating.UNSET


def forced_switch(switch_setting, period):
    weather_thread = threading.Thread(target=force_worker, args=[switch_setting, period])
    weather_thread.start()


def apply_setting():
    global HEATING
    global current_humidity
    global current_temperature
    global current_target_temperature
    logging.debug("current temperature: %d" % current_temperature)
    now = datetime.datetime.now()

    desired_temp = TIMER_SETTINGS[now.strftime("%A")][now.hour][int(now.minute / 15)]
    logging.debug("desired temperature: %d" % desired_temp)
    if FORCE_HEATING.value is not ForceHeating.UNSET:
        HEATING = FORCE_HEATING.value
    else:
        if current_temperature <= desired_temp - THRESHOLD:
            if not HEATING:
                HEATING = True
                logging.debug("HEATING: %s" % str(HEATING))
        else:
            if current_temperature >= desired_temp + THRESHOLD:
                if HEATING:
                    HEATING = False
                    logging.debug("HEATING: %s" % str(HEATING))

    HEATING_RELAY.on(led=True) if HEATING else HEATING_RELAY.off(led=True)


# Format: ("Monday", 10, 0, 11, 45, 24)
def change_setting(day, start_hour, start_min, end_hour, end_min, desired_temp):
    logging.debug("changing setting: %s - %d:%d -> %d:%d = %dC" % (day, start_hour, start_min, end_hour, end_min, desired_temp))
    global TIMER_SETTINGS
    hour = start_hour
    minute = start_min
    try:
        while True:
            if minute == 60:
                minute = 0
                hour += 1
            TIMER_SETTINGS[day][hour][int(minute / 15)] = desired_temp
            minute += 15
            if hour == end_hour and minute == end_min:
                break
    except KeyError:
        logging.error("Wrong day: %s" % day)
    except IndexError:
        logging.error("Wrong hour or minute: h: %d, min: %d, h:%d, min: %d" % (start_hour, start_min, end_hour, end_min))
    save_heating_settings(setting=TIMER_SETTINGS)
    return


def db_worker():
    global HEATING
    global current_humidity
    global current_temperature
    global humidities
    global temperatures

    while True:
        results = q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            try:
                humidities[results['location']].appendleft(results['humidity'])
            except KeyError:
                humidities[results['location']] = collections.deque(5 * [results['humidity']], 5)
            try:
                temperatures[results['location']].appendleft(results['temp'])
            except KeyError:
                temperatures[results['location']] = collections.deque(5 * [results['temp']], 5)

            norm_temp = normalise_dict(temperatures)
            norm_hum = normalise_dict(humidities)

            logging.debug(norm_temp)
            logging.debug(norm_hum)

            temperature_reading = norm_temp[MAIN_SENSOR]
            humidity_reading = norm_hum[MAIN_SENSOR]

            results['heating'] = HEATING
            if not DEV:
                if temperature_reading != current_temperature or humidity_reading != current_humidity:
                    db.put(results)


def run():
    global TIMER_SETTINGS
    TIMER_SETTINGS = load_heating_settings_from_file()
    client = mqtt.Client()
    client.connect(SERVER_HOST, SERVER_MQTT_PORT, SERVER_TIMEOUT)

    client.on_connect = on_connect
    client.on_message = on_message

    db_thread = threading.Thread(target=db_worker)
    db_thread.start()

    timer_thread = threading.Thread(target=timer_worker)
    timer_thread.start()

    weather_thread = threading.Thread(target=weather_worker)
    weather_thread.start()

    client.loop_forever()


if __name__ == '__main__':
    print(BANNER)
    if SERVER_LOG and SERVER_LOG != '':
        print("Server started see %s for details!" % SERVER_LOG)
        print("MQTT port: %d" % SERVER_MQTT_PORT)
    logging.basicConfig(filename=SERVER_LOG, level=LOGGING_LEVEL, format="%(asctime)s:%(levelname)s:%(message)s")
    run()
