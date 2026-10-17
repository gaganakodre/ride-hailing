from src.controllers.coupon_controllers import AddCouponController, DeleteCouponController
from src.controllers.driver_controllers import (
    DriverRideHistoryController,
    RegisterDriverController,
    UpdateDriverLocationController,
)
from src.controllers.ride_controllers import BookRideController, EndRideController
from src.controllers.user_controllers import RegisterUserController, UserRideHistoryController

# Maps an API Gateway resource to the controller class for each HTTP method.
CONTROLLER_MAP = {
    "/users": {"POST": RegisterUserController},
    "/users/{user_id}/rides": {"GET": UserRideHistoryController},
    "/drivers": {"POST": RegisterDriverController},
    "/drivers/{driver_id}/location": {"PUT": UpdateDriverLocationController},
    "/drivers/{driver_id}/rides": {"GET": DriverRideHistoryController},
    "/rides": {"POST": BookRideController},
    "/rides/{ride_id}/end": {"POST": EndRideController},
    "/coupons": {"POST": AddCouponController},
    "/coupons/{code}": {"DELETE": DeleteCouponController},
}