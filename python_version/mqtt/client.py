#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import json
from pprint import pprint
from random import *
import paho.mqtt.publish as publish
from python_version.mqtt.settings import *


'''
 Simulation of an IOT device publishing data randomly on MQTT protocol
'''

client = mqtt.Client()

data = {
    'client_id': 464,
    'location': 'living_room'
}

while True:
    data['temp'] = randint(20, 28)
    data['humidity'] = randint(1, 99)
    pprint(data)
    publish.single(payload=json.dumps(data), topic=TOPIC, hostname=CLIENT_HOST)
    time.sleep(randint(1, 10))
