import json


def main(event, context):
    response = json.dumps(event)
    return response
