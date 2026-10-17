from unittest import TestCase

from handler import handle
from src.container import Services
from tests.helpers import make_event, parse_body


class ApiTestCase(TestCase):
    """Calls the API the same way API Gateway would: build an event, call handle()."""

    def setUp(self):
        self.services = Services()  # fresh in-memory state for every test

    def call(self, method, resource, path_parameters=None, body=None):
        response = handle(make_event(method, resource, path_parameters, body), services=self.services)
        return response["statusCode"], parse_body(response)

    # ---------- small helpers to set up data ----------

    def register_user(self, phone="9000000001"):
        return self.call("POST", "/users", body={"name": "Asha", "phone": phone})[1]

    def register_driver(self, phone, car_type, x=1, y=0):
        body = {
            "name": "Ravi",
            "phone": phone,
            "cab_number": f"KA-{phone}",
            "car_type": car_type,
            "location": {"x": x, "y": y},
        }
        return self.call("POST", "/drivers", body=body)[1]

    def book(self, user_id, car_type="HATCHBACK", coupon_code=None, drop_x=10):
        body = {
            "user_id": user_id,
            "pickup": {"x": 0, "y": 0},
            "drop": {"x": drop_x, "y": 0},
            "car_type": car_type,
        }
        if coupon_code:
            body["coupon_code"] = coupon_code
        return self.call("POST", "/rides", body=body)

    def end(self, ride_id):
        return self.call("POST", "/rides/{ride_id}/end", {"ride_id": ride_id})


class TestRegistration(ApiTestCase):
    def test_register_user(self):
        status, body = self.call("POST", "/users", body={"name": "Asha", "phone": "9000000001"})
        self.assertEqual(status, 201)
        self.assertEqual(body["id"], "user_1")

    def test_register_user_with_missing_field(self):
        status, body = self.call("POST", "/users", body={"name": "Asha"})
        self.assertEqual(status, 400)
        self.assertIn("phone", body["message"])

    def test_duplicate_user_phone(self):
        self.register_user()
        status, body = self.call("POST", "/users", body={"name": "Other", "phone": "9000000001"})
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "already_exists")

    def test_register_driver(self):
        driver = self.register_driver("1", "sedan")  # car type is case-insensitive
        self.assertEqual(driver["cab"]["car_type"], "SEDAN")
        self.assertTrue(driver["is_available"])

    def test_register_driver_with_invalid_car_type(self):
        status, body = self.call("POST", "/drivers", body={
            "name": "Ravi", "phone": "1", "cab_number": "KA01",
            "car_type": "BUS", "location": {"x": 0, "y": 0},
        })
        self.assertEqual(status, 400)
        self.assertIn("HATCHBACK", body["message"])

    def test_invalid_json_body(self):
        response = handle({"httpMethod": "POST", "resource": "/users", "body": "{not json"},
                          services=self.services)
        self.assertEqual(response["statusCode"], 400)


class TestDriverLocation(ApiTestCase):
    def test_update_location(self):
        driver = self.register_driver("1", "HATCHBACK")
        status, body = self.call("PUT", "/drivers/{driver_id}/location", {"driver_id": driver["id"]},
                                 {"location": {"x": 3, "y": 4}})
        self.assertEqual(status, 200)
        self.assertEqual(body["cab"]["location"], {"x": 3, "y": 4})

    def test_update_location_of_unknown_driver(self):
        status, _ = self.call("PUT", "/drivers/{driver_id}/location", {"driver_id": "driver_99"},
                              {"location": {"x": 3, "y": 4}})
        self.assertEqual(status, 404)

    def test_moving_a_driver_closer_makes_them_bookable(self):
        user = self.register_user()
        driver = self.register_driver("1", "HATCHBACK", x=50)
        self.assertEqual(self.book(user["id"])[0], 409)  # too far

        self.call("PUT", "/drivers/{driver_id}/location", {"driver_id": driver["id"]},
                  {"location": {"x": 2, "y": 0}})
        self.assertEqual(self.book(user["id"])[0], 201)


