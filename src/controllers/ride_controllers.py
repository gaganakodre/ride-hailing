from src.controllers.base_controller import BaseController
from src.models import CarType
from utils.status_codes import StatusCodes


class BookRideController(BaseController):
    resource = "ride"

    def process(self):
        ride = self.services.ride_service.book_ride(
            user_id=self.get_string("user_id"),
            pickup=self.get_location("pickup"),
            drop=self.get_location("drop"),
            car_type=self.get_enum("car_type", CarType),
            coupon_code=self.get_string("coupon_code", required=False),
        )
        return StatusCodes.generate_success(201, ride.to_dict())


class EndRideController(BaseController):
    resource = "ride"

    def process(self):
        ride = self.services.ride_service.end_ride(self.path_parameters.get("ride_id"))
        return StatusCodes.generate_success(200, ride.to_dict())