#!/usr/bin/env python3
import copy
import json
import threading
import time
from multiprocessing import Queue

import paho.mqtt.client as mqtt

from properties import WEATHER_REFRESH, TIMER_REFRESH, STATE_SK, STATE_PK, STATE_TABLE, TOPIC, USE_ENV, BANNER, \
    SERVER_MQTT_PORT, SERVER_HOST, SERVER_TIMEOUT, SERVER_LOG, LOGGING_LEVEL, IS_MOCK_RELAY, IS_MOCK_DB
from forceheating import ForceHeating

from state import State
from utils import *

if IS_MOCK_RELAY:
    import mock_relay as HEATING_RELAY
else:
    import relay_controller as HEATING_RELAY

if IS_MOCK_DB:
    from mock_db import DatabaseManager
else:
    from db import DatabaseManager

db = DatabaseManager()
current_state = State()
q = Queue()


def on_connect(client, userdata, flags, rc):
    logging.debug("Connected with result code %d" % rc)
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
    old_state = copy.deepcopy(current_state)
    current_state.refresh_weather_data()
    logging.debug("old state: %s" % old_state)
    logging.debug("new state: %s" % current_state)
    if old_state != current_state:
        logging.debug("saving new state: %s" % current_state)
    time.sleep(WEATHER_REFRESH)


def timer_worker():
    while True:
        apply_setting()
        time.sleep(TIMER_REFRESH)


def force_worker(switch_setting, period):
    logging.debug("Forcing %s for %s minutes." % (str(switch_setting), period))
    current_state.force_heating = switch_setting
    time.sleep(period * 60)
    logging.debug("Force over")
    current_state.force_heating = ForceHeating.UNSET


def forced_switch(switch_setting, period):
    force_thread = threading.Thread(target=force_worker, args=[switch_setting, period])
    force_thread.start()


def apply_setting():
    HEATING_RELAY.on(led=True) if current_state.is_HEATING else HEATING_RELAY.off(led=True)


def reading_worker():
    while True:
        results = q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            old_state = copy.deepcopy(current_state)
            logging.debug("old state: %s" % old_state)
            location = results['location']
            current_state.add_reading(location, results['humidity'], results['temp'])
            if ((old_state.get_humidity(sensor_name=location) != current_state.get_humidity(sensor_name=location)) or
                    (old_state.get_temperature(sensor_name=location) != current_state.get_temperature(sensor_name=location))):
                results['heating'] = current_state.is_HEATING
                if not USE_ENV == "dev":
                    db.put(table_name=location, data=results)
            logging.debug("current state: %s" % current_state)
            if old_state != current_state:
                logging.debug("saving new state: %s" % current_state)
                if not USE_ENV == "dev":
                    db.put(table_name=STATE_TABLE, data=current_state.get_db_repr(), partition_key=STATE_PK, sort_key=STATE_SK)


def change_timer_setting(day, start_hour, start_min, end_hour, end_min, desired_temp):
    logging.debug("changing_timer_setting called")
    current_state.change_heating_setting(day, start_hour, start_min, end_hour, end_min, desired_temp)


def change_main_setting(settings):
    current_state.change_main_setting(settings)


def get_main_settings():
    return current_state.get_main_settings()


def run():
    client = mqtt.Client()
    client.connect(SERVER_HOST, SERVER_MQTT_PORT, SERVER_TIMEOUT)

    client.on_connect = on_connect
    client.on_message = on_message

    reading_thread = threading.Thread(target=reading_worker)
    reading_thread.start()

    timer_thread = threading.Thread(target=timer_worker)
    timer_thread.start()

    weather_thread = threading.Thread(target=weather_worker)
    weather_thread.start()

    client.loop_forever()


if __name__ == '__main__':
    print(BANNER)
    print("Using environment: %s" % USE_ENV)
    print("Server started see %s for details!" % SERVER_LOG)
    print("MQTT port: %d" % SERVER_MQTT_PORT)
    if SERVER_LOG and SERVER_LOG != '':
        logging.basicConfig(filename=SERVER_LOG, level=LOGGING_LEVEL, format="%(asctime)s:%(levelname)s:%(message)s")
    run()
