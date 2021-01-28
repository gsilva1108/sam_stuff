import boto3
import time
import os

from datetime import datetime, timedelta


def put_item(client_db, username, total, alarm_sent="false"):
    response = client_db.put_item(
        Item={
            "username": username,
            "total": total,
            "alarm_sent": alarm_sent
        }
    )
    return response


def send_sns(client_sns, sns_topic, username, total, log_group, log_stream):
    alert_message = f"ClientId: {username}\nTotalErrors: {str(total)}"
    response = client_sns.publish(
        TopicArn=sns_topic,
        Message=alert_message,
        Subject="Client '{}' Surpassed Threshold in {}/{}".format(
            username, log_group, log_stream)
    )
    return response


def main(event, context):
    log_group = os.environ['LOG_GROUP']
    log_stream = os.environ['LOG_STREAM']
    dynamo_table = os.environ['DYNAMODB_TABLE']
    sns_topic = os.environ['SNS_TOPIC']

    client_logs = boto3.client('logs')
    client_db = boto3.resource('dynamodb').Table(dynamo_table)
    client_sns = boto3.client('sns')

    start_time = int((datetime.today() - timedelta(hours=1)).timestamp())
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
            tmp_dict[user[0]['field']] = user[0]['value'] # "username": username
            tmp_dict[user[1]['field']] = user[1]['value'] # "total": total
            usercount_list.append(tmp_dict)

        print(f'Query Total from {log_stream}: {usercount_list}')

    except Exception as err:
        print(f"Error occurred while running query: {err}")
        return {
            'statusCode': 500,
            'error': f"Error occurred while running query: {err}"
        }

    try:
        alarm_sent = "true"
        table_items = client_db.scan()
        if not table_items['Items']:
            for user in usercount_list:
                if int(user['total']) < 12:
                    response = put_item(
                        client_db, user['username'], user['total'])
                else:
                    send_sns(client_sns, sns_topic, user['username'],
                             str(user['total']), log_group, log_stream)
                    response = put_item(
                        client_db, user['username'], user['total'], alarm_sent)
        else:
            for user in usercount_list:
                for item in table_items['Items']:
                    new_total = int(user['total']) + int(item['total'])
                    if user['username'] == item['username'] and item['alarm_sent'] == 'false':
                        if new_total < 12:
                            put_item(client_db, user['username'], new_total)
                        else:
                            send_sns(client_sns, sns_topic, user['username'],
                                     str(new_total), log_group, log_stream)
                            put_item(
                                client_db, user['username'], new_total, alarm_sent)
                    elif user['username'] == item['username'] and item['alarm_sent'] == 'true':
                        put_item(
                            client_db, user['username'], new_total, alarm_sent)
    except Exception as err:
        print(f"Error adding item to DynamoDB: {err}")
        return {
            "statusCode": 500,
            "error": f"Error adding item to DynamoDB: {err}"
        }
