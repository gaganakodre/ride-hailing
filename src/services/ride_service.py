from src.constants import CAR_TYPE_FALLBACK, SEARCH_RADIUS_KM
from src.exceptions import InvalidRideStateError, NoDriverAvailableError, NotFoundError
from src.models import Ride, RideStatus, now_utc
from src.repository import IdGenerator


class RideService:
    def __init__(self, ride_repo, user_service, driver_service, coupon_service, pricing_service,
                 radius_km=SEARCH_RADIUS_KM):
        self.ride_repo = ride_repo
        self.user_service = user_service
        self.driver_service = driver_service
        self.coupon_service = coupon_service
        self.pricing_service = pricing_service
        self.radius_km = radius_km
        self.ids = IdGenerator("ride")

    def book_ride(self, user_id, pickup, drop, car_type, coupon_code=None):
        self.user_service.get(user_id)  # raises NotFoundError if the user doesn't exist
        if self._has_ongoing_ride(user_id):
            raise InvalidRideStateError(f"User {user_id} already has an ongoing ride")

        # Validate the coupon before reserving a driver, so a bad code never blocks a driver.
        coupon = self.coupon_service.get_valid(coupon_code) if coupon_code else None

        driver = self._find_driver(pickup, car_type)
        if driver is None:
            raise NoDriverAvailableError(f"No driver available within {self.radius_km} km")

        driver.is_available = False
        ride = Ride(
            id=self.ids.next_id(),
            user_id=user_id,
            driver_id=driver.id,
            requested_car_type=car_type,
            assigned_car_type=driver.cab.car_type,
            pickup=pickup,
            drop=drop,
            coupon=coupon,
        )
        return self.ride_repo.save(ride.id, ride)

    def end_ride(self, ride_id):
        ride = self.get(ride_id)
        if ride.status != RideStatus.ONGOING:
            raise InvalidRideStateError(f"Ride {ride_id} is already {ride.status.value}")

        distance_km = ride.pickup.distance_to(ride.drop)
        # Billed at the REQUESTED car type, so an upgrade costs the user nothing extra.
        ride.fare = self.pricing_service.calculate_fare(distance_km, ride.requested_car_type, ride.coupon)
        ride.status = RideStatus.COMPLETED
        ride.ended_at = now_utc()

        driver = self.driver_service.get(ride.driver_id)
        driver.cab.location = ride.drop  # the cab is now where the ride ended
        driver.is_available = True
        return ride

    def get(self, ride_id):
        ride = self.ride_repo.get(ride_id)
        if ride is None:
            raise NotFoundError(f"Ride {ride_id} not found")
        return ride

    def _find_driver(self, pickup, requested_car_type):
        """Try the requested car type first, then its fallbacks (Hatchback -> Sedan)."""
        for car_type in CAR_TYPE_FALLBACK[requested_car_type]:
            driver = self.driver_service.find_nearest_available(pickup, car_type, self.radius_km)
            if driver:
                return driver
        return None

    def _has_ongoing_ride(self, user_id):
        return any(
            ride.user_id == user_id and ride.status == RideStatus.ONGOING
            for ride in self.ride_repo.all()
        )