from typing import List, Optional

from db.connection import get_connection
from Model.entities import Department, Employee


class EmployeeDAO:
    @staticmethod
    def get_all_departments() -> List[Department]:
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            return [Department(**row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"[EmployeeDAO] get_all_departments: {exc}")
            return []
        finally:
            conn.close()

    @staticmethod
    def add_employee(employee_no: str, first_name: str, last_name: str, department_id: int, position: str) -> Optional[int]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO employees (employee_no, first_name, last_name, department_id, position) VALUES (%s, %s, %s, %s, %s)",
                (employee_no, first_name, last_name, department_id, position),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as exc:
            print(f"[EmployeeDAO] add_employee: {exc}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def get_all_employees() -> List[Employee]:
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT e.id, e.employee_no, e.first_name, e.last_name,
                       e.department_id, d.name AS department, e.position, e.status, e.created_at
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                ORDER BY e.created_at DESC
                """
            )
            return [Employee.from_dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"[EmployeeDAO] get_all_employees: {exc}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_employee_by_id(employee_id: int) -> Optional[Employee]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT e.*, d.name AS department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.id = %s
                """,
                (employee_id,),
            )
            row = cursor.fetchone()
            return Employee.from_dict(row) if row else None
        except Exception as exc:
            print(f"[EmployeeDAO] get_employee_by_id: {exc}")
            return None
        finally:
            conn.close()

    @staticmethod
    def update_employee(employee_id: int, employee_no: str, first_name: str, last_name: str, department_id: int, position: str, status: str) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE employees
                SET employee_no = %s, first_name = %s, last_name = %s,
                    department_id = %s, position = %s, status = %s
                WHERE id = %s
                """,
                (employee_no, first_name, last_name, department_id, position, status, employee_id),
            )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[EmployeeDAO] update_employee: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_employee(employee_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
            conn.commit()
            return True
        except Exception as exc:
            print(f"[EmployeeDAO] delete_employee: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def employee_no_exists(employee_no: str, exclude_id: int | None = None) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT id FROM employees WHERE employee_no = %s AND id != %s",
                    (employee_no, exclude_id),
                )
            else:
                cursor.execute("SELECT id FROM employees WHERE employee_no = %s", (employee_no,))
            return cursor.fetchone() is not None
        except Exception as exc:
            print(f"[EmployeeDAO] employee_no_exists: {exc}")
            return False
        finally:
            conn.close()

    @staticmethod
    def has_face_encoding(employee_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM face_encodings WHERE employee_id = %s", (employee_id,))
            return cursor.fetchone() is not None
        except Exception as exc:
            print(f"[EmployeeDAO] has_face_encoding: {exc}")
            return False
        finally:
            conn.close()
