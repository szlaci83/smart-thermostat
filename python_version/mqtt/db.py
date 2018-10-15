import boto3
import decimal
import json
import time


class DatabaseManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('temp_test')

    def put(self, data):
        response = self.table.put_item(
            Item={
                'device_id': 7, # data["client_id"]
                'date': str(data['timestamp']),
                'temp': data['temp'],
                'humidity': data['humidity'],
            }
        )
        time.sleep(2)
        print(response)
        #return response

    def add_del_update_db_record(self, sql_query, args=()):
        self.cur.execute(sql_query, args)
        self.conn.commit()
        return


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
        'timestamp': '111',
        'temp': 0,
        'humidity': 0,
    })

    print("PutItem succeeded:")
    print(json.dumps(response, indent=4, cls=DecimalEncoder))


if __name__ == '__main__':
    example()

#
#
# response = table.query(
#     KeyConditionExpression=Key('device_id').eq(1)
# )
#
# for i in response['Items']:
#     print(i['date'], ":", i['temp'])
