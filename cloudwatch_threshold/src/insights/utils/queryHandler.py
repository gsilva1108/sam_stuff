import boto3
import logging
import os

from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

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
        self._log_group = log_group
        self._log_stream = log_stream
        self._dynamo_table: str = os.environ['DYNAMODB_TABLE']

    @property
    def query(self):
        return self._query

    @property
    def log_group(self):
        return self._log_group

    @property
    def log_stream(self):
        return self._log_stream

    @property
    def threshold(self):
        return self._threshold

    @property
    def client_logs(self):  # Getter for logs client
        return self._client_logs

    @property
    def client_db(self):  # Getter for dynamo client
        return self._client_db

    def get_message(self, query_name, username, total, threshold, alarm_sent=False):
        message = {
            "query_name": query_name,
            "username": username,
            "total": total,
            "threshold": threshold,
            "alarm_sent": alarm_sent
        }
        return message

    def query_table(self, username):
        try:
            table = self._client_db.Table(self._dynamo_table)
            response = table.query(
                KeyConditionExpression=Key('username').eq(username))
        except Exception as err:
            logger.error(f"Error getting items from Dynamo: {err}")
        return response['Items']

    def put_item(self, message):
        table = self._client_db.Table(self._dynamo_table)
        response = table.put_item(
            Item=message
        )
        return response

    def send_sns(self, sns_topic, username, total, log_group, log_stream):
        alert_message = f"ClientId: {username}\nTotalErrors: {str(total)}"
        response = self._client_sns.publish(
            TopicArn=sns_topic,
            Message=alert_message,
            Subject="Client '{}' Surpassed Threshold in {}/{}".format(
                username, log_group, log_stream)
        )
        return response

    def threshold_check(self, result) -> bool:
        if result < self._threshold:
            return False
        else:
            return True
