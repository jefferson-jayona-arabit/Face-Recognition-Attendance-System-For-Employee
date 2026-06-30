from typing import List, Optional

from DAO.employee_dao import EmployeeDAO
from Model.entities import Department, Employee


class EmployeeController:
    @staticmethod
    def list_departments() -> List[Department]:
        return EmployeeDAO.get_all_departments()

    @staticmethod
    def list_employees() -> List[Employee]:
        return EmployeeDAO.get_all_employees()

    @staticmethod
    def get_employee(employee_id: int) -> Optional[Employee]:
        return EmployeeDAO.get_employee_by_id(employee_id)

    @staticmethod
    def save_employee(employee_no: str, first_name: str, last_name: str, department_id: int, position: str, employee_id: Optional[int] = None, status: str = "active") -> Optional[int]:
        if employee_id:
            success = EmployeeDAO.update_employee(employee_id, employee_no, first_name, last_name, department_id, position, status)
            return employee_id if success else None
        return EmployeeDAO.add_employee(employee_no, first_name, last_name, department_id, position)

    @staticmethod
    def delete_employee(employee_id: int) -> bool:
        return EmployeeDAO.delete_employee(employee_id)

    @staticmethod
    def employee_no_exists(employee_no: str, exclude_id: Optional[int] = None) -> bool:
        return EmployeeDAO.employee_no_exists(employee_no, exclude_id)

    @staticmethod
    def employee_has_face_encoding(employee_id: int) -> bool:
        return EmployeeDAO.has_face_encoding(employee_id)
