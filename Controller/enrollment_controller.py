from typing import List, Optional

import numpy as np

from Controller.face_controller import FaceController


class EnrollmentController:
    @staticmethod
    def extract_encoding(frame):
        return FaceController.extract_encoding_from_frame(frame)

    @staticmethod
    def average_encodings(encodings: List) -> Optional:
        if not encodings:
            return None
        try:
            return np.mean(encodings, axis=0)
        except Exception as exc:
            print(f"[EnrollmentController] average_encodings: {exc}")
            return None

    @staticmethod
    def save_face_encoding(employee_id: int, encoding) -> bool:
        return FaceController.save_encoding(employee_id, encoding)

    @staticmethod
    def delete_face_encoding(employee_id: int) -> bool:
        return FaceController.delete_encoding(employee_id)
