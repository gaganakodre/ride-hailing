import json


def make_event(method, resource, path_parameters=None, body=None):
    """Builds an API Gateway-style event, like the ones the handler receives in AWS."""
    return {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": path_parameters or {},
        "body": json.dumps(body) if body is not None else None,
    }


def parse_body(response):
    return json.loads(response["body"]) if response["body"] else {}