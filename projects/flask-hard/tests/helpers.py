import json


def json_of_response(response):
    return json.loads(response.data)
