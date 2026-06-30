from typing import List, Optional
import pickle

from db.connection import get_connection


class FaceEncodingDAO:
    @staticmethod
    def save_face_encoding(employee_id: int, encoding) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_encodings WHERE employee_id = %s", (employee_id,))
            encoding_blob = pickle.dumps(encoding)
            cursor.execute(
                "INSERT INTO face_encodings (employee_id, encoding) VALUES (%s, %s)",
                (employee_id, encoding_blob),
            )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[FaceEncodingDAO] save_face_encoding: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def load_all_encodings() -> tuple[List, List[int]]:
        conn = get_connection()
        if not conn:
            return [], []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT employee_id, encoding FROM face_encodings")
            encodings = []
            employee_ids = []
            for employee_id, blob in cursor.fetchall():
                encodings.append(pickle.loads(blob))
                employee_ids.append(employee_id)
            return encodings, employee_ids
        except Exception as exc:
            print(f"[FaceEncodingDAO] load_all_encodings: {exc}")
            return [], []
        finally:
            conn.close()

    @staticmethod
    def delete_face_encoding(employee_id: int) -> bool:
        conn = get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_encodings WHERE employee_id = %s", (employee_id,))
            conn.commit()
            return True
        except Exception as exc:
            print(f"[FaceEncodingDAO] delete_face_encoding: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()
