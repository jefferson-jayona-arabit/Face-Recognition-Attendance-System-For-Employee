import datetime as dt
import numpy as np
import face_recognition

from db.connection import get_connection
from services.enrollment_service import load_all_encodings


def get_known_faces():
    """Load known encodings and employee IDs from the database."""
    encodings, employee_ids = load_all_encodings()
    return encodings, employee_ids


def recognize_face_from_frame(frame, known_encodings=None, known_employee_ids=None, tolerance=0.55):
    """Return the best matching employee ID and confidence for a frame."""
    if frame is None:
        return None, None, None

    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    try:
        locations = face_recognition.face_locations(rgb, model="hog")
        if not locations:
            return None, None, None

        encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
        if not encodings:
            return None, None, None

        if known_encodings is None or known_employee_ids is None:
            known_encodings, known_employee_ids = get_known_faces()

        if not known_encodings:
            return None, None, None

        distances = face_recognition.face_distance(known_encodings, encodings[0])
        best_index = int(np.argmin(distances)) if len(distances) else None
        if best_index is None:
            return None, None, None

        is_match = bool(face_recognition.compare_faces(
            known_encodings,
            encodings[0],
            tolerance=tolerance
        )[best_index])

        if is_match:
            return known_employee_ids[best_index], float(distances[best_index]), locations[0]
        return None, float(distances[best_index]), locations[0]
    except Exception as exc:
        print(f"[recognition_service] recognize_face_from_frame error: {exc}")
        return None, None, None


def get_attendance_record(employee_id, attendance_date=None):
    """Fetch a single attendance row for a given employee and date."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        if attendance_date is None:
            attendance_date = dt.date.today().isoformat()
        cursor.execute(
            "SELECT id, employee_id, date, time_in, time_out, status FROM attendance WHERE employee_id = %s AND date = %s",
            (employee_id, attendance_date),
        )
        return cursor.fetchone()
    except Exception as exc:
        print(f"[recognition_service] get_attendance_record error: {exc}")
        return None
    finally:
        conn.close()


def record_attendance(employee_id, attendance_date=None, check_in_time=None, status=None):
    """Insert or update the attendance row for the current day."""
    conn = get_connection()
    if not conn:
        return False

    if attendance_date is None:
        attendance_date = dt.date.today().isoformat()
    if check_in_time is None:
        check_in_time = dt.datetime.now().strftime("%H:%M:%S")
    if status is None:
        try:
            parsed_time = dt.datetime.strptime(check_in_time, "%H:%M:%S").time()
            status = "late" if parsed_time > dt.time(9, 0) else "present"
        except ValueError:
            status = "present"

    try:
        existing = get_attendance_record(employee_id, attendance_date)
        if existing:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE attendance SET time_in = COALESCE(time_in, %s), status = %s WHERE id = %s",
                (check_in_time, status, existing["id"]),
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attendance (employee_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
                (employee_id, attendance_date, check_in_time, status),
            )
        conn.commit()
        return True
    except Exception as exc:
        print(f"[recognition_service] record_attendance error: {exc}")
        conn.rollback()
        return False
    finally:
        conn.close()
