import boto3
import decimal
import json
from boto3.dynamodb.conditions import Key
from properties import READING_SK, READING_PK, HTTP_OK


class DatabaseManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')

    def __create_table(self, table_name, partition_key, sort_key):
        attribute_list = [
            {
                'AttributeName': partition_key['name'],
                'AttributeType': partition_key['type']
            },
            {
                'AttributeName': sort_key['name'],
                'AttributeType': sort_key['type']
            }]

        params = {
            'TableName': table_name,
            'KeySchema': [
                {
                    'AttributeName': partition_key['name'],
                    'KeyType': partition_key['key_type']  # Partition key
                },
                {
                    'AttributeName': sort_key['name'],
                    'KeyType': sort_key['key_type']  # Sort key
                }
            ],
            'AttributeDefinitions': attribute_list,
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }}

        table = self.dynamodb.create_table(**params)

        return table.table_status

    def __create_if_not_exist(self, table_name, partition_key, sort_key):
        client = boto3.client("dynamodb")
        try:
            response = client.describe_table(TableName=table_name)
        except client.exceptions.ResourceNotFoundException:
            response = self.__create_table(table_name, partition_key, sort_key)
            waiter = client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
        return response

    # Returns True if put was successful
    def put(self, table_name, data, partition_key=READING_PK, sort_key=READING_SK):
        self.__create_if_not_exist(table_name=table_name, partition_key=partition_key, sort_key=sort_key)
        response = self.dynamodb.Table(table_name).put_item(Item=data)
        return response['ResponseMetadata']['HTTPStatusCode'] == HTTP_OK

    def add_del_update_db_record(self, sql_query, args=()):
        self.cur.execute(sql_query, args)
        self.conn.commit()
        return

    def get_by_id(self, table_name,  id):
        response = self.dynamodb.Table(table_name).query(
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

