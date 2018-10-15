#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
from random import *
import paho.mqtt.publish as publish
import json



'''
 Simulation of an IOT device publishing data randomly on MQTT protocol
'''

client = mqtt.Client()
#client.connect("localhost", 1883, 60)

data = {
    'client_id': 1
}

while True:
    data['temp'] = randint(1, 24)
    data['humidity'] = randint(1, 99)
    publish.single(payload=json.dumps(data), topic="topic/temperature", hostname="localhost", client_id="112")
    #client.publish("topic/temperature", temp, )
    time.sleep(randint(1, 10))
