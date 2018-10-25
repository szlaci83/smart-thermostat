import datetime
import time
from python_version.mqtt.settings import *
from python_version.mqtt.timer_settings import TIMER_SETTINGS
import python_version.mqtt.mock_relay as HEATING_RELAY
'''
Setting different desired temperature values for time intervals
'''


def timer_worker():
    while True:
        _apply_setting()
        time.sleep(1)


def _apply_setting():
    global HEATING
    print("CURRENT: " + str(CURRENT_TEMP))
    now = datetime.datetime.now()
    day_settings = TIMER_SETTINGS[now.strftime("%A")]
    for setting in day_settings:
        if setting['start_hour'] <= now.hour <= setting['end_hour'] and setting['start_min'] <= now.minute <= setting['end_min']:
            print("DESIRED_TEMP: " + str(setting['desired_temp']))
            if CURRENT_TEMP <= setting['desired_temp'] - THRESHOLD:
                if not HEATING:
                    HEATING = True
                    print("HEATING: " + str(HEATING))
            else:
                if CURRENT_TEMP >= setting['desired_temp'] + THRESHOLD:
                    if HEATING:
                        HEATING = False
                        print("HEATING: " + str(HEATING))
    HEATING_RELAY.on(), HEATING_RELAY.turn_led_on() if HEATING else HEATING_RELAY.off(), HEATING_RELAY.turn_led_off()


if __name__ == '__main__':
    timer_worker()
