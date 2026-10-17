import logging

from src.container import Services
from src.routes import CONTROLLER_MAP
from utils.event_utils import EventUtils
from utils.status_codes import StatusCodes

logging.getLogger().setLevel(logging.INFO)

# Created once and reused across requests, like a warm Lambda container.
# Data lives in memory, so it resets when the process restarts.
default_services = Services()


def handle(event, context=None, services=None):
    """Entry point for every API request (same shape as an AWS Lambda handler).

    `services` can be passed in by tests to get a fresh, isolated state.
    """
    services = services or default_services
    resource = EventUtils.get_resource(event)
    request_type = EventUtils.get_request_type(event)
    logging.info("Request: %s %s", request_type, resource)

    methods = CONTROLLER_MAP.get(resource)
    if methods is None:
        return StatusCodes.generate_error(404, "resource", "resource_missing", f"No route for {resource}")

    controller_cls = methods.get(request_type)
    if controller_cls is None:
        return StatusCodes.generate_error(405, "resource", "method_not_allowed", f"{request_type} not allowed on {resource}")

    return controller_cls(event, services).execute()