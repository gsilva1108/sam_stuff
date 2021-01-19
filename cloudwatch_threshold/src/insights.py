import boto3
import time

from datetime import datetime, timedelta

log_groups = ['LogGroupForLambda']
log_streams = ['LogStreamForLambda']


def main(event, context):
    client = boto3.client('logs')
    query_total_count = -1

    for log_group in log_groups:
        for log_stream in log_streams:

            start_time = int(
                (datetime.today() - timedelta(minutes=60)).timestamp())
            end_time = int(datetime.now().timestamp())

            query = "fields @timestamp, @message | filter @logStream = 'LogStreamForLambda' | stats count(*) as total by username | sort total desc"

            try:
                start_query_response = client.start_query(
                    logGroupName=log_group,
                    startTime=start_time,
                    endTime=end_time,
                    queryString=query
                )

                query_id = start_query_response['queryId']
                response = None

                while response is None or response['status'] == 'Running':
                    time.sleep(5)
                    response = client.get_query_results(
                        queryId=query_id
                    )

                query_total_count = int(response['results'][0][0]['value'])

                print(f'Query Total from {log_stream}: {query_total_count}')

            except Exception as err:
                print(err)
                return {
                    'statusCode': 500
                }
