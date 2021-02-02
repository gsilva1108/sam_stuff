# import boto3
# import time
# import os
# import json
# import logging

# from utils.queryHandler import QueryHandler
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


# def add_to_dynamo(query_handler, query, user, total, sns_topic):
#     message = query_handler.get_message(
#         query['logGroup'], user['username'], total
#     )
#     try:
#         if not query_handler.threshold_check(total):
#             query_handler.put_item(message)
#         else:
#             if user['alarm_sent']:
#                 message['alarm_sent'] = True
#                 query_handler.put_item(message)
#             elif not user['alarm_sent']:
#                 query_handler.send_sns(
#                     sns_topic, user['username'],
#                     str(user['total']), query_handler.log_group,
#                     query_handler.log_stream
#                 )
#                 query_handler.put_item(message)
#     except Exception as err:
#         logger.error(f"Error when adding to Dynamo: {err}")


# def insights_query(query_handler):
#     start_time = int((datetime.today() - timedelta(hours=1)).timestamp())
#     end_time = int(datetime.now().timestamp())

#     try:
#         client_logs = query_handler.client_logs
#         start_query_response = client_logs.start_query(
#             logGroupName=query_handler.log_group,
#             startTime=start_time,
#             endTime=end_time,
#             queryString=query_handler.query
#         )

#         query_id = start_query_response['queryId']
#         response = None

#         while response is None or response['status'] == 'Running':
#             time.sleep(5)
#             response = client_logs.get_query_results(
#                 queryId=query_id
#             )
#         logger.info(f"Query completed. Query ID: {query_id}")

#         usercount_list = []
#         for user in response['results']:
#             tmp_dict = {}
#             tmp_dict[user[0]['field']] = user[0]['value']
#             tmp_dict[user[1]['field']] = user[1]['value']
#             usercount_list.append(tmp_dict)

#         logger.info(
#             f'Query Total from {query_handler.log_stream}: {usercount_list}'
#         )
#         return usercount_list

#     except Exception as err:
#         logger.error(f"Error occurred while running query: {err}")
#         return {
#             'statusCode': 500,
#             'error': f"Error occurred while running query: {err}"
#         }


# def main(event, context):
#     sns_topic = os.environ['SNS_TOPIC']

#     with open('utils/personal.json', 'r') as f:
#         data = json.load(f)

#     query = data['LogGroups'][0]
#     query_handler = QueryHandler(
#         query['query'], query['threshold'],
#         query['logGroup'], query['logStream']
#     )

#     usercount_list = query_handler.insights_query(query_handler)

#     try:
#         if not query_handler.scan_table():
#             for user in usercount_list:
#                 add_to_dynamo(
#                     query_handler, query, user,
#                     int(user['total']), sns_topic
#                 )
#         for item in query_handler.scan_table():
#             for user in usercount_list:
#                 new_total = int(user['total']) + int(item['total'])
#                 add_to_dynamo(
#                     query_handler, query,
#                     user, new_total, sns_topic
#                 )

#     except Exception as err:
#         logger.error(f"Error adding item to DynamoDB: {err}")
#         return {
#             "statusCode": 500,
#             "error": f"Error adding item to DynamoDB: {err}"
#         }
