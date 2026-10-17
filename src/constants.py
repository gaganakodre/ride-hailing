import math

from src.models import CarType
from src.pricing import RateCard, Slab

# Drivers farther than this from the pickup point are not considered.
SEARCH_RADIUS_KM = 5.0

FREE_CANCELLATION_MINUTES = 5
CANCELLATION_FEE = 50

# Slab-based rates per car type.
RATE_CARDS = {
    CarType.HATCHBACK: RateCard(
        minimum_fare=50,
        slabs=[Slab(2, 10), Slab(5, 8), Slab(math.inf, 5)],
    ),
    CarType.SEDAN: RateCard(  # assumed rates; the problem only gives Hatchback-style numbers
        minimum_fare=80,
        slabs=[Slab(2, 15), Slab(5, 12), Slab(math.inf, 8)],
    ),
}

# Which car types can serve a request, in order of preference.
# A Hatchback request falls back to a Sedan (billed at Hatchback rates).
CAR_TYPE_FALLBACK = {
    CarType.HATCHBACK: [CarType.HATCHBACK, CarType.SEDAN],
    CarType.SEDAN: [CarType.SEDAN],
}