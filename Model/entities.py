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
class User:
    id: int
    employee_id: Optional[int]
    username: str
    role: str
    created_at: Optional[datetime]

    @classmethod
    def from_dict(cls, row: dict) -> "User":
        return cls(
            id=row.get("id"),
            employee_id=row.get("employee_id"),
            username=row.get("username"),
            role=row.get("role", "admin"),
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


@dataclass
class WorkSchedule:
    id: int
    label: str
    time_in_start: time
    time_in_end: time
    late_cutoff: time
    time_out_start: time
    time_out_end: time
    is_active: bool

    def _to_time(self, val) -> time:
        """Accept time, timedelta, or HH:MM:SS string."""
        if isinstance(val, time):
            return val
        from datetime import timedelta
        if isinstance(val, timedelta):
            total = int(val.total_seconds())
            return time(total // 3600, (total % 3600) // 60, total % 60)
        if isinstance(val, str):
            parts = val.split(":")
            return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
        return val

    def __post_init__(self):
        self.time_in_start  = self._to_time(self.time_in_start)
        self.time_in_end    = self._to_time(self.time_in_end)
        self.late_cutoff    = self._to_time(self.late_cutoff)
        self.time_out_start = self._to_time(self.time_out_start)
        self.time_out_end   = self._to_time(self.time_out_end)

    @property
    def time_in_start_str(self) -> str:
        return self.time_in_start.strftime("%H:%M")

    @property
    def time_in_end_str(self) -> str:
        return self.time_in_end.strftime("%H:%M")

    @property
    def late_cutoff_str(self) -> str:
        return self.late_cutoff.strftime("%H:%M")

    @property
    def time_out_start_str(self) -> str:
        return self.time_out_start.strftime("%H:%M")

    @property
    def time_out_end_str(self) -> str:
        return self.time_out_end.strftime("%H:%M")

    @classmethod
    def from_dict(cls, row: dict) -> "WorkSchedule":
        return cls(
            id=row.get("id"),
            label=row.get("label", "Default Schedule"),
            time_in_start=row.get("time_in_start"),
            time_in_end=row.get("time_in_end"),
            late_cutoff=row.get("late_cutoff"),
            time_out_start=row.get("time_out_start"),
            time_out_end=row.get("time_out_end"),
            is_active=bool(row.get("is_active", True)),
        )
