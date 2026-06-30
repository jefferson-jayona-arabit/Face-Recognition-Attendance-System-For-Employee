import datetime as dt
from typing import List, Optional, Literal

from DAO.attendance_dao import AttendanceDAO
from DAO.schedule_dao import ScheduleDAO
from Model.entities import AttendanceRecord, DashboardSummary, AttendanceReportRow, WorkSchedule


# Fallback schedule used when no DB schedule is found
_FALLBACK_SCHEDULE = WorkSchedule(
    id=0,
    label="Default (fallback)",
    time_in_start=dt.time(6, 0),
    time_in_end=dt.time(8, 0),
    late_cutoff=dt.time(8, 1),
    time_out_start=dt.time(17, 0),
    time_out_end=dt.time(20, 0),
    is_active=True,
)


class AttendanceController:

    # ── Schedule helpers ─────────────────────────────────────────────────────
    @staticmethod
    def get_active_schedule() -> WorkSchedule:
        sched = ScheduleDAO.get_active_schedule()
        return sched if sched else _FALLBACK_SCHEDULE

    @staticmethod
    def get_current_mode() -> Literal["time_in", "time_out", "closed"]:
        """
        Return which mode the camera should operate in right now.

        time_in  — between time_in_start and time_out_start exclusive
        time_out — between time_out_start and time_out_end
        closed   — outside all windows
        """
        now   = dt.datetime.now().time()
        sched = AttendanceController.get_active_schedule()

        if sched.time_in_start <= now <= sched.time_in_end:
            return "time_in"
        # After time_in_end but before time_out_start → still allow time_in
        # (late arrivals up to time_out_start)
        if sched.time_in_end < now < sched.time_out_start:
            return "time_in"
        if sched.time_out_start <= now <= sched.time_out_end:
            return "time_out"
        return "closed"

    @staticmethod
    def determine_status(check_in_time_str: str, schedule: Optional[WorkSchedule] = None) -> str:
        """Return 'present' or 'late' based on the schedule's late_cutoff."""
        if schedule is None:
            schedule = AttendanceController.get_active_schedule()
        parsed = dt.datetime.strptime(check_in_time_str, "%H:%M:%S").time()
        return "late" if parsed >= schedule.late_cutoff else "present"

    # ── Dashboard ────────────────────────────────────────────────────────────
    @staticmethod
    def get_dashboard_summary() -> Optional[DashboardSummary]:
        today = dt.date.today().isoformat()
        return AttendanceDAO.get_dashboard_summary(today)

    @staticmethod
    def get_recent_attendance(limit: int = 10) -> List[AttendanceReportRow]:
        return AttendanceDAO.get_recent_attendance(limit)

    @staticmethod
    def get_attendance_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        department_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        name_search: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AttendanceReportRow]:
        return AttendanceDAO.get_attendance_report(
            start_date, end_date, department_id, employee_id,
            name_search, status, limit,
        )

    # ── Recording ────────────────────────────────────────────────────────────
    @staticmethod
    def record_attendance(
        employee_id: int,
        check_in_time: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Record time-in for an employee using the active schedule for status."""
        today = dt.date.today().isoformat()
        if check_in_time is None:
            check_in_time = dt.datetime.now().strftime("%H:%M:%S")
        if status is None:
            status = AttendanceController.determine_status(check_in_time)
        return AttendanceDAO.save_attendance(employee_id, today, check_in_time, status)

    @staticmethod
    def record_time_out(employee_id: int, time_out: Optional[str] = None) -> bool:
        """
        Record time-out for today's attendance row.
        Returns False if no time-in row exists or already timed out.
        """
        today = dt.date.today().isoformat()
        if time_out is None:
            time_out = dt.datetime.now().strftime("%H:%M:%S")
        return AttendanceDAO.record_time_out(employee_id, today, time_out)

    @staticmethod
    def has_timed_in(employee_id: int) -> bool:
        today = dt.date.today().isoformat()
        return AttendanceDAO.get_attendance_record(employee_id, today) is not None

    @staticmethod
    def has_timed_out(employee_id: int) -> bool:
        today = dt.date.today().isoformat()
        return AttendanceDAO.has_timed_out(employee_id, today)
