from dataclasses import dataclass

from src.models import CarType, Coupon


@dataclass(frozen=True)
class Slab:
    """Charge `rate_per_km` for every km up to `up_to_km` (use math.inf for the last slab)."""
    up_to_km: float
    rate_per_km: float


@dataclass(frozen=True)
class RateCard:
    minimum_fare: float
    slabs: list[Slab]

    def fare_for(self, distance_km: float) -> float:
        """Slab-based fare, like income tax: each km is charged at its own slab's rate."""
        fare = 0.0
        previous_limit = 0.0
        for slab in self.slabs:
            if distance_km <= previous_limit:
                break
            km_in_this_slab = min(distance_km, slab.up_to_km) - previous_limit
            fare += km_in_this_slab * slab.rate_per_km
            previous_limit = slab.up_to_km
        return max(fare, self.minimum_fare)


class PricingService:
    def __init__(self, rate_cards: dict[CarType, RateCard]):
        self.rate_cards = rate_cards

    def calculate_fare(self, distance_km: float, car_type: CarType, coupon: Coupon | None = None) -> dict:
        base_fare = self.rate_cards[car_type].fare_for(distance_km)
        discount = coupon.discount_for(base_fare) if coupon else 0.0
        return {
            "distance_km": round(distance_km, 2),
            "billed_car_type": car_type.value,
            "base_fare": round(base_fare, 2),
            "discount": round(discount, 2),
            "final_fare": round(base_fare - discount, 2),
        }