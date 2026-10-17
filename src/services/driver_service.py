from src.exceptions import AlreadyExistsError, NotFoundError
from src.models import Cab, Driver
from src.repository import IdGenerator


class DriverService:
    def __init__(self, driver_repo):
        self.driver_repo = driver_repo
        self.ids = IdGenerator("driver")

    def register(self, name, phone, cab_number, car_type, location, rating=5.0):
        for driver in self.driver_repo.all():
            if driver.phone == phone:
                raise AlreadyExistsError(f"Driver with phone {phone} already exists")
            if driver.cab.number == cab_number:
                raise AlreadyExistsError(f"Cab {cab_number} is already registered")

        cab = Cab(number=cab_number, car_type=car_type, location=location)
        driver = Driver(id=self.ids.next_id(), name=name, phone=phone, cab=cab, rating=rating)
        return self.driver_repo.save(driver.id, driver)

    def get(self, driver_id):
        driver = self.driver_repo.get(driver_id)
        if driver is None:
            raise NotFoundError(f"Driver {driver_id} not found")
        return driver

    def update_location(self, driver_id, location):
        driver = self.get(driver_id)
        driver.cab.location = location
        return driver

    def find_nearest_available(self, pickup, car_type, radius_km):
        """Nearest free driver of this car type within the radius, or None."""
        candidates = [
            driver for driver in self.driver_repo.all()
            if driver.is_available
            and driver.cab.car_type == car_type
            and driver.cab.location.distance_to(pickup) <= radius_km
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda driver: driver.cab.location.distance_to(pickup))