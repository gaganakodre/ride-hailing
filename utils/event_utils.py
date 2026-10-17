import json


class EventUtils:
    """Small helpers to read fields from an API Gateway-style event."""

    @staticmethod
    def get_resource(event):
        return event.get("resource", "")

    @staticmethod
    def get_request_type(event):
        return (event.get("httpMethod") or "").upper()

    @staticmethod
    def get_path_parameters(event):
        return event.get("pathParameters") or {}

    @staticmethod
    def get_body(event):
        """Returns the body as a dict. Raises ValueError if the body is not valid JSON."""
        body = event.get("body")
        if not body:
            return {}
        if isinstance(body, dict):
            return body
        return json.loads(body)