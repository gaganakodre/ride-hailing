from src.controllers.base_controller import BaseController
from utils.status_codes import StatusCodes


class RegisterUserController(BaseController):
    resource = "user"

    def process(self):
        user = self.services.user_service.register(
            name=self.get_string("name"),
            phone=self.get_string("phone"),
        )
        return StatusCodes.generate_success(201, user.to_dict())


class UserRideHistoryController(BaseController):
    resource = "ride"

    def process(self):
        history = self.services.ride_service.get_user_history(self.path_parameters.get("user_id"))
        return StatusCodes.generate_success(200, self.history_to_dict(history))