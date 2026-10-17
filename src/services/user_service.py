from src.exceptions import AlreadyExistsError, NotFoundError
from src.models import User
from src.repository import IdGenerator


class UserService:
    def __init__(self, user_repo):
        self.user_repo = user_repo
        self.ids = IdGenerator("user")

    def register(self, name, phone):
        if any(user.phone == phone for user in self.user_repo.all()):
            raise AlreadyExistsError(f"User with phone {phone} already exists")

        user = User(id=self.ids.next_id(), name=name, phone=phone)
        return self.user_repo.save(user.id, user)

    def get(self, user_id):
        user = self.user_repo.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user