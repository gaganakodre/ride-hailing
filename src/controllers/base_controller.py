import logging

from src.exceptions import (
    AlreadyExistsError,
    InvalidCouponError,
    InvalidRideStateError,
    NoDriverAvailableError,
    NotFoundError,
    RideHailingError,
    ValidationError,
)
from src.models import Location
from utils.event_utils import EventUtils
from utils.status_codes import StatusCodes

# The ONE place where business errors become HTTP status codes.
ERROR_MAP = {
    ValidationError: (400, "bad_request"),
    InvalidCouponError: (400, "invalid_coupon"),
    NotFoundError: (404, "resource_missing"),
    AlreadyExistsError: (409, "already_exists"),
    NoDriverAvailableError: (409, "no_driver_available"),
    InvalidRideStateError: (409, "invalid_state"),
}


class BaseController:
    resource = "resource"  # used in error responses, e.g. "ride"

    def __init__(self, event, services):
        self.event = event
        self.services = services
        self.path_parameters = EventUtils.get_path_parameters(event)
        self.body = {}

    def process(self):
        """Each controller implements this and returns a StatusCodes response."""
        raise NotImplementedError

    def execute(self):
        try:
            self.body = EventUtils.get_body(self.event)
            return self.process()
        except ValueError:
            return StatusCodes.generate_error(400, self.resource, "bad_request", "Body must be valid JSON")
        except RideHailingError as error:
            code, error_type = ERROR_MAP.get(type(error), (400, "bad_request"))
            return StatusCodes.generate_error(code, self.resource, error_type, str(error))
        except Exception:
            logging.exception("Unexpected error")
            return StatusCodes.generate_error(500, self.resource, "internal_error", "Something went wrong")

    # ---------- input helpers (raise ValidationError -> 400) ----------

    def get_string(self, field, required=True):
        value = self.body.get(field)
        if value is None and not required:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"'{field}' is required and must be a non-empty string")
        return value.strip()

    def get_number(self, field, required=True, default=None):
        value = self.body.get(field)
        if value is None and not required:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"'{field}' is required and must be a number")
        return value

    def get_enum(self, field, enum_cls):
        value = self.get_string(field).upper()
        try:
            return enum_cls(value)
        except ValueError:
            allowed = ", ".join(member.value for member in enum_cls)
            raise ValidationError(f"'{field}' must be one of: {allowed}")

    def get_location(self, field):
        value = self.body.get(field)
        if not isinstance(value, dict):
            raise ValidationError(f"'{field}' must be an object like {{\"x\": 1, \"y\": 2}}")
        x, y = value.get("x"), value.get("y")
        for coordinate in (x, y):
            if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
                raise ValidationError(f"'{field}' must have numeric 'x' and 'y'")
        return Location(x, y)

    @staticmethod
    def history_to_dict(history):
        return {status: [ride.to_dict() for ride in rides] for status, rides in history.items()}