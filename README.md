# Ride Hailing Backend

This is the backend for a simple ride-hailing service, similar to Uber. Users can book a cab,
drivers keep their cab's location up to date, and when a ride ends the user is charged using
tiered pricing that depends on the type of car.

The API is built the way I build APIs at work: a single Lambda-style `handle(event, context)`
function receives API Gateway-style requests and routes them to controllers. It uses only the
Python standard library, so there is nothing to install.

## Getting started

You need Python 3.10 or newer. From the project folder, run the tests:

```bash
python3 -m unittest -v
```

To try a request yourself, open a Python shell in the project folder and send an event to the handler:

```python
import json
from handler import handle

event = {
    "httpMethod": "POST",
    "resource": "/users",
    "body": json.dumps({"name": "Asha", "phone": "9000000001"}),
}
print(handle(event))
# {'statusCode': 201, 'body': '{"id": "user_1", "name": "Asha", "phone": "9000000001"}'}
```

Data is kept in memory, so it lasts as long as the Python process and resets when you restart.

## What it can do

- Register users, and register drivers along with their cab (Sedan or Hatchback).
- Update where a cab currently is.
- Book a ride. The system finds the nearest free driver within 5 km of the pickup point.
  If a Hatchback is requested but none is free, the user gets a Sedan at no extra cost.
- End a ride and get the fare.
- Add and delete coupon codes, and apply a coupon when booking to get a discount.
- See ride history for a user or a driver, split into ongoing and completed rides.

## How the code is organised

Every request goes through the same path:

```
event → handler → controller → service → repository
```

The **handler** (`handler.py`) looks at the request's path and method and picks the right
controller from `CONTROLLER_MAP` in `src/routes.py`.

The **controllers** (`src/controllers/`) read and check the input, call a service, and return a
response with a status code. They don't contain any business rules.

The **services** (`src/services/`) hold all the business rules: how a driver is chosen, when a
ride can be booked or ended, how coupons work, and how history is built.

The **repository** (`src/repository.py`) stores data in memory. It is kept behind a small
interface (`save`, `get`, `delete`, `all`), so it could be replaced by a real database without
changing the services.

Services never deal with HTTP. When something goes wrong they raise a plain error such as
`NoDriverAvailableError`, and the base controller turns it into the right status code. That
mapping lives in one place, `ERROR_MAP` in `src/controllers/base_controller.py`.

## The API

| Method | Path | What it does |
|---|---|---|
| POST | `/users` | Register a user |
| POST | `/drivers` | Register a driver and their cab |
| PUT | `/drivers/{driver_id}/location` | Update a cab's location |
| POST | `/rides` | Book a ride |
| POST | `/rides/{ride_id}/end` | End a ride and get the fare |
| GET | `/users/{user_id}/rides` | A user's ride history |
| GET | `/drivers/{driver_id}/rides` | A driver's ride history |
| POST | `/coupons` | Add a coupon |
| DELETE | `/coupons/{code}` | Delete a coupon |

A booking request looks like this:

```json
{
  "user_id": "user_1",
  "pickup": {"x": 0, "y": 0},
  "drop": {"x": 10, "y": 0},
  "car_type": "HATCHBACK",
  "coupon_code": "FLAT20"
}
```

When that ride ends, the response includes the fare breakdown:

```json
"fare": {
  "distance_km": 10.0,
  "billed_car_type": "HATCHBACK",
  "base_fare": 69.0,
  "discount": 20.0,
  "final_fare": 49.0
}
```

If something goes wrong, you get a clear status code and message: 400 for bad input or an
invalid coupon, 404 when something doesn't exist, 405 for the wrong HTTP method, and 409 when
no driver is available, something already exists, or a ride is in the wrong state (for example,
ending it twice).

## How pricing works

Fares are calculated in slabs, the same way income tax works: each kilometre is charged at the
rate of the slab it falls in. If the total is below the minimum fare, the minimum is charged.

For a Hatchback, the minimum is ₹50. The first 2 km cost ₹10/km, 2 to 5 km cost ₹8/km, and
anything beyond 5 km costs ₹5/km. So a 10 km ride costs 2×10 + 3×8 + 5×5 = ₹69.

For a Sedan, the problem didn't give rates, so I assumed a minimum of ₹80 and ₹15, ₹12 and
₹8 per km for the same slabs. The rates live in `src/constants.py`, so changing them, or adding a
new car type, doesn't require touching the pricing logic.

A coupon is applied after the minimum fare. It can be a flat amount or a percentage with an
optional cap, and the final fare never goes below ₹0.

## Decisions and assumptions

A few choices are worth calling out (the full list is in [PLAN.md](PLAN.md)):

- **The upgrade really is free.** Each ride remembers both the car type the user asked for and
  the one they got. The fare is always based on what they asked for.
- **Coupons are checked at booking time,** before a driver is reserved, so an invalid code never
  leaves a driver stuck as busy. The coupon is also saved on the ride, so deleting it later
  doesn't change the price of a ride that's already in progress.
- **Locations are simple x/y points in km,** and distance is measured in a straight line. The
  drop location is given when booking.
- **When a ride ends,** the driver becomes free again and their cab is moved to the drop point,
  since that's where the cab now is.
- A user can only have one ongoing ride at a time.

##To see every feature in action, run the demo. `--step` pauses after each request:

```bash
python3 demo.py --step
```

## What I would do next

- **Handle two people booking at the same time.** Right now, finding a driver and marking them
  busy are two separate steps, so two simultaneous requests could pick the same driver. A lock
  around that step, or a conditional update in the database, would fix it.
- **Search drivers more efficiently.** The current search checks every driver. At real scale I
  would use a geo index such as PostGIS or geohash buckets.
- **Add the bonus features:** surge pricing, a switchable driver-matching strategy (drivers
  already have a rating stored), and ride cancellation with a fee.
- **Store data in a real database** by replacing the in-memory repository.

## How I used AI

I used Claude to write the code, working from a plan I wrote first. I chose the architecture: a
Lambda-style handler with thin controllers, the same pattern I use at work, instead of Flask.
I built it one step at a time, adding each part myself, running the tests and committing only
when they passed. I kept the scope to the mandatory requirements so the core would be solid.
I reviewed each part before committing, so I can explain how every piece works and why it was
built that way.
