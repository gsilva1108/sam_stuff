import boto3
import time
import logging
import os
import json

from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class QueryHandler(object):

    def __init__(self, query, threshold, log_group, log_stream):
        self._threshold = threshold
        self._query = query
        self._log_group = log_group
        self._log_stream = log_stream
        self._client_logs = boto3.client('logs')
        self._client_db = boto3.resource('dynamodb')
        self._client_sns = boto3.client('sns')
        self._log_group = str = os.environ['LOG_GROUP']
        self._log_stream = str = os.environ['LOG_STREAM']
        self._dynamo_table = str = os.environ['DYNAMODB_TABLE']
        self._sns_topic = str = os.environ['SNS_TOPIC']
        self._result = self.insights_query(self._query, self._log_group, self._log_stream)

    def scan_table(self):
        try:
            table = self._client_db.Table(self._dynamo_table)
            response = table.scan()
        except Exception as e:
            print(e)
        return response['Items']

    def put_item(self, message):
        table = self._client_db.Table(self._dynamo_table)
        response = table.put_item(
            Item=message
        )
        return response


    def send_sns(self,sns_topic, username, total, log_group, log_stream):
        alert_message = f"ClientId: {username}\nTotalErrors: {str(total)}"
        response = self._client_sns.publish(
            TopicArn=sns_topic,
            Message=alert_message,
            Subject="Client '{}' Surpassed Threshold in {}/{}".format(
                username, log_group, log_stream)
        )
        return response


    def insights_query(self, query, log_group, log_stream):
        start_time = int((datetime.today() - timedelta(hours=1)).timestamp())
        end_time = int(datetime.now().timestamp())

        try:
            start_query_response = self._client_logs.start_query(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query
            )

            query_id = start_query_response['queryId']
            response = None

            while response is None or response['status'] == 'Running':
                time.sleep(5)
                response = self._client_logs.get_query_results(
                    queryId=query_id
                )

            print(f'Query Total from {log_stream}: {usercount_list}')
            return response['results']

        except Exception as err:
            print(f"Error occurred while running query: {err}")
            return {
                'statusCode': 500,
                'error': f"Error occurred while running query: {err}"
            }

    def threshold_check(self) -> bool:
        for result in self._result:
            if int(result[1]['value']) < self._threshold:
                self.put_item(
                    message = {
                        "username": result[0]['value'],
                        "total": result[1]['value'],
                        "alarm_sent": "false"
                    }
                )
            else:
                self.send_sns(self._sns_topic, user['username'],
                        str(result[0]['value']), self._log_group, self._log_stream)
                response = put_item(
                    table, user['username'], user['total'], alarm_sent)

    def add_to_dynamo(self,user):
        try:
            alarm_sent = "true"
            table = self._client_db.Table(self._dynamo_table)
            table_items = table.scan()
            if not table_items['Items']:
                if int(user['total']) < 12:
                    response = put_item(
                        table, user['username'], user['total'])
                else:
                    send_sns(client_sns, sns_topic, user['username'],
                            str(user['total']), log_group, log_stream)
                    response = put_item(
                        table, user['username'], user['total'], alarm_sent)
            else:
                for user in usercount_list:
                    for item in table_items['Items']:
                        new_total = int(user['total']) + int(item['total'])
                        if user['username'] == item['username'] and item['alarm_sent'] == 'false':
                            if new_total < 12:
                                put_item(table, user['username'], new_total)
                            else:
                                send_sns(client_sns, sns_topic, user['username'],
                                        str(new_total), log_group, log_stream)
                                put_item(
                                    table, user['username'], new_total, alarm_sent)
                        elif user['username'] == item['username'] and item['alarm_sent'] == 'true':
                            put_item(
                                table, user['username'], new_total, alarm_sent)
        except Exception as err:
        print(f"Error adding item to DynamoDB: {err}")
        return {
            "statusCode": 500,
            "error": f"Error adding item to DynamoDB: {err}"
        }
