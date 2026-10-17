# Ride Hailing Backend: Plan

## Scope
Mandatory requirements only:
- Register a user and a driver (each driver has one cab)
- Update a cab's location
- Book a ride if a driver is available within a radius
- End a ride and get its cost
- Tiered pricing, with different rates for Sedan and Hatchback
- Upgrade Hatchback to Sedan at no extra cost if no Hatchback is free
- Coupons: add, delete, and apply a valid one when booking
- Ride history (ongoing and completed) for users and drivers

## Assumptions
- Locations are 2D points `{x, y}` in km; distance is a straight line (Euclidean).
- Drop location is given at booking; ride distance = pickup to drop.
- Search radius is fixed at 5 km (configurable in `constants.py`).
- Pricing is slab-based, like income tax:
  - Hatchback: min ₹50; first 2 km ₹10/km, 2–5 km ₹8/km, beyond 5 km ₹5/km
  - Sedan (assumed rates): min ₹80; first 2 km ₹15/km, 2–5 km ₹12/km, beyond 5 km ₹8/km
  - Example: 10 km Hatchback = 2×10 + 3×8 + 5×5 = ₹69
- An upgraded ride is billed at the requested (Hatchback) rate.
- Coupons are flat or percentage, with an optional max discount.
  The coupon is validated at booking and stored on the ride, so deleting it
  mid-ride does not affect that ride. Final fare never goes below ₹0.
- A user or a driver can have only one ongoing ride at a time.
- Storage is in memory (dicts), so data resets on restart.

## Design
Layered, so each part has one job:

```
HTTP (Flask) → handler (router) → controllers → services → repository
```

- **handler**: matches method + path to a controller (like an API Gateway → Lambda router).
- **controllers**: parse and validate input, call a service, return a status code. No business logic.
- **services**: all business rules (booking, pricing, upgrade, coupons).
- **repository**: in-memory storage. Could be swapped for a database without changing services.

## API
| Method | Path | Purpose |
|---|---|---|
| POST | /users | Register user |
| POST | /drivers | Register driver with cab |
| PUT | /drivers/{driver_id}/location | Update cab location |
| POST | /rides | Book a ride |
| POST | /rides/{ride_id}/end | End ride, returns fare |
| GET | /users/{user_id}/rides | User ride history |
| GET | /drivers/{driver_id}/rides | Driver ride history |
| POST | /coupons | Add coupon |
| DELETE | /coupons/{code} | Delete coupon |

## Error codes
- 400: invalid input or invalid coupon
- 404: user, driver, ride or coupon not found
- 409: no driver available, already exists, or ride not in the right state

## Build order (one commit each)
1. Plan
2. Project skeleton
3. Domain models and exceptions
4. Tiered pricing + tests
5. User, driver and coupon services
6. Ride booking and ending (with upgrade and coupon)
7. Ride history
8. REST layer (router, controllers, Flask app)
9. API tests
10. README