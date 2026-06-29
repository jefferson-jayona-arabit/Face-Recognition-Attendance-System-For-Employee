import pickle
import numpy as np
import face_recognition
from db.connection import get_connection


def save_face_encoding(employee_id, encoding):
    """Serialize and save a face encoding to the database."""
    conn = get_connection()
    if not conn:
        return False
    try:
        encoding_blob = pickle.dumps(encoding)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM face_encodings WHERE employee_id = %s", (employee_id,))
        cursor.execute(
            "INSERT INTO face_encodings (employee_id, encoding) VALUES (%s, %s)",
            (employee_id, encoding_blob)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[enrollment_service] save_face_encoding error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def load_all_encodings():
    """
    Load all face encodings from DB.
    Returns (list_of_encodings, list_of_employee_ids).
    """
    conn = get_connection()
    if not conn:
        return [], []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id, encoding FROM face_encodings")
        rows = cursor.fetchall()
        encodings, ids = [], []
        for emp_id, blob in rows:
            enc = pickle.loads(blob)
            encodings.append(enc)
            ids.append(emp_id)
        return encodings, ids
    except Exception as e:
        print(f"[enrollment_service] load_all_encodings error: {e}")
        return [], []
    finally:
        conn.close()


def delete_face_encoding(employee_id):
    """Remove a face encoding for a given employee."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM face_encodings WHERE employee_id = %s", (employee_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[enrollment_service] delete_face_encoding error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def encode_face_from_frame(frame):
    """
    Given an OpenCV BGR frame, detect and return the first face encoding.
    Always runs detection and encoding on the SAME full-resolution RGB frame.
    Returns the encoding (numpy array) or None if no face detected.
    """
    # Convert BGR -> RGB (face_recognition expects RGB) and force contiguous memory.
    rgb = np.ascontiguousarray(frame[:, :, ::-1])

    try:
        locations = face_recognition.face_locations(rgb, model="hog")
        if not locations:
            return None
        encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
        return encodings[0] if encodings else None
    except Exception as e:
        print(f"[enrollment_service] encode_face_from_frame error: {e}")
        return None


def average_encodings(encoding_list):
    """Average a list of encodings into one for better accuracy."""
    return np.mean(encoding_list, axis=0)