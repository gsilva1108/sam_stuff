import os
import json
import boto3

client = boto3.client('iam')


def update_user(user, new_user):
    response = client.update_user(
        UserName=user,
        NewUserName=new_user
    )
    return response


def main(event, context):
    request = event['detail']
    try:
        update_user(request['user'], request['new_user'])
        return {
            "statusCode": 200,
            "message": "UserName {} successfully changed to {}".format(request['user'], request['new_user'])
        }
    except Exception as err:
        return {
            "statusCode": 500,
            "errorMessage": err
        }
