import boto3
import decimal
import json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import time


class DatabaseManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('temp_test')

    # Returns True if put was successful
    def put(self, data):
        response = self.table.put_item(
            Item={
                'device_id': data["client_id"],
                'date': str(data['timestamp']),
                'temp': data['temp'],
                'humidity': data['humidity'],
            }
        )
        return response['ResponseMetadata']['HTTPStatusCode'] == 200

    def add_del_update_db_record(self, sql_query, args=()):
        self.cur.execute(sql_query, args)
        self.conn.commit()
        return

    def get(self, id):
        response = self.table.query(
            KeyConditionExpression=Key('device_id').eq(id))
        return response


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def example():
    db = DatabaseManager()
    response = db.put(data={
        'client_id': 11,
        'timestamp': '1112',
        'temp': 0,
        'humidity': 0,
    })
    print("PutItem succeeded: " + str(response))

    response = db.get(11)
    for i in response['Items']:
        print(i['date'], ":", i['temp'], ":", i['humidity'])


if __name__ == '__main__':
    example()

