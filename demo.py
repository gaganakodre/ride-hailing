"""Walks through every feature by sending API Gateway-style events to the handler.

Run from the project folder:
    python3 demo.py          # runs everything at once
    python3 demo.py --step   # pauses after each request (press Enter to continue)
"""
import json
import logging
import sys

from handler import handle

logging.getLogger().setLevel(logging.WARNING)  # hide the handler's INFO logs to keep output clean
STEP_MODE = "--step" in sys.argv


def call(title, method, resource, path_parameters=None, body=None):
    event = {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": path_parameters or {},
        "body": json.dumps(body) if body is not None else None,
    }
    response = handle(event)
    data = json.loads(response["body"]) if response["body"] else {}

    print(f"\n=== {title} ===")
    print(f"{method} {resource}  ->  {response['statusCode']}")
    if data:
        print(json.dumps(data, indent=2))
    if STEP_MODE:
        input("\n(press Enter for the next step)")
    return data


# 1. Registration
call("1. Register a user", "POST", "/users",
     body={"name": "Asha", "phone": "9000000001"})

call("2. Register a Sedan driver (there are no Hatchbacks, so we can see the upgrade)", "POST", "/drivers",
     body={"name": "Ravi", "phone": "9000000002", "cab_number": "KA01AB1234",
           "car_type": "SEDAN", "location": {"x": 1, "y": 1}})

# 2. Location update
call("3. Update the cab's location", "PUT", "/drivers/{driver_id}/location",
     {"driver_id": "driver_1"}, {"location": {"x": 2, "y": 0}})

# 3. Coupons
call("4. Add a coupon", "POST", "/coupons",
     body={"code": "FLAT20", "discount_type": "FLAT", "value": 20})

# 4. Booking with upgrade and coupon
ride = call("5. Book a Hatchback: none free, so the user is upgraded to a Sedan", "POST", "/rides",
            body={"user_id": "user_1", "pickup": {"x": 0, "y": 0}, "drop": {"x": 10, "y": 0},
                  "car_type": "HATCHBACK", "coupon_code": "FLAT20"})

call("6. User history while the ride is ongoing", "GET", "/users/{user_id}/rides",
     {"user_id": "user_1"})

# 5. End ride and fare
call("7. End the ride: billed at the Hatchback rate, 10 km = 69, minus 20 coupon = 49", "POST",
     "/rides/{ride_id}/end", {"ride_id": ride["id"]})

call("8. Driver history after the ride", "GET", "/drivers/{driver_id}/rides",
     {"driver_id": "driver_1"})

# 6. Cancellation (bonus)
second_ride = call("9. Book another ride (the cab is now at the previous drop point)", "POST", "/rides",
                   body={"user_id": "user_1", "pickup": {"x": 10, "y": 0}, "drop": {"x": 12, "y": 0},
                         "car_type": "SEDAN"})

call("10. Cancel it: free, because it's within 5 minutes of booking", "POST",
     "/rides/{ride_id}/cancel", {"ride_id": second_ride["id"]})

call("11. Delete the coupon", "DELETE", "/coupons/{code}", {"code": "FLAT20"})

# 7. Error handling
call("12. Error: no driver within 5 km of the pickup", "POST", "/rides",
     body={"user_id": "user_1", "pickup": {"x": 100, "y": 100}, "drop": {"x": 101, "y": 100},
           "car_type": "SEDAN"})

call("13. Error: invalid input", "POST", "/rides",
     body={"user_id": "user_1", "car_type": "BUS"})

call("14. Error: ending a ride that is already completed", "POST", "/rides/{ride_id}/end",
     {"ride_id": ride["id"]})

print("\nDemo finished.")