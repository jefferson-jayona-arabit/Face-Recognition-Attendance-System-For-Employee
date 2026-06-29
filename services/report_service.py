import csv
import datetime as dt

from db.connection import get_connection


def get_attendance_report(start_date=None, end_date=None, department_id=None, employee_id=None):
    """Return attendance rows joined with employee and department details."""
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

        query += " ORDER BY a.date DESC, a.time_in DESC"
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as exc:
        print(f"[report_service] get_attendance_report error: {exc}")
        return []
    finally:
        conn.close()


def get_recent_attendance(limit=10):
    """Fetch the most recent attendance entries."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.id, a.date AS attendance_date, a.time_in, a.time_out, a.status,
                   e.employee_no, e.first_name, e.last_name
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            ORDER BY a.date DESC, a.time_in DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Exception as exc:
        print(f"[report_service] get_recent_attendance error: {exc}")
        return []
    finally:
        conn.close()


def get_dashboard_summary():
    """Return summary stats for the dashboard."""
    conn = get_connection()
    if not conn:
        return {}
    today = dt.date.today().isoformat()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total_employees FROM employees WHERE status = 'active'")
        total_employees = cursor.fetchone()["total_employees"]

        cursor.execute("SELECT COUNT(*) AS present_today FROM attendance WHERE date = %s AND status = 'present'", (today,))
        present_today = cursor.fetchone()["present_today"]

        cursor.execute("SELECT COUNT(*) AS late_today FROM attendance WHERE date = %s AND status = 'late'", (today,))
        late_today = cursor.fetchone()["late_today"]

        cursor.execute("SELECT COUNT(*) AS total_today FROM attendance WHERE date = %s", (today,))
        total_today = cursor.fetchone()["total_today"]

        return {
            "total_employees": total_employees,
            "present_today": present_today,
            "late_today": late_today,
            "total_today": total_today,
            "date": today,
        }
    except Exception as exc:
        print(f"[report_service] get_dashboard_summary error: {exc}")
        return {}
    finally:
        conn.close()


def export_report_to_csv(rows, file_path):
    """Export report rows to a CSV file."""
    try:
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "attendance_date",
                "employee_no",
                "first_name",
                "last_name",
                "department_name",
                "time_in",
                "time_out",
                "status",
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return True
    except Exception as exc:
        print(f"[report_service] export_report_to_csv error: {exc}")
        return False
