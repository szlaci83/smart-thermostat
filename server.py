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
#from timer_settings import TIMER_SETTINGS

import mock_relay as HEATING_RELAY

db = DatabaseManager()
q = Queue()

humidities = {}
temperatures = {}

weather_data = {}
HEATING = False
current_humidity = 0
current_temperature = 0
current_target_temperature = 0

banner = "____ _  _ ____ ____ ___    ___ _  _ ____ ____ _  _ ____ ____ ___ ____ ___    \n" \
         "[__  |\/| |__| |__/  |  __  |  |__| |___ |__/ |\/| |  | [__   |  |__|  |     \n" \
         "___] |  | |  | |  \  |      |  |  | |___ |  \ |  | |__| ___]  |  |  |  |  0.1\n"

tolerance = 1

TIMER_SETTINGS = {}


def load_heating_settings(setting_file=HEATING_SETTINGS):
    global TIMER_SETTINGS
    with open(setting_file, 'rb') as handle:
        TIMER_SETTINGS = pickle.load(handle)


def save_heating_settings(it=TIMER_SETTINGS, filename=HEATING_SETTINGS):
    with open(filename + '.pickle', 'wb') as file:
        pickle.dump(it,  file, protocol=pickle.HIGHEST_PROTOCOL)
    return


def normalise_list(values_list):
    # smoothing outliers (ignore readings outside tolerance)
    if abs(values_list[0] - values_list[1]) > tolerance and abs(values_list[1] - values_list[2]) > tolerance:
        values_list[1] = values_list[0]
    return sum(values_list) / 5


def normalise_dict(target_dict):
    print(type(target_dict))
    norm_dict = {}
    for k, v in target_dict.items():
        norm_dict[k] = normalise_list(v)
    return norm_dict


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        data['epoch'] = str(time.time())
        q.put(data)
    except Exception as e:
        print(e)
    print(data)


def weather_worker():
    global weather_data
    weather_data = requests.get(WEATHER_QUERY % (str(CITY_ID), API_KEY), headers=JSON_HEADER).json()
    print(weather_data['main']['temp'])
    print(weather_data['main']['humidity'])
    pprint(weather_data)
    # enough sleep for free tier usage
    time.sleep(11 * 60)


def timer_worker():
    while True:
        apply_setting()
        time.sleep(1)


def apply_setting():
    global HEATING
    global current_humidity
    global current_temperature
    global current_target_temperature
    print("CURRENT: " + str(current_temperature))
    now = datetime.datetime.now()

    # TODO: add settings to desired temp for timeslots

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
    (HEATING_RELAY.on(), HEATING_RELAY.turn_led_on()) if HEATING \
        else (HEATING_RELAY.off(), HEATING_RELAY.turn_led_off())


# ("Monday", 10, 0, 11, 45, 24)
def change_setting(day, start_hour, start_min, end_hour, end_min, desired_temp):
    hour = start_hour
    minute = start_min
    try:
        while True:
            if minute == 60:
                minute = 0
                hour = hour + 1
            TIMER_SETTINGS[day][hour][int(minute / 15)] = desired_temp
            minute += 15
            if hour == end_hour and minute == end_min:
                break
    except KeyError:
        print("Wrong day")
    except IndexError:
        print("wrong minute or hour,min has to be: 0, 15, 30, 45 hour 0-23")
    save_heating_settings()
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
            current_humidity = results['humidity']
            current_temperature = results['temp']

            print(normalise_dict(temperatures))
            print(normalise_dict(humidities))
            results['heating'] = HEATING
            db.put(results)


def run():
    print(banner)

    load_heating_settings()
    client = mqtt.Client()
    client.connect(SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT)

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
    run()
