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

CURRENT_TEMP = 22

DAYS = ['Monday', 'Tuesday', "Wednesday", 'Thursday', "Friday", "Saturday", "Sunday"]

HEATING_SETTINGS = {"Tuesday": [{'start_hour': 6,
                         'start_min': 0,
                         'end_hour': 23,
                         'end_min': 30,
                         'desired_temp': 24},

                                {'start_hour': 23,
                         'start_min': 31,
                         'end_hour': 23,
                         'end_min': 59,
                         'desired_temp': 20
                        }]
                    }


