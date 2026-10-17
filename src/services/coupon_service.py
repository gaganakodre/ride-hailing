from src.exceptions import AlreadyExistsError, InvalidCouponError, NotFoundError, ValidationError
from src.models import Coupon, DiscountType


class CouponService:
    def __init__(self, coupon_repo):
        self.coupon_repo = coupon_repo

    def add(self, code, discount_type, value, max_discount=None):
        code = code.strip().upper()
        if value <= 0:
            raise ValidationError("Coupon value must be greater than 0")
        if discount_type == DiscountType.PERCENT and value > 100:
            raise ValidationError("Percentage coupon cannot be more than 100")
        if self.coupon_repo.get(code):
            raise AlreadyExistsError(f"Coupon {code} already exists")

        coupon = Coupon(code=code, discount_type=discount_type, value=value, max_discount=max_discount)
        return self.coupon_repo.save(code, coupon)

    def delete(self, code):
        if self.coupon_repo.delete(code.strip().upper()) is None:
            raise NotFoundError(f"Coupon {code} not found")

    def get_valid(self, code):
        """Used at booking time. A missing coupon is a bad request, not a 404."""
        coupon = self.coupon_repo.get(code.strip().upper())
        if coupon is None:
            raise InvalidCouponError(f"Coupon {code} is not valid")
        return coupon