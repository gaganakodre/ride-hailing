from src.controllers.base_controller import BaseController
from src.models import DiscountType
from utils.status_codes import StatusCodes


class AddCouponController(BaseController):
    resource = "coupon"

    def process(self):
        coupon = self.services.coupon_service.add(
            code=self.get_string("code"),
            discount_type=self.get_enum("discount_type", DiscountType),
            value=self.get_number("value"),
            max_discount=self.get_number("max_discount", required=False),
        )
        return StatusCodes.generate_success(201, coupon.to_dict())


class DeleteCouponController(BaseController):
    resource = "coupon"

    def process(self):
        self.services.coupon_service.delete(self.path_parameters.get("code"))
        return StatusCodes.generate_success(204)