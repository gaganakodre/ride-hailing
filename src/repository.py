import itertools


class InMemoryRepository:
    """Stores objects by key in a dict. In production this would be a database table (e.g. RDS)."""

    def __init__(self):
        self._items = {}

    def save(self, key, item):
        self._items[key] = item
        return item

    def get(self, key):
        return self._items.get(key)

    def delete(self, key):
        return self._items.pop(key, None)

    def all(self):
        return list(self._items.values())


class IdGenerator:
    """Readable sequential ids such as user_1, user_2 (easier to follow in tests and demos than UUIDs)."""

    def __init__(self, prefix):
        self.prefix = prefix
        self._counter = itertools.count(1)

    def next_id(self):
        return f"{self.prefix}_{next(self._counter)}"