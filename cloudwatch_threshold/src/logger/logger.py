import boto3
import json

from datetime import datetime


def get_sequence_id(client, log_group):
    response = client.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix='LogStreamForLambda'
    )
    try:
        return response['logStreams'][0]['uploadSequenceToken']
    except KeyError:
        return None


def send_message(client, log_group, logEvents, token=None):
    if token is None:
        response = client.put_log_events(
            logGroupName=log_group,
            logStreamName='LogStreamForLambda',
            logEvents=logEvents
        )
    else:
        response = client.put_log_events(
            logGroupName=log_group,
            logStreamName='LogStreamForLambda',
            logEvents=logEvents,
            sequenceToken=token
        )
    return response


def main(event, context):
    client = boto3.client('logs')
    logEvents = []

    for i in range(len(event['logs'])):
        message = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "message": json.dumps(event['logs'][i])
        }
        logEvents.append(message)

    for group in event['log_groups']:
        token = get_sequence_id(client, group)
        send_message(client, group, logEvents, token)
