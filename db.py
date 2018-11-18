import boto3
import decimal
import json
from boto3.dynamodb.conditions import Key
from settings import *


class DatabaseManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        #TODO: create tables proframatically for locations...
        self.table = self.dynamodb.Table(TABLE_NAME)

    # Returns True if put was successful
    def put(self, data):
    # TODO: store location in DB as well (String)
        response = self.table.put_item(
            Item={
                'device_id': data["client_id"],
                'date': str(data['epoch']),
                'temp': data['temp'],
                'humidity': data['humidity']
            }
        )
        return response['ResponseMetadata']['HTTPStatusCode'] == HTTP_OK

    def add_del_update_db_record(self, sql_query, args=()):
        self.cur.execute(sql_query, args)
        self.conn.commit()
        return

    def get_by_id(self, id):
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

    response = db.get_by_id(11)
    for i in response['Items']:
        print(i['date'], ":", i['temp'], ":", i['humidity'])


if __name__ == '__main__':
    example()

