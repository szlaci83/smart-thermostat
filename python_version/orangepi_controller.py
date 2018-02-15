#!/usr/bin/env python
import os
import sys

if not os.getegid() == 0:
    sys.exit('Script must be run as root')

from pyA20.gpio import gpio
from pyA20.gpio import port

led = port.PA12

gpio.init()
gpio.setcfg(led, gpio.OUTPUT)

def turn_off(pin):
    gpio.output(pin, 0)

def turn_on(pin):
    gpio.output(pin, 1)

def turn_led_on():
    turn_on(led)

def turn_led_off():
    turn_off(led)
