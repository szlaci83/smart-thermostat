#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import datetime
from multiprocessing import Pool, Queue, cpu_count
import threading
from python_version.mqtt.db import *

# This is the Subscriber
# SERVER SIDE

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('temp_test')


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("topic/temperature")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        q.put(data)
        data['timestamp'] = datetime.datetime.now().timestamp()
    except Exception as e:
        print(e)
    print(data)
    print()


def log_worker():
    """runs in own thread to log data"""
    while True:
        results = q.get(block=True, timeout=None)
        if results is None:
            continue
        else:
            db.put(results)
            print("DBBBBB")
            #print("message saved ",results["message"])


q = Queue()
client = mqtt.Client()
client.connect("localhost", 1883, 60)
db = DatabaseManager()

client.on_connect = on_connect
client.on_message = on_message

t = threading.Thread(target=log_worker)
t.start()

client.loop_forever()


