from typing import List, Optional

from DAO.user_dao import UserDAO
from Model.entities import User


class UserController:

    @staticmethod
    def login(username: str, password: str) -> Optional[User]:
        """Return User on success, None on bad credentials."""
        return UserDAO.verify_password(username, password)

    @staticmethod
    def list_users() -> List[User]:
        return UserDAO.get_all_users()

    @staticmethod
    def add_user(username: str, password: str, role: str = "admin",
                 employee_id: Optional[int] = None) -> Optional[int]:
        return UserDAO.add_user(username, password, role, employee_id)

    @staticmethod
    def update_user(user_id: int, username: str, role: str,
                    password: Optional[str] = None) -> bool:
        return UserDAO.update_user(user_id, username, role, password)

    @staticmethod
    def delete_user(user_id: int) -> bool:
        return UserDAO.delete_user(user_id)

    @staticmethod
    def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        return UserDAO.username_exists(username, exclude_id)
