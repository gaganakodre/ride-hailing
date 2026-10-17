import json


class StatusCodes:
    """Builds API Gateway-style responses: {"statusCode": ..., "body": "<json string>"}."""

    @staticmethod
    def generate_success(code, data=None):
        body = "" if code == 204 else json.dumps(data if data is not None else {}, default=str)
        return {"statusCode": code, "body": body}

    @staticmethod
    def generate_error(code, resource="resource", error_type="bad_request", message=""):
        body = {"error": error_type, "resource": resource, "message": message}
        return {"statusCode": code, "body": json.dumps(body)}