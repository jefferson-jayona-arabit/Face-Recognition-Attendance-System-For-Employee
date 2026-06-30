from typing import List, Optional, Tuple
import numpy as np
import cv2
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
        """Recognise a single (first) face in the frame. Kept for backward compat."""
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

    @staticmethod
    def recognize_all_faces_from_frame(
        frame,
        known_encodings: List,
        known_employee_ids: List[int],
        tolerance: float = 0.55,
    ) -> List[Tuple[Optional[int], float, tuple]]:
        """
        Detect and recognise EVERY face visible in the frame.

        Returns a list of (employee_id | None, confidence, location) tuples —
        one entry per detected face.  employee_id is None when no known match
        meets the tolerance threshold.

        location format: (top, right, bottom, left)  — same as face_recognition.
        """
        if frame is None or not known_encodings:
            return []

        # Shrink frame for faster HOG detection, then scale locations back up
        scale   = 0.5
        small   = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb     = np.ascontiguousarray(small[:, :, ::-1])

        try:
            small_locs = face_recognition.face_locations(rgb, model="hog")
            if not small_locs:
                return []

            # Scale locations back to full-frame coordinates
            full_locs = [
                (int(t / scale), int(r / scale), int(b / scale), int(l / scale))
                for (t, r, b, l) in small_locs
            ]

            rgb_full  = np.ascontiguousarray(frame[:, :, ::-1])
            encodings = face_recognition.face_encodings(rgb_full, known_face_locations=full_locs)

            results = []
            for enc, loc in zip(encodings, full_locs):
                distances  = face_recognition.face_distance(known_encodings, enc)
                best_idx   = int(np.argmin(distances))
                matches    = face_recognition.compare_faces(known_encodings, enc, tolerance=tolerance)
                if matches[best_idx]:
                    results.append((known_employee_ids[best_idx], float(distances[best_idx]), loc))
                else:
                    results.append((None, float(distances[best_idx]), loc))

            return results

        except Exception as exc:
            print(f"[FaceController] recognize_all_faces_from_frame: {exc}")
            return []
