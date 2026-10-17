class RideHailingError(Exception):
    """Base class for all business errors. Controllers turn these into HTTP status codes."""


class ValidationError(RideHailingError):
    """Input is missing or has the wrong format."""


class NotFoundError(RideHailingError):
    """A user, driver, ride or coupon does not exist."""


class AlreadyExistsError(RideHailingError):
    """Trying to create something that already exists (e.g. duplicate phone or coupon code)."""


class InvalidCouponError(RideHailingError):
    """Coupon code given at booking is not valid."""


class NoDriverAvailableError(RideHailingError):
    """No free driver of a suitable car type within the search radius."""


class InvalidRideStateError(RideHailingError):
    """Action not allowed in the ride's current state (e.g. ending a completed ride)."""