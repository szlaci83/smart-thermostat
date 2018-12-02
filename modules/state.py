from helpers.forceheating import ForceHeating
import collections
import requests
import logging
import datetime
import time
import pickle
import os

from properties import WEATHER_QUERY, JSON_HEADER, HEATING_SETTING_FILE, QUEUE_SIZE, MAIN_SETTING_FILE, RESOURCE_FOLDER
from credentials import API_KEY, CITY_ID

logging.basicConfig(filename="", level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")


class State:
    def __init__(self):
        self.humidities = {}
        self.temperatures = {}
        self.weather_data = {}
        self.TIMER_SETTINGS = self.load_settings_from_file()
        self.settings = self.load_settings_from_file(setting_file=MAIN_SETTING_FILE)
        self.HEATING = False
        self.force_heating = ForceHeating.UNSET
        self.refresh_weather_data()

    def get_humidities(self):
        return self._dict_avg(self.humidities)

    def get_humidity(self, sensor_name='MAIN_SENSOR'):
        try:
            sensor = self.settings[sensor_name]
        except KeyError:
            sensor = None
        try:
            if sensor:
                humidity = self._list_avg(self.humidities[sensor])
            else:
                humidities = self.get_humidities().values()
                humidity = sum(humidities) / len(humidities)
        except (KeyError, ZeroDivisionError):
            humidity = 0
        return humidity

    def get_temperatures(self):
        return self._dict_avg(self.temperatures)

    def get_temperature(self, sensor_name='MAIN_SENSOR'):
        logging.debug("TEMPS" + str(self.temperatures))
        try:
            sensor = self.settings[sensor_name]
        except KeyError:
            sensor = None
        try:
            if sensor:
                temperature = self._list_avg(self.temperatures[sensor])
            else:
                temperatures = self.get_temperatures().values()
                temperature = sum(temperatures) / len(temperatures)
        except (KeyError, ZeroDivisionError):
            temperature = 0
        return temperature

    def get_main_settings(self):
        return self.settings

    @property
    def humidity_out(self):
        try:
            humidity = self.weather_data['main']['humidity']
        except KeyError:
            humidity = 0
        return humidity

    @property
    def temperature_out(self):
        try:
            temperature = self.weather_data['main']['temp']
        except KeyError:
            temperature = 0
        return temperature

    @property
    def desired_temperature(self):
        desired_temp = self.get_setting_for_time()
        logging.debug("desired temp: %d" % desired_temp)
        return desired_temp

    def get_setting_for_time(self, day=None, hour=None, minute=None, target_date=datetime.datetime.now()):
        if day is None:
            day, hour, minute = target_date.strftime("%A"), target_date.hour, target_date.minute
        result = self.TIMER_SETTINGS[day]
        if hour is not None:
            result = result[int(hour)]
            if minute is not None:
                result = result[int(int(minute) / 15)]
        return result

    @property
    def is_HEATING(self):
        logging.debug("current temp: %s" % self.get_temperature())

        if self.force_heating.value is not None:
            logging.debug("forcing %s: " % self.force_heating.value)
            return self.force_heating.value
        else:
            logging.debug("checking heating")
            if self.get_temperature() <= self.desired_temperature - self.settings['HEAT_THRESHOLD']:
                logging.debug("HEATING: %s" % True)
                return True
            else:
                if self.get_temperature() >= self.desired_temperature + self.settings['HEAT_THRESHOLD']:
                    logging.debug("HEATING: %s" % False)
                    return False

    @staticmethod
    def _list_avg(values):
        values_list = list(values)
        return sum(values_list) / len(values_list)

    def _dict_avg(self, target_dict):
        norm_dict = {}
        for k, v in target_dict.items():
            norm_dict[k] = self._list_avg(v)
        return norm_dict

    @staticmethod
    def is_outlier(elements, value, tolerance):
        element_list = list(elements)
        return value - element_list[0] > tolerance

    def add_reading(self, location, humidity, temperature):
        try:
            if not self.is_outlier(self.humidities[location], humidity, self.settings['HUM_TOLERANCE']):
                self.humidities[location].appendleft(humidity)
        except KeyError:
            self.humidities[location] = collections.deque(QUEUE_SIZE * [humidity], QUEUE_SIZE)
        try:
            if not self.is_outlier(self.temperatures[location], temperature, self.settings['TEMP_TOLERANCE']):
                self.temperatures[location].appendleft(temperature)
        except KeyError:
            self.temperatures[location] = collections.deque(QUEUE_SIZE * [temperature], QUEUE_SIZE)
        logging.debug(str(self.temperatures))
        logging.debug(str(self.humidities))

    def refresh_weather_data(self):
        query = WEATHER_QUERY % (str(CITY_ID), API_KEY)
        try:
            self.weather_data = requests.get(query, headers=JSON_HEADER).json()
        except:
            logging.error("Could not get data from %s" % query)
            self.weather_data = {}
        logging.debug("WeatherAPI temp: %d" % self.weather_data['main']['temp'])
        logging.debug("WeatherAPI humidity: %d" % self.weather_data['main']['humidity'])

    def change_heating_setting(self, day, start_hour, start_min, end_hour, end_min, desired_temp):
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
        self._save_settings(setting=self.TIMER_SETTINGS)
        return

    def change_main_setting(self, settings):
        self._save_settings(settings, setting_file=MAIN_SETTING_FILE)
        self.settings = settings
        return

    def load_settings_from_file(self, setting_file=HEATING_SETTING_FILE, resource_folder=RESOURCE_FOLDER):
        try:
            with open(os.path.join(RESOURCE_FOLDER, setting_file), 'rb') as handle:
                settings = pickle.load(handle)
        except FileNotFoundError or IOError:
            logging.error("error while loading settings %s/%s" % (resource_folder, setting_file))
            if setting_file == HEATING_SETTING_FILE:
                settings = self.load_default_timer_settings(os.path.join("resources", "main_settings"))
            if setting_file == MAIN_SETTING_FILE:
                settings = self.load_default_main_settings()
        logging.info("settings loaded from %s/%s" % (resource_folder, setting_file))
        return settings

    @staticmethod
    def load_default_timer_settings():
        logging.info("fallback to default settings")
        try:
            from helpers.timer_settings import DEFAULT_TIMER_SETTINGS
            return DEFAULT_TIMER_SETTINGS
        except ImportError:
            pass
            logging.error("couldn't import timer_settings module, can't load default timer settings")
        return {}

    @staticmethod
    def load_default_main_settings():
        null_setting = {'THRESHOLD': 0,
                         'MAIN_SENSOR': None}
        logging.info("fallback to default settings")
        try:
            from helpers.main_settings import MAIN_SETTINGS
            return MAIN_SETTINGS
        except ImportError:
            pass
            logging.error("couldn't import timer_settings module, can't load default timer settings")
        return null_setting

    @staticmethod
    def _save_settings(setting, setting_file=HEATING_SETTING_FILE, resource_folder=RESOURCE_FOLDER):
        try:
            with open(setting_file, 'wb') as file:
                pickle.dump(setting, os.path.join(resource_folder, setting_file), protocol=pickle.HIGHEST_PROTOCOL)
        except FileNotFoundError or IOError:
            logging.error("error while saving timer settings to: %s/%s" % (RESOURCE_FOLDER, setting_file))
            return False
        logging.info("heating settings saved to %s" % setting_file)
        return True

    def __cmp__(self, other):
        return self.humidity_out == other.humidity_out and \
               self.temperature_out == other.temperature_out and \
               self.desired_temperature == other.desired_temperature and \
               self.get_humidity() == other.get_humidity() and \
               self.get_temperature() == other.get_temperature() and \
               self.is_HEATING == other.is_HEATING and \
               self.force_heating == other.force_heating

    def __eq__(self, other):
        return self.__cmp__(other)

    def __ne__(self, other):
        return self.humidity_out != other.humidity_out or \
               self.temperature_out != other.temperature_out or \
               self.desired_temperature != other.desired_temperature or \
               self.get_humidity() != other.get_humidity() or \
               self.get_temperature() != other.get_temperature() or \
               self.is_HEATING != other.is_HEATING or \
               self.force_heating != other.force_heating

    def get_json_repr(self):
        return {"humidities": self.get_humidities(),
                "temperatures": self.get_temperatures(),
                "humidity": self.get_humidity(),
                "temperature": self.get_temperature(),
                "heating": self.is_HEATING,
                "desired_temperature": self.desired_temperature,
                "outside_temp": self.temperature_out,
                "outside_humidity": self.humidity_out,
                "timestamp": str(time.time()),
                "force_heating": self.force_heating.value
                }

    def get_db_repr(self):
        return {"humidities": str(self.get_humidities()),
                "temperatures": str(self.get_temperatures()),
                "humidity": str(self.get_humidity()),
                "temperature": str(self.get_temperature()),
                "heating": 1 if self.is_HEATING else 0,
                "desired_temperature": str(self.desired_temperature),
                "outside_temp": str(self.temperature_out),
                "outside_humidity": str(self.humidity_out),
                "timestamp": str(time.time()),
                "force_heating": str(self.force_heating.value)
                }

    def __repr__(self):
        data = self.get_json_repr()
        return repr(data)

