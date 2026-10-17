from datetime import timedelta
from unittest import TestCase

from handler import handle
from src.cancellation import TimeBasedCancellationPolicy
from src.container import Services
from src.models import CarType, Location, Ride, RideStatus
from tests.helpers import make_event, parse_body


class TestTimeBasedCancellationPolicy(TestCase):
    def setUp(self):
        self.policy = TimeBasedCancellationPolicy(free_window_minutes=5, fee=50)
        self.ride = Ride("ride_1", "user_1", "driver_1", CarType.HATCHBACK, CarType.HATCHBACK,
                         Location(0, 0), Location(1, 0))

    def test_free_within_window(self):
        cancelled_at = self.ride.created_at + timedelta(minutes=4)
        self.assertEqual(self.policy.fee_for(self.ride, cancelled_at), 0)

    def test_exactly_at_window_is_still_free(self):
        cancelled_at = self.ride.created_at + timedelta(minutes=5)
        self.assertEqual(self.policy.fee_for(self.ride, cancelled_at), 0)

    def test_fee_after_window(self):
        cancelled_at = self.ride.created_at + timedelta(minutes=6)
        self.assertEqual(self.policy.fee_for(self.ride, cancelled_at), 50)


class TestCancelRideApi(TestCase):
    def setUp(self):
        self.services = Services()
        self.user = self.call("POST", "/users", body={"name": "Asha", "phone": "9000000001"})[1]
        self.driver = self.call("POST", "/drivers", body={
            "name": "Ravi", "phone": "9000000002", "cab_number": "KA01",
            "car_type": "HATCHBACK", "location": {"x": 1, "y": 0},
        })[1]
        self.ride = self.call("POST", "/rides", body={
            "user_id": self.user["id"], "pickup": {"x": 0, "y": 0},
            "drop": {"x": 10, "y": 0}, "car_type": "HATCHBACK",
        })[1]

    def call(self, method, resource, path_parameters=None, body=None):
        response = handle(make_event(method, resource, path_parameters, body), services=self.services)
        return response["statusCode"], parse_body(response)

    def cancel(self, ride_id):
        return self.call("POST", "/rides/{ride_id}/cancel", {"ride_id": ride_id})

    def test_cancel_right_after_booking_is_free(self):
        status, ride = self.cancel(self.ride["id"])

        self.assertEqual(status, 200)
        self.assertEqual(ride["status"], "CANCELLED")
        self.assertEqual(ride["cancellation_fee"], 0)

    def test_cancel_late_charges_fee(self):
        stored_ride = self.services.ride_service.get(self.ride["id"])
        stored_ride.created_at -= timedelta(minutes=10)  # pretend it was booked 10 minutes ago

        _, ride = self.cancel(self.ride["id"])
        self.assertEqual(ride["cancellation_fee"], 50)

    def test_driver_is_free_again_after_cancel(self):
        self.cancel(self.ride["id"])
        driver = self.services.driver_service.get(self.driver["id"])
        self.assertTrue(driver.is_available)
        self.assertEqual(driver.cab.location, Location(1, 0))  # did not move to the drop

    def test_user_can_book_again_after_cancel(self):
        self.cancel(self.ride["id"])
        status, _ = self.call("POST", "/rides", body={
            "user_id": self.user["id"], "pickup": {"x": 0, "y": 0},
            "drop": {"x": 3, "y": 0}, "car_type": "HATCHBACK",
        })
        self.assertEqual(status, 201)

    def test_cannot_cancel_twice(self):
        self.cancel(self.ride["id"])
        status, body = self.cancel(self.ride["id"])
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state")

    def test_cannot_end_a_cancelled_ride(self):
        self.cancel(self.ride["id"])
        status, _ = self.call("POST", "/rides/{ride_id}/end", {"ride_id": self.ride["id"]})
        self.assertEqual(status, 409)

    def test_cancelled_ride_shows_in_history(self):
        self.cancel(self.ride["id"])
        _, history = self.call("GET", "/users/{user_id}/rides", {"user_id": self.user["id"]})
        self.assertEqual([r["id"] for r in history["cancelled"]], [self.ride["id"]])
        self.assertEqual(history["ongoing"], [])

    def test_cancel_unknown_ride(self):
        self.assertEqual(self.cancel("ride_99")[0], 404)