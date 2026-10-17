from unittest import TestCase

from src.models import CarType, Coupon, DiscountType, Location, Ride


class TestLocation(TestCase):
    def test_distance_is_straight_line(self):
        self.assertEqual(Location(0, 0).distance_to(Location(3, 4)), 5)


class TestCoupon(TestCase):
    def test_flat_discount(self):
        coupon = Coupon("FLAT30", DiscountType.FLAT, 30)
        self.assertEqual(coupon.discount_for(100), 30)

    def test_percent_discount_respects_cap(self):
        coupon = Coupon("SAVE50", DiscountType.PERCENT, 50, max_discount=40)
        self.assertEqual(coupon.discount_for(100), 40)  # 50% of 100 = 50, capped at 40

    def test_discount_never_exceeds_amount(self):
        coupon = Coupon("BIG", DiscountType.FLAT, 500)
        self.assertEqual(coupon.discount_for(60), 60)


class TestRide(TestCase):
    def test_ride_knows_when_it_was_upgraded(self):
        ride = Ride("ride_1", "user_1", "driver_1", CarType.HATCHBACK, CarType.SEDAN,
                    Location(0, 0), Location(1, 1))
        self.assertTrue(ride.is_upgraded)
        self.assertEqual(ride.to_dict()["status"], "ONGOING")
