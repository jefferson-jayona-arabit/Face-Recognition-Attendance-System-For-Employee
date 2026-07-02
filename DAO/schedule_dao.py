from typing import Optional
from db.connection import get_connection
from Model.entities import WorkSchedule
from events import AppEvents


class ScheduleDAO:

    @staticmethod
    def get_active_schedule() -> Optional[WorkSchedule]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM work_schedule WHERE is_active = 1 ORDER BY id LIMIT 1"
            )
            row = cursor.fetchone()
            return WorkSchedule.from_dict(row) if row else None
        except Exception as exc:
            print(f"[ScheduleDAO] get_active_schedule: {exc}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_all_schedules():
        conn = get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM work_schedule ORDER BY id")
            return [WorkSchedule.from_dict(r) for r in cursor.fetchall()]
        except Exception as exc:
            print(f"[ScheduleDAO] get_all_schedules: {exc}")
            return []
        finally:
            conn.close()

    @staticmethod
    def save_schedule(label: str,
                      time_in_start: str,
                      time_in_end: str,
                      late_cutoff: str,
                      time_out_start: str,
                      time_out_end: str,
                      schedule_id: Optional[int] = None) -> Optional[int]:
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            if schedule_id:
                cursor.execute(
                    """UPDATE work_schedule
                       SET label=%s, time_in_start=%s, time_in_end=%s,
                           late_cutoff=%s, time_out_start=%s, time_out_end=%s
                       WHERE id=%s""",
                    (label, time_in_start, time_in_end,
                     late_cutoff, time_out_start, time_out_end, schedule_id),
                )
                conn.commit()
                return schedule_id
            else:
                cursor.execute(
                    """INSERT INTO work_schedule
                       (label, time_in_start, time_in_end, late_cutoff,
                        time_out_start, time_out_end)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (label, time_in_start, time_in_end,
                     late_cutoff, time_out_start, time_out_end),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as exc:
            print(f"[ScheduleDAO] save_schedule: {exc}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def set_active(schedule_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE work_schedule SET is_active = 0")
            cursor.execute(
                "UPDATE work_schedule SET is_active = 1 WHERE id = %s",
                (schedule_id,),
            )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[ScheduleDAO] set_active: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_schedule(schedule_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_schedule WHERE id = %s", (schedule_id,))
            conn.commit()
            return True
        except Exception as exc:
            print(f"[ScheduleDAO] delete_schedule: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()
