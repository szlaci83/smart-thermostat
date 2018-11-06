#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import datetime
import requests
import collections
import pickle
from pprint import pprint

from multiprocessing import Queue
import threading

from db import *
from settings import *
from credentials import *

import mock_relay as HEATING_RELAY
import logging

current_humidity = 0
current_temperature = 0
current_target_temperature = 0
q = Queue()
HEATING = False
FORCE_HEATING = False
FORCE_NOT_HEATING = False
db = DatabaseManager()
humidities = {}
temperatures = {}
weather_data = {}
TIMER_SETTINGS = {}


def load_heating_settings(setting_file=HEATING_SETTINGS):
    global TIMER_SETTINGS
    with open(setting_file, 'rb') as handle:
        TIMER_SETTINGS = pickle.load(handle)
    logging.info("heating settings loaded from %s" % setting_file)


def save_heating_settings(it, setting_file=HEATING_SETTINGS):
    with open(setting_file, 'wb') as file:
        pickle.dump(it,  file, protocol=pickle.HIGHEST_PROTOCOL)
    logging.info("heating settings saved to %s" % setting_file)
    return


def normalise_list(values_list):
    # smoothing outliers (ignore readings outside tolerance)
    if abs(values_list[0] - values_list[1]) > TOLERANCE and abs(values_list[1] - values_list[2]) > TOLERANCE:
        values_list[1] = values_list[0]
    return sum(values_list) / 5


def normalise_dict(target_dict):
    norm_dict = {}
    for k, v in target_dict.items():
        norm_dict[k] = normalise_list(v)
    return norm_dict


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
    # TODO: remove print
    print(data)


def weather_worker():
    global weather_data
    query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
    try:
        weather_data = requests.get(query, headers=JSON_HEADER).json()
    except:
        logging.error("Could not get data from %s" % query)
    # TODO: remove prints
    print(weather_data['main']['temp'])
    print(weather_data['main']['humidity'])
    pprint(weather_data)
    # enough sleep for free tier usage
    time.sleep(11 * 60)


def timer_worker():
    while True:
        apply_setting()
        time.sleep(1)


def force_worker(on, period):
    global FORCE_HEATING
    global FORCE_NOT_HEATING
    FORCE_HEATING = True if on else False
    FORCE_NOT_HEATING = not FORCE_HEATING
    time.sleep(period * 60)
    FORCE_HEATING = False
    FORCE_NOT_HEATING = False


def forcer(on, period):
    weather_thread = threading.Thread(target=force_worker, args=[on, period])
    weather_thread.start()


def apply_setting():
    global HEATING
    global current_humidity
    global current_temperature
    global current_target_temperature
    print("CURRENT: " + str(current_temperature))
    now = datetime.datetime.now()

    desired_temp = TIMER_SETTINGS[now.strftime("%A")][now.hour][int(now.minute / 15)]

    print("DESIRED_TEMP: %d" % desired_temp)
    if current_temperature <= desired_temp - THRESHOLD:
        if not HEATING:
            HEATING = True
            print("HEATING: %d" % HEATING)
    else:
        if current_temperature >= desired_temp + THRESHOLD:
            if HEATING:
                HEATING = False
                print("HEATING: %d" % HEATING)
    # FORCE overrides all of the above
    if FORCE_HEATING:
        HEATING = True
    if FORCE_NOT_HEATING:
        HEATING = False
    (HEATING_RELAY.on(), HEATING_RELAY.turn_led_on()) if HEATING \
        else (HEATING_RELAY.off(), HEATING_RELAY.turn_led_off())


# ("Monday", 10, 0, 11, 45, 24)
def change_setting(day, start_hour, start_min, end_hour, end_min, desired_temp):
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
        print("Wrong day")
    except IndexError:
        logging.error("Wrong hour or minute: h: %d, min: %d, h:%d, min: %d" % (start_hour, start_min, end_hour, end_min))
        print("wrong minute or hour,min has to be: 0, 15, 30, 45 hour 0-23")
    save_heating_settings(it=TIMER_SETTINGS)
    return


def db_worker():
    global HEATING
    global current_humidity
    global current_temperature
    """runs in own thread to log data"""
    while True:
        results = q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            try:
                humidities[results['location']].appendleft(results['humidity'])
            except KeyError:
                humidities[results['location']] = collections.deque(5 * [results['humidity']], 5)
            print(humidities)
            try:
                temperatures[results['location']].appendleft(results['temp'])
            except KeyError:
                temperatures[results['location']] = collections.deque(5 * [results['temp']], 5)
            print(temperatures)
            # TODO: only record if its changed
            current_humidity = results['humidity']
            current_temperature = results['temp']

            print(normalise_dict(temperatures))
            print(normalise_dict(humidities))
            results['heating'] = HEATING
            if not DEV:
                db.put(results)


def run():
    load_heating_settings()
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
