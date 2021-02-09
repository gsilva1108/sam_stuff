import boto3
import os


def main(event, context):
    dynamo_table = os.environ['DYNAMODB_TABLE']

    client_db = boto3.resource('dynamodb').Table(dynamo_table)

    table_items = client_db.scan()

    for item in table_items['Items']:
        client_db.delete_item(
            Key={
                "username": item['username'],
                "query_name": item['query_name']
            }
        )
