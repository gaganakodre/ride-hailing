import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CarType(str, Enum):
    HATCHBACK = "HATCHBACK"
    SEDAN = "SEDAN"


class RideStatus(str, Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class DiscountType(str, Enum):
    FLAT = "FLAT"        # fixed amount off, e.g. ₹30
    PERCENT = "PERCENT"  # percentage off, e.g. 10%


def now_utc():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Location:
    """A point on a 2D grid, in km."""
    x: float
    y: float

    def distance_to(self, other: "Location") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_dict(self):
        return {"x": self.x, "y": self.y}


@dataclass
class User:
    id: str
    name: str
    phone: str

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone}


@dataclass
class Cab:
    number: str
    car_type: CarType
    location: Location

    def to_dict(self):
        return {
            "number": self.number,
            "car_type": self.car_type.value,
            "location": self.location.to_dict(),
        }


@dataclass
class Driver:
    """A driver owns exactly one cab."""
    id: str
    name: str
    phone: str
    cab: Cab
    rating: float = 5.0
    is_available: bool = True

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "rating": self.rating,
            "is_available": self.is_available,
            "cab": self.cab.to_dict(),
        }


@dataclass
class Coupon:
    code: str
    discount_type: DiscountType
    value: float
    max_discount: float | None = None  # cap for percentage coupons

    def discount_for(self, amount: float) -> float:
        """Discount to subtract from `amount`. Never more than the amount itself."""
        if self.discount_type == DiscountType.FLAT:
            discount = self.value
        else:
            discount = amount * self.value / 100

        if self.max_discount is not None:
            discount = min(discount, self.max_discount)
        return min(discount, amount)

    def to_dict(self):
        return {
            "code": self.code,
            "discount_type": self.discount_type.value,
            "value": self.value,
            "max_discount": self.max_discount,
        }


@dataclass
class Ride:
    id: str
    user_id: str
    driver_id: str
    requested_car_type: CarType  # what the user asked for (used for billing)
    assigned_car_type: CarType   # what they actually got (may be an upgrade)
    pickup: Location
    drop: Location
    coupon: Coupon | None = None  # copied at booking, so deleting it later is safe
    status: RideStatus = RideStatus.ONGOING
    fare: dict | None = None
    created_at: datetime = field(default_factory=now_utc)
    ended_at: datetime | None = None

    @property
    def is_upgraded(self) -> bool:
        return self.requested_car_type != self.assigned_car_type

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "driver_id": self.driver_id,
            "requested_car_type": self.requested_car_type.value,
            "assigned_car_type": self.assigned_car_type.value,
            "is_upgraded": self.is_upgraded,
            "pickup": self.pickup.to_dict(),
            "drop": self.drop.to_dict(),
            "coupon_code": self.coupon.code if self.coupon else None,
            "status": self.status.value,
            "fare": self.fare,
            "created_at": self.created_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }