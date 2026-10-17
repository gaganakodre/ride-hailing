from src.constants import RATE_CARDS
from src.pricing import PricingService
from src.repository import InMemoryRepository
from src.services.coupon_service import CouponService
from src.services.driver_service import DriverService
from src.services.ride_service import RideService
from src.services.user_service import UserService


class Services:
    """Creates every service once and wires them together (the app's shared in-memory state)."""

    def __init__(self):
        self.user_service = UserService(InMemoryRepository())
        self.driver_service = DriverService(InMemoryRepository())
        self.coupon_service = CouponService(InMemoryRepository())
        self.pricing_service = PricingService(RATE_CARDS)
        self.ride_service = RideService(
            InMemoryRepository(),
            self.user_service,
            self.driver_service,
            self.coupon_service,
            self.pricing_service,
        )