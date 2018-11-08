import logging

# ENV
DEV = True


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
#SERVER_LOG = "logs/server.log"
LOGGING_LEVEL = logging.DEBUG
SERVER_LOG = ""

TOPIC = "topic/temperature"

# DB
TABLE_NAME = 'temp_test'
MOCK_FILE = 'db.csv'
HEATING_SETTINGS = 'timer.pickle'

# REST API
HTTP_OK = 200
SERVER_REST_PORT = 8888


# Heating
HEATING = False
THRESHOLD = 0.8
FORCE_ON_DEFAULT = 1 * 60 #1 Hour (it will be multiplied by 60 again)
TOLERANCE = 1

WEATHER_QUERY = "http://api.openweathermap.org/data/2.5/weather?units=metric&id=%s&APPID=%s"
JSON_HEADER = {'content-type': 'application/json'}

BANNER = "____ _  _ ____ ____ ___    ___ _  _ ____ ____ _  _ ____ ____ ___ ____ ___    \n" \
             "[__  |\/| |__| |__/  |  __  |  |__| |___ |__/ |\/| |  | [__   |  |__|  |     \n" \
             "___] |  | |  | |  \  |      |  |  | |___ |  \ |  | |__| ___]  |  |  |  |  0.1\n"
