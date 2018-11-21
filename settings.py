import logging

# ENV
DEV = True

# IMAGE LOCATION: https://openweathermap.org/img/w/04n.png
# heat index calculation: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
# dew point calc : 

# SERVER
SERVER_HOST = "localhost"
SERVER_MQTT_PORT = 1883
SERVER_TIMEOUT = 60

# CLIENT
CLIENT_HOST = "localhost"
CLIENT_MQTT_PORT = 1883
CLIENT_TIMEOUT = 60


# Logging
CLIENT_LOGS = "logs/client.log"
LOGGING_LEVEL = logging.DEBUG

# SERVER_LOG = "logs/server.log"
# log to console:
SERVER_LOG = ""

TOPIC = "topic/temperature"

# DB
TABLE_NAME = 'temp_test'
MOCK_FILE = 'db.csv'
HEATING_SETTINGS_FILE = 'timer.pickle'

# REST API
HTTP_OK = 200
SERVER_REST_PORT = 8887


# Heating
HEATING = False
THRESHOLD = 0.8
TIMER_REFRESH = 5
MAIN_SENSOR = 'mock_location1'
QUEUE_SIZE = 5  # queue size for smoothing

# 1 Hour (it will be multiplied by 60 again)
FORCE_ON_DEFAULT = 1 * 60
TOLERANCE = 1

WEATHER_QUERY = "http://api.openweathermap.org/data/2.5/weather?units=metric&id=%s&APPID=%s"
JSON_HEADER = {'content-type': 'application/json'}
WEATHER_REFRESH = 10 * 60 + 1

BANNER = "____ _  _ ____ ____ ___    ___ _  _ ____ ____ _  _ ____ ____ ___ ____ ___    \n" \
             "[__  |\/| |__| |__/  |  __  |  |__| |___ |__/ |\/| |  | [__   |  |__|  |     \n" \
             "___] |  | |  | |  \  |      |  |  | |___ |  \ |  | |__| ___]  |  |  |  |  0.1\n"
