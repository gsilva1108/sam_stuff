import os
import json
import boto3


client = boto3.client('events')


def main(event, context):
    try:
        requestData = json.loads(event['body'])

        if requestData:
            client.put_events(
                Entries=[
                    {
                        'Detail': json.dumps(requestData),
                        'DetailType': requestData['type'],
                        'Source': 'TextEndpoint',
                        'EventBusName': os.environ['EVENT_BUS_NAME']
                    }
                ]
            )

        print('Pushed data to EventBridge')

        return {
            "message": "data received",
            "data": requestData
        }
    except Exception as err:
        print(err)
        return {
            "message": "Error submitting data",
            "error": err
        }
