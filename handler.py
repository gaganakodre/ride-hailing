import logging

from src.routes import CONTROLLER_MAP
from utils.event_utils import EventUtils
from utils.status_codes import StatusCodes

logging.getLogger().setLevel(logging.INFO)


def handle(event, context=None):
    """Entry point for every API request (same shape as an AWS Lambda handler)."""
    resource = EventUtils.get_resource(event)
    request_type = EventUtils.get_request_type(event)
    logging.info("Request: %s %s", request_type, resource)

    methods = CONTROLLER_MAP.get(resource)
    if methods is None:
        return StatusCodes.generate_error(404, "resource", "resource_missing", f"No route for {resource}")

    controller_cls = methods.get(request_type)
    if controller_cls is None:
        return StatusCodes.generate_error(405, "resource", "method_not_allowed", f"{request_type} not allowed on {resource}")

    return controller_cls(event).execute()