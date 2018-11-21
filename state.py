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
        return {"humidity": self.get_humidity(),
                "temperature": self.get_temperature(),
                "heating": self.is_HEATING,
                "desired_temperature": self.desired_temperature,
                "outside_temp": self.temperature_out,
                "outside_humidity": self.humidity_out,
                "timestamp": str(time.time()),
                "force_heating": self.force_heating.value
                }

    def __repr__(self):
        data = self.get_json_repr()
        return repr(data)

