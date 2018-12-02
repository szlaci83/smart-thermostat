#!/usr/bin/env python
import os
import sys

if not os.getegid() == 0:
    sys.exit('Script must be run as root')

from pyA20.gpio import gpio
from pyA20.gpio import connector
from helpers.relay_status import RelayStatus


global STATUS
STATUS = RelayStatus.OFF

__led = connector.LEDp2
__HEATING_PIN = __led # TODO: specify the heating PIN, it will switch the inbuilt LED for now.


gpio.init()
gpio.setcfg(__led, gpio.OUTPUT)
gpio.setcfg(__HEATING_PIN, gpio.OUTPUT)


def off(pin=__HEATING_PIN, led=False):
    global STATUS
    STATUS = RelayStatus.OFF.value
    gpio.output(pin, 0)
    if led:
        turn_led_on()


def on(pin=__HEATING_PIN, led=False):
    global STATUS
    STATUS = RelayStatus.ON.value
    gpio.output(pin, 1)
    if led:
        turn_led_on()


def get_status():
    return STATUS


def turn_led_on():
    on(__led)


def turn_led_off():
    off(__led)