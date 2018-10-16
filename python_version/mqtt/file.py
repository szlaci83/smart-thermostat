'''
Mock DB using file output.
'''
from python_version.mqtt.settings import *

class DatabaseManager:
    @staticmethod
    def put(data):
        print("FILE" + str(data))
        with open(MOCK_FILE, 'w+') as file:
            item={
                'device_id': data["client_id"],
                'date': data['timestamp'],
                'temp': data['temp'],
                'humidity': data['humidity'],
                }
            file.write(str(item))
            file.close()


def example():
    db = DatabaseManager()
    db.put(data={'client_id': 11,
                 'timestamp': '111',
                 'temp': 0,
                 'humidity': 0})

    print("PutItem succeeded:")


def handle(data):
    db = DatabaseManager()
    db.put(data=data)


if __name__ == '__main__':
    example()