class TestBookAndEndRide(ApiTestCase):
    def test_full_ride_flow(self):
        user = self.register_user()
        driver = self.register_driver("1", "HATCHBACK")

        status, ride = self.book(user["id"])
        self.assertEqual(status, 201)
        self.assertEqual(ride["driver_id"], driver["id"])
        self.assertEqual(ride["status"], "ONGOING")

        status, ended = self.end(ride["id"])
        self.assertEqual(status, 200)
        self.assertEqual(ended["status"], "COMPLETED")
        self.assertEqual(ended["fare"]["final_fare"], 69)  # 10 km Hatchback

    def test_upgrade_to_sedan_at_hatchback_price(self):
        user = self.register_user()
        self.register_driver("1", "SEDAN")

        _, ride = self.book(user["id"], car_type="HATCHBACK")
        self.assertTrue(ride["is_upgraded"])
        self.assertEqual(ride["assigned_car_type"], "SEDAN")

        _, ended = self.end(ride["id"])
        self.assertEqual(ended["fare"]["billed_car_type"], "HATCHBACK")
        self.assertEqual(ended["fare"]["final_fare"], 69)

    def test_sedan_rates(self):
        user = self.register_user()
        self.register_driver("1", "SEDAN")
        _, ride = self.book(user["id"], car_type="SEDAN")
        _, ended = self.end(ride["id"])
        self.assertEqual(ended["fare"]["final_fare"], 106)

    def test_short_ride_pays_minimum_fare(self):
        user = self.register_user()
        self.register_driver("1", "HATCHBACK")
        _, ride = self.book(user["id"], drop_x=1)
        _, ended = self.end(ride["id"])
        self.assertEqual(ended["fare"]["final_fare"], 50)

    def test_no_driver_available(self):
        user = self.register_user()
        status, body = self.book(user["id"])
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "no_driver_available")

    def test_booking_for_unknown_user(self):
        self.register_driver("1", "HATCHBACK")
        status, _ = self.book("user_99")
        self.assertEqual(status, 404)

    def test_booking_with_missing_pickup(self):
        user = self.register_user()
        status, body = self.call("POST", "/rides", body={"user_id": user["id"], "car_type": "SEDAN"})
        self.assertEqual(status, 400)
        self.assertIn("pickup", body["message"])

    def test_end_unknown_ride(self):
        self.assertEqual(self.end("ride_99")[0], 404)

    def test_end_ride_twice(self):
        user = self.register_user()
        self.register_driver("1", "HATCHBACK")
        _, ride = self.book(user["id"])
        self.end(ride["id"])
        status, body = self.end(ride["id"])
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state")


class TestCoupons(ApiTestCase):
    def add_coupon(self, code, discount_type, value, max_discount=None):
        body = {"code": code, "discount_type": discount_type, "value": value}
        if max_discount is not None:
            body["max_discount"] = max_discount
        return self.call("POST", "/coupons", body=body)

    def test_add_and_delete_coupon(self):
        status, coupon = self.add_coupon("flat30", "FLAT", 30)
        self.assertEqual(status, 201)
        self.assertEqual(coupon["code"], "FLAT30")

        status, _ = self.call("DELETE", "/coupons/{code}", {"code": "FLAT30"})
        self.assertEqual(status, 204)

    def test_delete_unknown_coupon(self):
        status, _ = self.call("DELETE", "/coupons/{code}", {"code": "NOPE"})
        self.assertEqual(status, 404)

    def test_duplicate_coupon(self):
        self.add_coupon("FLAT30", "FLAT", 30)
        status, _ = self.add_coupon("FLAT30", "FLAT", 50)
        self.assertEqual(status, 409)

    def test_ride_with_percent_coupon(self):
        user = self.register_user()
        self.register_driver("1", "HATCHBACK")
        self.add_coupon("HALF", "PERCENT", 50, max_discount=20)

        _, ride = self.book(user["id"], coupon_code="HALF")
        _, ended = self.end(ride["id"])

        self.assertEqual(ended["fare"]["base_fare"], 69)
        self.assertEqual(ended["fare"]["discount"], 20)
        self.assertEqual(ended["fare"]["final_fare"], 49)

    def test_invalid_coupon_rejects_booking(self):
        user = self.register_user()
        self.register_driver("1", "HATCHBACK")
        status, body = self.book(user["id"], coupon_code="NOPE")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_coupon")


class TestRideHistory(ApiTestCase):
    def test_user_and_driver_history(self):
        user = self.register_user()
        driver = self.register_driver("1", "HATCHBACK")
        # Short first ride: after it ends, the cab is at x=2, still inside the 5 km radius.
        _, first = self.book(user["id"], drop_x=2)
        self.end(first["id"])
        _, second = self.book(user["id"])

        status, user_history = self.call("GET", "/users/{user_id}/rides", {"user_id": user["id"]})
        self.assertEqual(status, 200)
        self.assertEqual([r["id"] for r in user_history["completed"]], [first["id"]])
        self.assertEqual([r["id"] for r in user_history["ongoing"]], [second["id"]])

        _, driver_history = self.call("GET", "/drivers/{driver_id}/rides", {"driver_id": driver["id"]})
        self.assertEqual(len(driver_history["completed"]), 1)
        self.assertEqual(len(driver_history["ongoing"]), 1)

    def test_history_of_unknown_user(self):
        status, _ = self.call("GET", "/users/{user_id}/rides", {"user_id": "user_99"})
        self.assertEqual(status, 404)