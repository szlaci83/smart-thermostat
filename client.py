#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from pyA20.gpio import gpio
from pyA20.gpio import port
#import RPi.GPIO as GPIO
import dht22
import time
import json

from settings import *

# https://github.com/ionutpi/DHT22-Python-library-Orange-PI/blob/master/README.md

# initialize GPIO
#gpio.setwarnings(False)
#gpio.setmode(GPIO.BCM)
PIN2 = port.PA6
gpio.init()
#gpio.cleanup()

# read data using pin 14
instance = dht22.DHT22(pin=PIN2)

client = mqtt.Client()

data = {
    'client_id': 1,
    'location': 'master_bedroom'
}

while True:
    result = instance.read()
    data['temp'] = result.temperature
    data['humidity'] = result.humidity
    #pprint(data)
    publish.single(payload=json.dumps(data), topic=TOPIC, hostname=CLIENT_HOST)
    time.sleep(5)
