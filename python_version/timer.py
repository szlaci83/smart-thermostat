import datetime
import time
from python_version.mqtt.settings import *
'''
Setting different desired temperature values for time intervals
'''


def apply_setting():
    global HEATING
    print("CURRENT: " + str(CURRENT_TEMP))
    now = datetime.datetime.now()
    day_settings = HEATING_SETTINGS[DAYS[now.weekday()]]
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


if __name__ == '__main__':
    while True:
        apply_setting()
        time.sleep(1)

