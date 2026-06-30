from typing import List, Optional
import numpy as np
import face_recognition

from DAO.face_encoding_dao import FaceEncodingDAO


class FaceController:
    @staticmethod
    def save_encoding(employee_id: int, encoding) -> bool:
        return FaceEncodingDAO.save_face_encoding(employee_id, encoding)

    @staticmethod
    def delete_encoding(employee_id: int) -> bool:
        return FaceEncodingDAO.delete_face_encoding(employee_id)

    @staticmethod
    def load_known_faces() -> tuple[List, List[int]]:
        return FaceEncodingDAO.load_all_encodings()

    @staticmethod
    def extract_encoding_from_frame(frame):
        if frame is None:
            return None
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        try:
            locations = face_recognition.face_locations(rgb, model="hog")
            if not locations:
                return None
            encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
            return encodings[0] if encodings else None
        except Exception as exc:
            print(f"[FaceController] extract_encoding_from_frame: {exc}")
            return None

    @staticmethod
    def recognize_face_from_frame(frame, known_encodings=None, known_employee_ids=None, tolerance=0.55):
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
                known_encodings, known_employee_ids = FaceEncodingDAO.load_all_encodings()
            if not known_encodings:
                return None, None, None
            distances = face_recognition.face_distance(known_encodings, encodings[0])
            best_index = int(np.argmin(distances)) if len(distances) else None
            if best_index is None:
                return None, None, None
            is_match = bool(face_recognition.compare_faces(known_encodings, encodings[0], tolerance=tolerance)[best_index])
            if is_match:
                return known_employee_ids[best_index], float(distances[best_index]), locations[0]
            return None, float(distances[best_index]), locations[0]
        except Exception as exc:
            print(f"[FaceController] recognize_face_from_frame: {exc}")
            return None, None, None
