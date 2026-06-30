import hashlib
from typing import List, Optional

from db.connection import get_connection
from Model.entities import User


def _hash(password: str) -> str:
    """SHA-256 hash. Replace with bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


class UserDAO:

    @staticmethod
    def get_all_users() -> List[User]:
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, employee_id, username, role, created_at FROM users ORDER BY created_at DESC"
            )
            return [User.from_dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"[UserDAO] get_all_users: {exc}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, employee_id, username, role, created_at FROM users WHERE username = %s",
                (username,),
            )
            row = cursor.fetchone()
            return User.from_dict(row) if row else None
        except Exception as exc:
            print(f"[UserDAO] get_user_by_username: {exc}")
            return None
        finally:
            conn.close()

    @staticmethod
    def verify_password(username: str, password: str) -> Optional[User]:
        """Return the User if credentials match, else None."""
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, employee_id, username, role, created_at, password FROM users WHERE username = %s",
                (username,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            stored = row.get("password", "")
            # Support both plain-text legacy passwords and hashed ones
            match = (stored == _hash(password)) or (stored == password)
            if match:
                row.pop("password", None)
                return User.from_dict(row)
            return None
        except Exception as exc:
            print(f"[UserDAO] verify_password: {exc}")
            return None
        finally:
            conn.close()

    @staticmethod
    def add_user(username: str, password: str, role: str = "admin",
                 employee_id: Optional[int] = None) -> Optional[int]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role, employee_id) VALUES (%s, %s, %s, %s)",
                (username, _hash(password), role, employee_id),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as exc:
            print(f"[UserDAO] add_user: {exc}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def update_user(user_id: int, username: str, role: str,
                    password: Optional[str] = None) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if password:
                cursor.execute(
                    "UPDATE users SET username = %s, role = %s, password = %s WHERE id = %s",
                    (username, role, _hash(password), user_id),
                )
            else:
                cursor.execute(
                    "UPDATE users SET username = %s, role = %s WHERE id = %s",
                    (username, role, user_id),
                )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[UserDAO] update_user: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_user(user_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as exc:
            print(f"[UserDAO] delete_user: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s AND id != %s",
                    (username, exclude_id),
                )
            else:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            return cursor.fetchone() is not None
        except Exception as exc:
            print(f"[UserDAO] username_exists: {exc}")
            return False
        finally:
            conn.close()
