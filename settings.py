# SERVER
SERVER_HOST = "localhost"
SERVER_PORT = 1883
SERVER_TIMEOUT = 60

# CLIENT
CLIENT_HOST = "localhost"
CLIENT_PORT = 1883
CLIENT_TIMEOUT = 60

TOPIC = "topic/temperature"

# DB
TABLE_NAME = 'temp_test'
MOCK_FILE = 'db.csv'

HTTP_OK = 200

# Heating
HEATING = False
THRESHOLD = 0.8

WEATHER_QUERY = "http://api.openweathermap.org/data/2.5/weather?units=metric&id=%s&APPID=%s"
JSON_HEADER = {'content-type': 'application/json'}