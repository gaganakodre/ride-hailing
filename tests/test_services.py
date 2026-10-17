from unittest import TestCase

from src.exceptions import AlreadyExistsError, InvalidCouponError, NotFoundError, ValidationError
from src.models import CarType, DiscountType, Location
from src.repository import InMemoryRepository
from src.services.coupon_service import CouponService
from src.services.driver_service import DriverService
from src.services.user_service import UserService


class TestUserService(TestCase):
    def setUp(self):
        self.users = UserService(InMemoryRepository())

    def test_register_and_get_user(self):
        user = self.users.register("Asha", "9000000001")
        self.assertEqual(self.users.get(user.id).name, "Asha")

    def test_duplicate_phone_is_rejected(self):
        self.users.register("Asha", "9000000001")
        with self.assertRaises(AlreadyExistsError):
            self.users.register("Someone else", "9000000001")

    def test_unknown_user_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.users.get("user_99")


class TestDriverService(TestCase):
    def setUp(self):
        self.drivers = DriverService(InMemoryRepository())

    def add_driver(self, phone, cab_number, car_type, x, y):
        return self.drivers.register("Driver", phone, cab_number, car_type, Location(x, y))

    def test_update_location(self):
        driver = self.add_driver("1", "KA01", CarType.SEDAN, 0, 0)
        self.drivers.update_location(driver.id, Location(2, 3))
        self.assertEqual(self.drivers.get(driver.id).cab.location, Location(2, 3))

    def test_finds_nearest_driver_within_radius(self):
        self.add_driver("1", "KA01", CarType.HATCHBACK, 4, 0)
        near = self.add_driver("2", "KA02", CarType.HATCHBACK, 1, 0)
        found = self.drivers.find_nearest_available(Location(0, 0), CarType.HATCHBACK, radius_km=5)
        self.assertEqual(found.id, near.id)

    def test_ignores_far_busy_and_wrong_type_drivers(self):
        self.add_driver("1", "KA01", CarType.HATCHBACK, 10, 0)          # too far
        busy = self.add_driver("2", "KA02", CarType.HATCHBACK, 1, 0)
        busy.is_available = False                                         # busy
        self.add_driver("3", "KA03", CarType.SEDAN, 1, 0)                # wrong type
        found = self.drivers.find_nearest_available(Location(0, 0), CarType.HATCHBACK, radius_km=5)
        self.assertIsNone(found)


class TestCouponService(TestCase):
    def setUp(self):
        self.coupons = CouponService(InMemoryRepository())

    def test_add_get_and_delete(self):
        self.coupons.add("flat30", DiscountType.FLAT, 30)
        self.assertEqual(self.coupons.get_valid("FLAT30").value, 30)  # codes are case-insensitive
        self.coupons.delete("FLAT30")
        with self.assertRaises(InvalidCouponError):
            self.coupons.get_valid("FLAT30")

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.coupons.add("ZERO", DiscountType.FLAT, 0)
        with self.assertRaises(ValidationError):
            self.coupons.add("TOOMUCH", DiscountType.PERCENT, 150)

    def test_deleting_unknown_coupon_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.coupons.delete("NOPE")