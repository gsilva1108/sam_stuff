import os
import json
import boto3
import datetime
from json import JSONEncoder

client = boto3.client('iam')


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def main(event, context):
    request = json.dumps(event['body'])

    try:
        if request['user']:
            response = client.get_user(
                UserName=request['user']
            )
        elif request['user'] is None:
            response = client.list_users()
        return json.dumps(response, indent=4, cls=DateTimeEncoder)
    except client.exceptions.NoSuchEntityException as err:
        return {
            "statusCode": 400,
            "error": err
        }
