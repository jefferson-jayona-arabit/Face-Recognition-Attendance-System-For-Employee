from typing import List, Optional

from DAO.user_dao import UserDAO
from Model.entities import User
from events import AppEvents


class UserController:

    @staticmethod
    def login(username: str, password: str) -> Optional[User]:
        return UserDAO.verify_password(username, password)

    @staticmethod
    def list_users() -> List[User]:
        return UserDAO.get_all_users()

    @staticmethod
    def add_user(username: str, password: str, role: str = "admin",
                 employee_id: Optional[int] = None) -> Optional[int]:
        result = UserDAO.add_user(username, password, role, employee_id)
        if result:
            AppEvents.emit("user_changed")
        return result

    @staticmethod
    def update_user(user_id: int, username: str, role: str,
                    password: Optional[str] = None) -> bool:
        ok = UserDAO.update_user(user_id, username, role, password)
        if ok:
            AppEvents.emit("user_changed")
        return ok

    @staticmethod
    def delete_user(user_id: int) -> bool:
        ok = UserDAO.delete_user(user_id)
        if ok:
            AppEvents.emit("user_changed")
        return ok

    @staticmethod
    def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        return UserDAO.username_exists(username, exclude_id)
