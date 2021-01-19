import boto3
import json

from datetime import datetime


def get_sequence_id(client):
    response = client.describe_log_streams(
        logGroupName='LogGroupForLambda',
        logStreamNamePrefix='LogStreamForLambda'
    )
    try:
        return response['logStreams'][0]['uploadSequenceToken']
    except KeyError:
        return None


def send_message(client, logEvents, token=None):
    if token is None:
        response = client.put_log_events(
            logGroupName="LogGroupForLambda",
            logStreamName="LogStreamForLambda",
            logEvents=logEvents
        )
    response = client.put_log_events(
        logGroupName="LogGroupForLambda",
        logStreamName="LogStreamForLambda",
        logEvents=logEvents,
        sequenceToken=token
    )
    return response


def main(event, context):
    client = boto3.client('logs')
    token = get_sequence_id(client)

    logEvents = [
        {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "message": json.dumps(event[0])
        },
        {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "message": json.dumps(event[1])
        },
        {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "message": json.dumps(event[2])
        }
    ]

    return send_message(client, logEvents, token)
