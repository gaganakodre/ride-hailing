from unittest import TestCase

from src.constants import RATE_CARDS
from src.exceptions import InvalidCouponError, InvalidRideStateError, NoDriverAvailableError, NotFoundError
from src.models import CarType, DiscountType, Location, RideStatus
from src.pricing import PricingService
from src.repository import InMemoryRepository
from src.services.coupon_service import CouponService
from src.services.driver_service import DriverService
from src.services.ride_service import RideService
from src.services.user_service import UserService

PICKUP = Location(0, 0)
DROP_10_KM = Location(10, 0)


class TestRideService(TestCase):
    def setUp(self):
        self.users = UserService(InMemoryRepository())
        self.drivers = DriverService(InMemoryRepository())
        self.coupons = CouponService(InMemoryRepository())
        self.rides = RideService(
            InMemoryRepository(), self.users, self.drivers, self.coupons, PricingService(RATE_CARDS)
        )
        self.user = self.users.register("Asha", "9000000001")

    def add_driver(self, phone, car_type, x=1, y=0):
        return self.drivers.register("Driver", phone, f"CAB-{phone}", car_type, Location(x, y))

    # --- booking ---

    def test_books_nearest_driver_of_requested_type(self):
        self.add_driver("1", CarType.HATCHBACK, x=3)
        near = self.add_driver("2", CarType.HATCHBACK, x=1)

        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

        self.assertEqual(ride.driver_id, near.id)
        self.assertEqual(ride.status, RideStatus.ONGOING)
        self.assertFalse(near.is_available)

    def test_hatchback_request_is_upgraded_to_sedan_at_hatchback_price(self):
        self.add_driver("1", CarType.SEDAN)

        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)
        self.assertTrue(ride.is_upgraded)

        ended = self.rides.end_ride(ride.id)
        self.assertEqual(ended.fare["final_fare"], 69)  # Hatchback rate, not Sedan's 106

    def test_sedan_request_is_not_downgraded(self):
        self.add_driver("1", CarType.HATCHBACK)
        with self.assertRaises(NoDriverAvailableError):
            self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.SEDAN)

    def test_no_driver_within_radius(self):
        self.add_driver("1", CarType.HATCHBACK, x=50)
        with self.assertRaises(NoDriverAvailableError):
            self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

    def test_booked_driver_is_not_given_to_another_user(self):
        self.add_driver("1", CarType.HATCHBACK)
        other_user = self.users.register("Ravi", "9000000002")

        self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)
        with self.assertRaises(NoDriverAvailableError):
            self.rides.book_ride(other_user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

    def test_user_cannot_have_two_ongoing_rides(self):
        self.add_driver("1", CarType.HATCHBACK)
        self.add_driver("2", CarType.HATCHBACK)

        self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)
        with self.assertRaises(InvalidRideStateError):
            self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

    # --- coupons ---

    def test_coupon_is_applied_even_if_deleted_mid_ride(self):
        self.add_driver("1", CarType.HATCHBACK)
        self.coupons.add("FLAT30", DiscountType.FLAT, 30)

        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK, "FLAT30")
        self.coupons.delete("FLAT30")
        ended = self.rides.end_ride(ride.id)

        self.assertEqual(ended.fare["discount"], 30)
        self.assertEqual(ended.fare["final_fare"], 39)

    def test_invalid_coupon_fails_booking_without_blocking_driver(self):
        driver = self.add_driver("1", CarType.HATCHBACK)
        with self.assertRaises(InvalidCouponError):
            self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK, "NOPE")
        self.assertTrue(driver.is_available)

    # --- ending ---

    def test_end_ride_frees_driver_and_moves_cab_to_drop(self):
        driver = self.add_driver("1", CarType.HATCHBACK)
        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

        ended = self.rides.end_ride(ride.id)

        self.assertEqual(ended.status, RideStatus.COMPLETED)
        self.assertEqual(ended.fare["final_fare"], 69)
        self.assertTrue(driver.is_available)
        self.assertEqual(driver.cab.location, DROP_10_KM)

    def test_cannot_end_a_ride_twice(self):
        self.add_driver("1", CarType.HATCHBACK)
        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)
        self.rides.end_ride(ride.id)
        with self.assertRaises(InvalidRideStateError):
            self.rides.end_ride(ride.id)


    # --- history ---

    def test_user_history_splits_ongoing_and_completed(self):
        self.add_driver("1", CarType.HATCHBACK)
        first = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)
        self.rides.end_ride(first.id)
        second = self.rides.book_ride(self.user.id, DROP_10_KM, PICKUP, CarType.HATCHBACK)

        history = self.rides.get_user_history(self.user.id)

        self.assertEqual([ride.id for ride in history["completed"]], [first.id])
        self.assertEqual([ride.id for ride in history["ongoing"]], [second.id])

    def test_driver_history_only_has_that_drivers_rides(self):
        driver = self.add_driver("1", CarType.HATCHBACK)
        other = self.add_driver("2", CarType.HATCHBACK, x=4)
        ride = self.rides.book_ride(self.user.id, PICKUP, DROP_10_KM, CarType.HATCHBACK)

        self.assertEqual([r.id for r in self.rides.get_driver_history(driver.id)["ongoing"]], [ride.id])
        self.assertEqual(self.rides.get_driver_history(other.id), {"ongoing": [], "completed": []})

    def test_history_for_unknown_user_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.rides.get_user_history("user_99")