from src.controllers.base_controller import BaseController
from src.exceptions import ValidationError
from src.models import CarType
from utils.status_codes import StatusCodes


class RegisterDriverController(BaseController):
    resource = "driver"

    def process(self):
        rating = self.get_number("rating", required=False, default=5.0)
        if not 1 <= rating <= 5:
            raise ValidationError("'rating' must be between 1 and 5")

        driver = self.services.driver_service.register(
            name=self.get_string("name"),
            phone=self.get_string("phone"),
            cab_number=self.get_string("cab_number"),
            car_type=self.get_enum("car_type", CarType),
            location=self.get_location("location"),
            rating=rating,
        )
        return StatusCodes.generate_success(201, driver.to_dict())


class UpdateDriverLocationController(BaseController):
    resource = "driver"

    def process(self):
        driver = self.services.driver_service.update_location(
            driver_id=self.path_parameters.get("driver_id"),
            location=self.get_location("location"),
        )
        return StatusCodes.generate_success(200, driver.to_dict())


class DriverRideHistoryController(BaseController):
    resource = "ride"

    def process(self):
        history = self.services.ride_service.get_driver_history(self.path_parameters.get("driver_id"))
        return StatusCodes.generate_success(200, self.history_to_dict(history))