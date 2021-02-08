import time
import os
import json
import logging

from queryHandler import QueryHandler
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def add_to_dynamo(query_handler, query_name, user, total, threshold, sns_topic):
    """
    This method creates the  item for DynamoDB (message),
    and takes the information from 'query_to_stream'.  It
    checks to see if the user already exists in the table
    and if an alert for meeting the threshold was already 
    sent. If the threshold is met, an email will be sent
    to the SNS Topic. If the alert was already sent, 
    continue to update the 'total' value, but don't send 
    the alert.

    Args: Class object,   JSON information,   user info,
          user total, threshold for the query, SNS Topic
    """
    message = query_handler.get_message(
        query_name, user['username'], total, threshold
    )
    if not query_handler.threshold_check(int(total)):
        query_handler.put_item(message)
    else:
        try:
            message['alert_sent'] = True
            if user['alert_sent']:
                query_handler.put_item(message)
            elif not user['alert_sent']:
                query_handler.send_sns(
                    sns_topic, user['username'],
                    total, query_handler.log_group,
                    query_handler.log_stream
                )
                query_handler.put_item(message)
        except KeyError:
            query_handler.send_sns(
                sns_topic, user['username'],
                total, query_handler.log_group,
                query_handler.log_stream
            )
            query_handler.put_item(message)
        except Exception as err:
            logger.error(f"Error adding item to Dynamo: {err}")


def insights_query(query_handler):
    """
    This method does the insight query  based on  the
    log  group  and  log stream provided, and get the 
    usernames  as  well  as  the total amount of logs
    that the user has within the log group/log stream

    Args:      Class object
    Returns:  'usercount_list' as a list of users and
               their total log count.
    """
    start_time = int((datetime.today() - timedelta(hours=1)).timestamp())
    end_time = int(datetime.now().timestamp())

    try:
        client_logs = query_handler.client_logs
        start_query_response = client_logs.start_query(
            logGroupName=query_handler.log_group,
            startTime=start_time,
            endTime=end_time,
            queryString=query_handler.query
        )

        query_id = start_query_response['queryId']
        response = None

        while response is None or response['status'] == 'Running':
            response = client_logs.get_query_results(
                queryId=query_id
            )
        logger.info(f"Query completed. Query ID: {query_id}")

        usercount_list = []
        for user in response['results']:
            tmp_dict = {}
            tmp_dict[user[0]['field']] = user[0]['value']
            tmp_dict[user[1]['field']] = user[1]['value']
            usercount_list.append(tmp_dict)

        logger.info(
            f'Query Total from {query_handler.log_stream}: {usercount_list}'
        )
        return usercount_list

    except Exception as err:
        logger.error(f"Error occurred while running query: {err}")
        return {
            'statusCode': 500,
            'error': f"Error occurred while running query: {err}"
        }


def query_to_stream(query_handler, sns_topic):
    """
    This will call 'insights_query'  to  get the user 
    list, and for   each user,   it  will input   the 
    arguments passed into this method, and send it to
    'add_to_dynamo'

    Args: Class object, JSON information,  SNS Topic.  
    """
    usercount_list = insights_query(query_handler)

    try:
        for user in usercount_list:
            response = query_handler.query_table(user['username'])
            if not response:
                add_to_dynamo(
                    query_handler, query_handler.query_name, user,
                    int(user['total']), query_handler.threshold,
                    sns_topic
                )
            elif response:
                dynamo_user = response[0]
                new_total = int(user['total']) + int(dynamo_user['total'])
                add_to_dynamo(
                    query_handler, query_handler.query_name, dynamo_user,
                    new_total, query_handler.threshold, sns_topic
                )

    except Exception as err:
        logger.error(f"Error moving information to 'add_to_dynamo': {err}")
        return {
            "statusCode": 500,
            "error": f"Error moving information to 'add_to_dynamo': {err}"
        }


def main(event, context):
    sns_topic = os.environ['SNS_TOPIC']

    with open('config/personal.json', 'r') as f:
        # JSON with all the Log Groups, Log Streams and queries
        data = json.load(f)

    for queries in data.values():  # Retrieves the information required for the handler
        try:
            for i in range(len(queries)):
                query = queries[i]
                query_handler = QueryHandler(
                    query['query'], query['query_name'],
                    query['threshold'], query['logGroup'],
                    query['logStream']
                )
                query_to_stream(query_handler, sns_topic)

        except Exception as err:
            logger.error(
                f"Error moving information to 'query_to_stream': {err}")
            return {
                "statusCode": 500,
                "error": f"Error moving information to 'query_to_stream': {err}"
            }
