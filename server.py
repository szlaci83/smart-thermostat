#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import datetime
import requests
import collections
from pprint import pprint

import threading

from db import *
from settings import *
from credentials import *
from utils import *
from current_state import CurrentState
from forceheating import ForceHeating

import mock_relay as HEATING_RELAY
import logging

db = DatabaseManager()


def on_connect(client, userdata, flags, rc):
    logging.debug("Connected with result code %d" %rc)
    client.subscribe(TOPIC)
    logging.debug("Subscribed to topic %s" % TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        data['epoch'] = str(time.time())
        CurrentState.q.put(data)
    except Exception as e:
        logging.error(e)
    logging.debug("received data: %s" % str(data))


def weather_worker():
    query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
    try:
        CurrentState.weather_data = requests.get(query, headers=JSON_HEADER).json()
    except:
        logging.error("Could not get data from %s" % query)
    logging.debug("WeatherAPI temp: %d" % CurrentState.weather_data['main']['temp'])
    logging.debug("WeatherAPI humidity: %d" % CurrentState.weather_data['main']['humidity'])
    #pprint(weather_data)
    # enough sleep for free tier usage
    time.sleep(10 * 60 + 1)


def timer_worker():
    while True:
        apply_setting()
        time.sleep(TIMER_REFRESH)


def force_worker(switch_setting, period):
    logging.debug("Forcing %s for %s minutes." % (str(switch_setting), period))
    CurrentState.FORCE_HEATING = switch_setting
    time.sleep(period * 60)
    logging.debug("Force over")
    CurrentState.FORCE_HEATING = ForceHeating.UNSET


def forced_switch(switch_setting, period):
    weather_thread = threading.Thread(target=force_worker, args=[switch_setting, period])
    weather_thread.start()


def apply_setting():
    logging.debug("current temperature: %d" % CurrentState.temperature)
    now = datetime.datetime.now()

    desired_temp = CurrentState.TIMER_SETTINGS[now.strftime("%A")][now.hour][int(now.minute / 15)]
    logging.debug("desired temperature: %d" % desired_temp)
    if CurrentState.FORCE_HEATING.value is not ForceHeating.UNSET:
        CurrentState.HEATING = CurrentState.FORCE_HEATING.value
    else:
        if CurrentState.temperature <= desired_temp - THRESHOLD:
            if not CurrentState.HEATING:
                CurrentState.HEATING = True
                logging.debug("HEATING: %s" % str(CurrentState.HEATING))
        else:
            if CurrentState.temperature >= desired_temp + THRESHOLD:
                if CurrentState.HEATING:
                    CurrentState.HEATING = False
                    logging.debug("HEATING: %s" % str(CurrentState.HEATING))

    HEATING_RELAY.on(led=True) if CurrentState.HEATING else HEATING_RELAY.off(led=True)


# Format: ("Monday", 10, 0, 11, 45, 24)
def change_setting(day, start_hour, start_min, end_hour, end_min, desired_temp):
    logging.debug("changing setting: %s - %d:%d -> %d:%d = %dC" % (day, start_hour, start_min, end_hour, end_min, desired_temp))
    hour = start_hour
    minute = start_min
    try:
        while True:
            if minute == 60:
                minute = 0
                hour += 1
            CurrentState.TIMER_SETTINGS[day][hour][int(minute / 15)] = desired_temp
            minute += 15
            if hour == end_hour and minute == end_min:
                break
    except KeyError:
        logging.error("Wrong day: %s" % day)
    except IndexError:
        logging.error("Wrong hour or minute: h: %d, min: %d, h:%d, min: %d" % (start_hour, start_min, end_hour, end_min))
    save_heating_settings(setting=CurrentState.TIMER_SETTINGS)
    return


def db_worker():
    while True:
        results = CurrentState.q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            try:
                CurrentState.humidities[results['location']].appendleft(results['humidity'])
            except KeyError:
                CurrentState.humidities[results['location']] = collections.deque(5 * [results['humidity']], 5)
            try:
                CurrentState.temperatures[results['location']].appendleft(results['temp'])
            except KeyError:
                CurrentState.temperatures[results['location']] = collections.deque(5 * [results['temp']], 5)

            norm_temp = normalise_dict(CurrentState.temperatures)
            norm_hum = normalise_dict(CurrentState.humidities)

            logging.debug(norm_temp)
            logging.debug(norm_hum)

            temperature_reading = norm_temp[MAIN_SENSOR]
            humidity_reading = norm_hum[MAIN_SENSOR]

            results['heating'] = HEATING
            if not DEV:
                if temperature_reading != CurrentState.temperature or humidity_reading != CurrentState.humidity:
                    db.put(results)
            CurrentState.temperature = temperature_reading
            CurrentState.humidity = humidity_reading


def run():
    CurrentState.TIMER_SETTINGS = load_heating_settings_from_file()
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
