import boto3
import time
import os

from datetime import datetime, timedelta


def main(event, context):
    log_group = os.environ['LOG_GROUP']
    log_stream = os.environ['LOG_STREAM']
    dynamo_table = os.environ['DYNAMODB_TABLE']

    client_logs = boto3.client('logs')
    client_db = boto3.resource('dynamodb').Table(dynamo_table)

    start_time = int((datetime.today() - timedelta(hours=12)).timestamp())
    end_time = int(datetime.now().timestamp())

    query = "fields @timestamp, @message | filter @logStream = 'LogStreamForLambda' | stats count(*) as total by username | sort total desc"

    try:
        start_query_response = client_logs.start_query(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            queryString=query
        )

        query_id = start_query_response['queryId']
        response = None

        while response is None or response['status'] == 'Running':
            time.sleep(5)
            response = client_logs.get_query_results(
                queryId=query_id
            )

        usercount_list = []
        for user in response['results']:
            tmp_dict = {}
            tmp_dict[user[0]['value']] = user[1]['value']
            usercount_list.append(tmp_dict)

        print(f'Query Total from {log_stream}: {usercount_list}')

    except Exception as err:
        print(f"Error occurred while running query: {err}")
        return {
            'statusCode': 500,
            'error': f"Error occurred while running query: {err}"
        }

    try:
        table_items = client_db.scan(Select='ALL_ATTRIBUTES')
        dynamo_list = []
        for item in table_items:
            if item in usercount_list:
                continue
            dynamo_list.append(item)

        for user in dynamo_list:
            client_db.put_item(
                Item={
                    "ClientId": user.get("username"),
                    "TotalErrors": user.get("total")
                }
            )

    except Exception as err:
        print(f"Error adding item to DynamoDB: {err}")
        return {
            "statusCode": 500,
            "error": f"Error adding item to DynamoDB: {err}"
        }
