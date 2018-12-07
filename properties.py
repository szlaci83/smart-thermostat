# Common app settings accross dev envs go here  (this would be an application.yml in java)
import logging
from utils import load_settings_from_yml

USE_ENV = "dev"

BANNER = "____ _  _ ____ ____ ___    ___ _  _ ____ ____ _  _ ____ ____ ___ ____ ___    \n" \
             "[__  |\/| |__| |__/  |  __  |  |__| |___ |__/ |\/| |  | [__   |  |__|  |     \n" \
             "___] |  | |  | |  \  |      |  |  | |___ |  \ |  | |__| ___]  |  |  |  |  0.1\n"

# Weather API settings
WEATHER_QUERY = "http://api.openweathermap.org/data/2.5/weather?units=metric&id=%s&APPID=%s"
JSON_HEADER = {'content-type': 'application/json'}
WEATHER_REFRESH = 10 * 60 + 1

# resources folder:
RESOURCE_FOLDER = "resources"

# Logging
CLIENT_LOGS = "logs/client.log"
LOGGING_LEVEL = logging.DEBUG

# SERVER_LOG = "logs/server.log"
# log to console:
SERVER_LOG = ""

# DB
MOCK_FILE = 'db.csv'
READING_PK = {'name': 'client_id', 'key_type': 'HASH', 'type': 'N'}
READING_SK = {'name': 'epoch', 'key_type': 'RANGE', 'type': 'S'}
STATE_TABLE = "state"
STATE_PK = {'name': 'heating', 'key_type': 'HASH', 'type': 'N'}
STATE_SK = {'name': 'timestamp', 'key_type': 'RANGE', 'type': 'S'}

# Heating
QUEUE_SIZE = 5  # queue size for smoothing
# 1 Hour (it will be multiplied by 60 again)
FORCE_ON_DEFAULT = 1 * 60
TIMER_REFRESH = 5
MAIN_SETTING_FILE = "main_settings.pickle"
HEATING_SETTING_FILE = 'timer.pickle'
HTTP_OK = 200

#------------------------------------------------------------------------------------
# REST IS LOADED DYNAMICALLY ACCORDING TO ENV
yml_settings = load_settings_from_yml("env-" + USE_ENV + ".yml")

IS_MOCK_DB = yml_settings['mock']['db']
IS_MOCK_RELAY = yml_settings['mock']['relay']

# SERVER
SERVER_HOST = yml_settings['server']['host']
SERVER_MQTT_PORT = yml_settings['server']['mqtt-port']
SERVER_TIMEOUT = yml_settings['server']['timeout']
SERVER_REST_PORT = yml_settings['server']['rest-port']

# CLIENT
CLIENT_HOST = yml_settings['client']['host']
CLIENT_MQTT_PORT = yml_settings['client']['mqtt-port']
CLIENT_TIMEOUT = yml_settings['client']['timeout']

TOPIC = yml_settings['topic']

if __name__ == '__main__':
    print(locals())