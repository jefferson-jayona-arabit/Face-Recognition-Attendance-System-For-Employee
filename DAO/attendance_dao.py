from typing import List, Optional
from db.connection import get_connection
from Model.entities import AttendanceRecord, DashboardSummary, AttendanceReportRow


class AttendanceDAO:
    @staticmethod
    def get_attendance_record(employee_id: int, attendance_date: str):
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, employee_id, date, time_in, time_out, status, created_at "
                "FROM attendance WHERE employee_id = %s AND date = %s",
                (employee_id, attendance_date),
            )
            row = cursor.fetchone()
            return AttendanceRecord.from_dict(row) if row else None
        except Exception as exc:
            print(f"[AttendanceDAO] get_attendance_record: {exc}")
            return None
        finally:
            conn.close()

    @staticmethod
    def has_timed_out(employee_id: int, attendance_date: str) -> bool:
        """Return True if a time_out has already been recorded today."""
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT time_out FROM attendance "
                "WHERE employee_id = %s AND date = %s AND time_out IS NOT NULL",
                (employee_id, attendance_date),
            )
            return cursor.fetchone() is not None
        except Exception as exc:
            print(f"[AttendanceDAO] has_timed_out: {exc}")
            return False
        finally:
            conn.close()

    @staticmethod
    def record_time_out(employee_id: int, attendance_date: str, time_out: str) -> bool:
        """Write time_out on the existing attendance row for today."""
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            # Only update if a time_in row exists and time_out is still NULL
            cursor.execute(
                "UPDATE attendance SET time_out = %s "
                "WHERE employee_id = %s AND date = %s AND time_out IS NULL",
                (time_out, employee_id, attendance_date),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"[AttendanceDAO] record_time_out: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def save_attendance(employee_id: int, attendance_date: str,
                        check_in_time: str, status: str) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            existing = AttendanceDAO.get_attendance_record(employee_id, attendance_date)
            cursor = conn.cursor()
            if existing:
                cursor.execute(
                    "UPDATE attendance SET time_in = COALESCE(time_in, %s), status = %s "
                    "WHERE id = %s",
                    (check_in_time, status, existing.id),
                )
            else:
                cursor.execute(
                    "INSERT INTO attendance (employee_id, date, time_in, status) "
                    "VALUES (%s, %s, %s, %s)",
                    (employee_id, attendance_date, check_in_time, status),
                )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[AttendanceDAO] save_attendance: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_recent_attendance(limit: int = 10) -> List[AttendanceReportRow]:
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT a.id, a.date AS attendance_date, a.time_in, a.time_out, a.status,
                       e.employee_no, e.first_name, e.last_name, d.name AS department_name
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                ORDER BY a.date DESC, a.time_in DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [AttendanceReportRow.from_dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"[AttendanceDAO] get_recent_attendance: {exc}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_dashboard_summary(today: str) -> Optional[DashboardSummary]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS total_employees FROM employees WHERE status = 'active'")
            total_employees = cursor.fetchone().get("total_employees", 0)

            cursor.execute("SELECT COUNT(*) AS present_today FROM attendance WHERE date = %s AND status = 'present'", (today,))
            present_today = cursor.fetchone().get("present_today", 0)

            cursor.execute("SELECT COUNT(*) AS late_today FROM attendance WHERE date = %s AND status = 'late'", (today,))
            late_today = cursor.fetchone().get("late_today", 0)

            cursor.execute("SELECT COUNT(*) AS total_today FROM attendance WHERE date = %s", (today,))
            total_today = cursor.fetchone().get("total_today", 0)

            return DashboardSummary(
                total_employees=total_employees,
                present_today=present_today,
                late_today=late_today,
                total_today=total_today,
                date=today,
            )
        except Exception as exc:
            print(f"[AttendanceDAO] get_dashboard_summary: {exc}")
            return None
        finally:
            conn.close()

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
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT
                    a.id,
                    a.date AS attendance_date,
                    a.time_in,
                    a.time_out,
                    a.status,
                    e.employee_no,
                    e.first_name,
                    e.last_name,
                    d.name AS department_name
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE 1=1
            """
            params = []
            if start_date:
                query += " AND a.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND a.date <= %s"
                params.append(end_date)
            if department_id:
                query += " AND e.department_id = %s"
                params.append(department_id)
            if employee_id:
                query += " AND a.employee_id = %s"
                params.append(employee_id)
            if name_search:
                query += (
                    " AND (e.first_name LIKE %s OR e.last_name LIKE %s"
                    " OR CONCAT(e.first_name,' ',e.last_name) LIKE %s"
                    " OR e.employee_no LIKE %s)"
                )
                like = f"%{name_search}%"
                params.extend([like, like, like, like])
            if status:
                query += " AND a.status = %s"
                params.append(status)
            query += " ORDER BY a.date DESC, a.time_in DESC"
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            cursor.execute(query, params)
            return [AttendanceReportRow.from_dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"[AttendanceDAO] get_attendance_report: {exc}")
            return []
        finally:
            conn.close()
