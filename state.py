from forceheating import ForceHeating
import collections
import requests
import logging
import datetime
import time
import pickle

from settings import TOLERANCE, MAIN_SENSOR, WEATHER_QUERY, JSON_HEADER, THRESHOLD, HEATING_SETTINGS_FILE, QUEUE_SIZE
from credentials import API_KEY, CITY_ID

logging.basicConfig(filename="", level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")


class State:
    def __init__(self):
        self.humidities = {}
        self.temperatures = {}
        self.weather_data = {}
        self.TIMER_SETTINGS = self.load_heating_settings_from_file()
        self.HEATING = False
        self.force_heating = ForceHeating.UNSET
        self.refresh_weather_data()

    def get_humidity(self, sensor=MAIN_SENSOR):
        try:
            humidity = self._normalise_list(self.humidities[sensor]) if sensor else self._normalise_dict(self.humidities)
        except KeyError:
            humidity = 0
        return humidity

    def get_temperature(self, sensor=MAIN_SENSOR):
        try:
            temperature = self._normalise_list(self.temperatures[sensor]) if sensor else self._normalise_dict(self.temperatures)
        except KeyError:
            temperature = 0
        return temperature

    @property
    def get_humidity_out(self):
        try:
            humidity = self.weather_data['main']['humidity']
        except KeyError:
            humidity = 0
        return humidity

    @property
    def get_temperature_out(self):
        try:
            temperature = self.weather_data['main']['temp']
        except KeyError:
            temperature = 0
        return temperature

    @property
    def desired_temperature(self):
        now = datetime.datetime.now()

        desired_temp = self.TIMER_SETTINGS[now.strftime("%A")][now.hour][int(now.minute / 15)]
        logging.debug("desired temp: %d" % desired_temp)
        return desired_temp

    @property
    def is_HEATING(self):
        logging.debug("current temp: %d" % self.get_temperature())

        if self.force_heating.value is not None:
            logging.debug("forcing %s: " % self.force_heating.value)
            return self.force_heating.value
        else:
            logging.debug("checking heating")
            if self.get_temperature() <= self.desired_temperature - THRESHOLD:
                logging.debug("HEATING: %s" % True)
                return True
            else:
                if self.get_temperature() >= self.desired_temperature + THRESHOLD:
                    logging.debug("HEATING: %s" % False)
                    return False


    @staticmethod
    def _normalise_list(values_list, tolerance=TOLERANCE):
        # smoothing outliers (ignore readings outside tolerance)
        if abs(values_list[0] - values_list[1]) > tolerance and abs(values_list[1] - values_list[2]) > tolerance:
            values_list[1] = values_list[0]
        return sum(values_list) / QUEUE_SIZE

    def _normalise_dict(self, target_dict):
        norm_dict = {}
        for k, v in target_dict.items():
            norm_dict[k] = self._normalise_list(v)
        return norm_dict

    def add_reading(self, location, humidity, temperature):
        try:
            self.humidities[location].appendleft(humidity)
        except KeyError:
            self.humidities[location] = collections.deque(QUEUE_SIZE * [humidity], QUEUE_SIZE)
        try:
            self.temperatures[location].appendleft(temperature)
        except KeyError:
            self.temperatures[location] = collections.deque(QUEUE_SIZE * [temperature], QUEUE_SIZE)

    def refresh_weather_data(self):
        query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
        try:
            self.weather_data = requests.get(query, headers=JSON_HEADER).json()
        except:
             logging.error("Could not get data from %s" % query)
             self.weather_data = {}
        logging.debug("WeatherAPI temp: %d" % self.weather_data['main']['temp'])
        logging.debug("WeatherAPI humidity: %d" % self.weather_data['main']['humidity'])

    # Format: ("Monday", 10, 0, 11, 45, 24)
    def change_setting(self, day, start_hour, start_min, end_hour, end_min, desired_temp):
        logging.debug("changing setting: %s - %d:%d -> %d:%d = %dC" % (
        day, start_hour, start_min, end_hour, end_min, desired_temp))
        hour = start_hour
        minute = start_min
        try:
            while True:
                if minute == 60:
                    minute = 0
                    hour += 1
                self.TIMER_SETTINGS[day][hour][int(minute / 15)] = desired_temp
                minute += 15
                if hour == end_hour and minute == end_min:
                    break
        except KeyError:
            logging.error("Wrong day: %s" % day)
            pass
        except IndexError:
            logging.error(
                "Wrong hour or minute: h: %d, min: %d, h:%d, min: %d" % (start_hour, start_min, end_hour, end_min))
        self._save_heating_settings(setting=self.TIMER_SETTINGS)
        return

    def load_heating_settings_from_file(self, setting_file=HEATING_SETTINGS_FILE):
        try:
            with open(setting_file, 'rb') as handle:
                settings = pickle.load(handle)
        except FileNotFoundError or IOError:
            logging.error("error while loading timer settings from: %s" % setting_file)
            settings = self.load_default_heating_settings()
        logging.info("heating settings loaded from %s" % setting_file)
        return settings

    @staticmethod
    def load_default_heating_settings():
        logging.info("fallback to default settings")
        try:
            from timer_settings import DEFAULT_TIMER_SETTINGS
            return DEFAULT_TIMER_SETTINGS
        except ImportError:
            pass
            logging.error("couldn't import timer_settings module, can't load default timer settings")
        return {}

    @staticmethod
    def _save_heating_settings(setting, setting_file=HEATING_SETTINGS_FILE):
        try:
            with open(setting_file, 'wb') as file:
                pickle.dump(setting, file, protocol=pickle.HIGHEST_PROTOCOL)
        except FileNotFoundError or IOError:
            logging.error("error while saving timer settings to: %s" % setting_file)
            return False
        logging.info("heating settings saved to %s" % setting_file)
        return True

    def __repr__(self):
        data = {"humidity": self.get_humidity(),
                "temperature": self.get_temperature(),
                "heating": self.is_HEATING,
                "desired_temperature": self.desired_temperature,
                "outside_temp": self.get_temperature_out,
                "outside_humidity": self.get_humidity_out,
                "timestamp": str(time.time()),
                "force_heating": self.force_heating.value}
        return repr(data)
