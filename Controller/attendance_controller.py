import datetime as dt
from typing import List, Optional

from DAO.attendance_dao import AttendanceDAO
from Model.entities import AttendanceRecord, DashboardSummary, AttendanceReportRow


class AttendanceController:
    @staticmethod
    def get_dashboard_summary() -> Optional[DashboardSummary]:
        today = dt.date.today().isoformat()
        return AttendanceDAO.get_dashboard_summary(today)

    @staticmethod
    def get_recent_attendance(limit: int = 10) -> List[AttendanceReportRow]:
        return AttendanceDAO.get_recent_attendance(limit)

    @staticmethod
    def get_attendance_report(start_date: Optional[str] = None, end_date: Optional[str] = None, department_id: Optional[int] = None, employee_id: Optional[int] = None) -> List[AttendanceReportRow]:
        return AttendanceDAO.get_attendance_report(start_date, end_date, department_id, employee_id)

    @staticmethod
    def record_attendance(employee_id: int, check_in_time: Optional[str] = None, status: Optional[str] = None) -> bool:
        today = dt.date.today().isoformat()
        if check_in_time is None:
            check_in_time = dt.datetime.now().strftime("%H:%M:%S")
        if status is None:
            parsed_time = dt.datetime.strptime(check_in_time, "%H:%M:%S").time()
            status = "late" if parsed_time > dt.time(9, 0) else "present"
        return AttendanceDAO.save_attendance(employee_id, today, check_in_time, status)
