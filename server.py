#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import datetime
from multiprocessing import Queue
import threading

from db import *
from settings import *
from timer_settings import TIMER_SETTINGS
import mock_relay as HEATING_RELAY


global HEATING
global current_humidity
global current_temperature


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


def timer_worker():
    while True:
        apply_setting()
        time.sleep(1)


def apply_setting():
    global HEATING
    global current_humidity
    global current_temperature
    print("CURRENT: " + str(current_temperature))
    now = datetime.datetime.now()
    # TODO: replace dict with DB
    # TODO: add settings to desired temp for timeslots
    day_settings = TIMER_SETTINGS[now.strftime("%A")]
    for setting in day_settings:
        if setting['start_hour'] <= now.hour <= setting['end_hour'] and setting['start_min'] <= now.minute <= setting['end_min']:
            print("DESIRED_TEMP: " + str(setting['desired_temp']))
            if current_temperature <= setting['desired_temp'] - THRESHOLD:
                if not HEATING:
                    HEATING = True
                    print("HEATING: " + str(HEATING))
            else:
                if current_temperature >= setting['desired_temp'] + THRESHOLD:
                    if HEATING:
                        HEATING = False
                        print("HEATING: " + str(HEATING))
    (HEATING_RELAY.on(), HEATING_RELAY.turn_led_on()) if HEATING else (HEATING_RELAY.off(), HEATING_RELAY.turn_led_off())


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
            current_humidity = results['humidity']
            current_temperature = results['temp']
            results['heating'] = HEATING
            db.put(results)


if __name__ == '__main__':
    current_temperature = 0
    current_humidity = 0

    db = DatabaseManager()
    #q = Queue()
    client = mqtt.Client()
    client.connect(SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT)

    client.on_connect = on_connect
    client.on_message = on_message

    db_thread = threading.Thread(target=db_worker)
    db_thread.start()

    timer_thread = threading.Thread(target=timer_worker)
    timer_thread.start()

    client.loop_forever()

