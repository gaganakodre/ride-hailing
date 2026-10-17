from unittest import TestCase

from src.constants import RATE_CARDS
from src.models import CarType, Coupon, DiscountType
from src.pricing import PricingService


class TestHatchbackRateCard(TestCase):
    def setUp(self):
        self.card = RATE_CARDS[CarType.HATCHBACK]

    def test_short_ride_pays_minimum_fare(self):
        self.assertEqual(self.card.fare_for(1), 50)    # 1x10 = 10 -> minimum 50
        self.assertEqual(self.card.fare_for(4), 50)    # 2x10 + 2x8 = 36 -> minimum 50

    def test_fare_crosses_all_three_slabs(self):
        self.assertEqual(self.card.fare_for(7), 54)    # 2x10 + 3x8 + 2x5
        self.assertEqual(self.card.fare_for(10), 69)   # 2x10 + 3x8 + 5x5

    def test_fractional_distance_is_prorated(self):
        self.assertEqual(self.card.fare_for(12.5), 81.5)  # 20 + 24 + 7.5x5


class TestSedanRateCard(TestCase):
    def test_sedan_rates(self):
        card = RATE_CARDS[CarType.SEDAN]
        self.assertEqual(card.fare_for(1), 80)         # minimum
        self.assertEqual(card.fare_for(10), 106)       # 2x15 + 3x12 + 5x8


class TestPricingService(TestCase):
    def setUp(self):
        self.pricing = PricingService(RATE_CARDS)

    def test_fare_without_coupon(self):
        fare = self.pricing.calculate_fare(10, CarType.HATCHBACK)
        self.assertEqual(fare["base_fare"], 69)
        self.assertEqual(fare["discount"], 0)
        self.assertEqual(fare["final_fare"], 69)

    def test_flat_coupon(self):
        coupon = Coupon("FLAT30", DiscountType.FLAT, 30)
        fare = self.pricing.calculate_fare(10, CarType.HATCHBACK, coupon)
        self.assertEqual(fare["final_fare"], 39)

    def test_percent_coupon_with_cap(self):
        coupon = Coupon("HALF", DiscountType.PERCENT, 50, max_discount=20)
        fare = self.pricing.calculate_fare(10, CarType.HATCHBACK, coupon)
        self.assertEqual(fare["discount"], 20)
        self.assertEqual(fare["final_fare"], 49)