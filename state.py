from forceheating import ForceHeating
import collections
import requests
import time
import datetime
import pickle

from settings import TOLERANCE, MAIN_SENSOR, WEATHER_QUERY, JSON_HEADER, THRESHOLD, HEATING_SETTINGS_FILE
from credentials import API_KEY, CITY_ID


class State:
    # Todo: def refresh_state to refresh it with data received from the queue
    # db worker gets it, passes it here and writes CurrentState to db

    def __init__(self):
        self.humidities = {}
        self.temperatures = {}
        self.weather_data = {}
        self.TIMER_SETTINGS = self.load_heating_settings_from_file()
        self.HEATING = False
        self.FORCE_HEATING = ForceHeating.UNSET
        self.refresh_weather_data()

    @property
    def humidity(self):
        try:
            humidity = self._normalise_dict(self.humidities[MAIN_SENSOR])
        except KeyError:
            humidity = 0
        return humidity

    @property
    def temperature(self):
        try:
            temperature = self._normalise_dict(self.temperatures[MAIN_SENSOR])
        except KeyError:
            temperature = 0
        return temperature

    @property
    def is_HEATING(self):
    # logging.debug("current temperature: %d" % State.temperature)
        now = datetime.datetime.now()

        desired_temp = self.TIMER_SETTINGS[now.strftime("%A")][now.hour][int(now.minute / 15)]
      #  logging.debug("desired temperature: %d" % desired_temp)
        if self.FORCE_HEATING.value is not ForceHeating.UNSET:
            self.HEATING = self.FORCE_HEATING.value
        else:
            if self.temperature <= desired_temp - THRESHOLD:
                if not self.HEATING:
                    self.HEATING = True
                    return True
              #      logging.debug("HEATING: %s" % str(self.HEATING))
            else:
                if self.temperature >= desired_temp + THRESHOLD:
                    if self.HEATING:
                        self.HEATING = False
                        return False
                        #logging.debug("HEATING: %s" % str(State.HEATING))

    @staticmethod
    def _normalise_list(values_list, tolerance=TOLERANCE):
        # smoothing outliers (ignore readings outside tolerance)
        if abs(values_list[0] - values_list[1]) > tolerance and abs(values_list[1] - values_list[2]) > tolerance:
            values_list[1] = values_list[0]
        return sum(values_list) / 5

    def _normalise_dict(self, target_dict):
        norm_dict = {}
        for k, v in target_dict.items():
            norm_dict[k] = self._normalise_list(v)
        return norm_dict

    def add_reading(self, location, humidity, temperature):
        try:
            self.humidities[location].appendleft(humidity)
        except KeyError:
            self.humidities[location] = collections.deque(5 * [humidity], 5)
        try:
            self.temperatures[location].appendleft(temperature)
        except KeyError:
            self.temperatures[location] = collections.deque(5 * [temperature], 5)

    def refresh_weather_data(self):
        query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
        try:
            self.weather_data = requests.get(query, headers=JSON_HEADER).json()
        except:
        #     logging.error("Could not get data from %s" % query)
        # logging.debug("WeatherAPI temp: %d" % State.weather_data['main']['temp'])
        # logging.debug("WeatherAPI humidity: %d" % State.weather_data['main']['humidity'])
            self.weather_data = {}

    # Format: ("Monday", 10, 0, 11, 45, 24)
    def change_setting(self, day, start_hour, start_min, end_hour, end_min, desired_temp):
        #logging.debug("changing setting: %s - %d:%d -> %d:%d = %dC" % (
        #day, start_hour, start_min, end_hour, end_min, desired_temp))
        hour = start_hour
        minute = start_min
        try:
            while True:
                if minute == 60:
                    minute = 0
                    hour += 1
                State.TIMER_SETTINGS[day][hour][int(minute / 15)] = desired_temp
                minute += 15
                if hour == end_hour and minute == end_min:
                    break
        except KeyError:
         #   logging.error("Wrong day: %s" % day)
            pass
        except IndexError:
            pass #logging.error(
                #"Wrong hour or minute: h: %d, min: %d, h:%d, min: %d" % (start_hour, start_min, end_hour, end_min))
        self._save_heating_settings(setting=State.TIMER_SETTINGS)
        return

    def load_heating_settings_from_file(self, setting_file=HEATING_SETTINGS_FILE):
        try:
            with open(setting_file, 'rb') as handle:
                settings = pickle.load(handle)
        except FileNotFoundError or IOError:
           # logging.error("error while loading timer settings from: %s" % setting_file)
            settings = self.load_default_heating_settings()
        #logging.info("heating settings loaded from %s" % setting_file)
        return settings

    @staticmethod
    def load_default_heating_settings():
        #logging.info("fallback to default settings")
        try:
            from timer_settings import DEFAULT_TIMER_SETTINGS
            return DEFAULT_TIMER_SETTINGS
        except ImportError:
            pass
         #   logging.error("couldn't import timer_settings module, can't load default timer settings")
        return {}

    @staticmethod
    def _save_heating_settings(setting, setting_file=HEATING_SETTINGS_FILE):
        try:
            with open(setting_file, 'wb') as file:
                pickle.dump(setting, file, protocol=pickle.HIGHEST_PROTOCOL)
        except FileNotFoundError or IOError:
            #logging.error("error while saving timer settings to: %s" % setting_file)
            return False
        #logging.info("heating settings saved to %s" % setting_file)
        return True