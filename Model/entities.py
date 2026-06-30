from dataclasses import dataclass
from datetime import date, time, datetime
from typing import Optional


@dataclass
class Department:
    id: int
    name: str


@dataclass
class Employee:
    id: int
    employee_no: str
    first_name: str
    last_name: str
    department_id: Optional[int]
    department: Optional[str]
    position: Optional[str]
    status: str
    created_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def from_dict(cls, row: dict) -> "Employee":
        return cls(
            id=row.get("id"),
            employee_no=row.get("employee_no"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            department_id=row.get("department_id"),
            department=row.get("department") or row.get("department_name"),
            position=row.get("position"),
            status=row.get("status") or "active",
            created_at=row.get("created_at"),
        )


@dataclass
class AttendanceRecord:
    id: int
    employee_id: int
    date: date
    time_in: Optional[time]
    time_out: Optional[time]
    status: str
    created_at: datetime

    @classmethod
    def from_dict(cls, row: dict) -> "AttendanceRecord":
        return cls(
            id=row.get("id"),
            employee_id=row.get("employee_id"),
            date=row.get("date"),
            time_in=row.get("time_in"),
            time_out=row.get("time_out"),
            status=row.get("status"),
            created_at=row.get("created_at"),
        )


@dataclass
class DashboardSummary:
    total_employees: int
    present_today: int
    late_today: int
    total_today: int
    date: date

    @classmethod
    def from_dict(cls, row: dict) -> "DashboardSummary":
        return cls(
            total_employees=row.get("total_employees", 0),
            present_today=row.get("present_today", 0),
            late_today=row.get("late_today", 0),
            total_today=row.get("total_today", 0),
            date=row.get("date"),
        )


@dataclass
class AttendanceReportRow:
    attendance_date: date
    employee_no: str
    first_name: str
    last_name: str
    department_name: Optional[str]
    time_in: Optional[time]
    time_out: Optional[time]
    status: str

    @classmethod
    def from_dict(cls, row: dict) -> "AttendanceReportRow":
        return cls(
            attendance_date=row.get("attendance_date"),
            employee_no=row.get("employee_no"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            department_name=row.get("department_name"),
            time_in=row.get("time_in"),
            time_out=row.get("time_out"),
            status=row.get("status"),
        )
