#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
from multiprocessing import Pool, Queue, cpu_count
import threading
from python_version.mqtt.db import *
from python_version.mqtt.settings import *
from python_version.mqtt.timer import timer_worker


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


def db_worker():
    """runs in own thread to log data"""
    while True:
        results = q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            db.put(results)


if __name__ == '__main__':
    db = DatabaseManager()
    q = Queue()
    client = mqtt.Client()
    client.connect(SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT)

    client.on_connect = on_connect
    client.on_message = on_message

    db_thread = threading.Thread(target=db_worker)
    db_thread.start()

    timer_thread = threading.Thread(target=timer_worker)
    timer_thread.start()

    client.loop_forever()

