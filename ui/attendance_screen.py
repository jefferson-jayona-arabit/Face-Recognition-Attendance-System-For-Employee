import threading
import customtkinter as ctk
from PIL import Image
import cv2

from services.employee_service import get_all_employees
from services.recognition_service import recognize_face_from_frame, record_attendance
from services.report_service import get_recent_attendance


class AttendanceScreen(ctk.CTkFrame):
    PREVIEW_W, PREVIEW_H = 480, 360

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._cap = None
        self._running = False
        self._capture_thread = None
        self._render_job = None
        self._lock = threading.Lock()
        self._known_encodings = []
        self._known_employee_ids = []
        self._marked_today = set()
        self._current_name = ""
        self._current_frame = None
        self._build_ui()
        self._load_known_faces()
        self._refresh_attendance_list()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Face Attendance", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 10)
        )

        self._status_label = ctk.CTkLabel(
            left,
            text="Start the camera to begin recognition.",
            fg_color=("gray85", "gray25"),
            corner_radius=8,
            padx=10,
            pady=8,
        )
        self._status_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))

        self._video_label = ctk.CTkLabel(left, text="Camera preview", width=self.PREVIEW_W, height=self.PREVIEW_H)
        self._video_label.grid(row=2, column=0, padx=18, pady=(0, 10))

        button_row = ctk.CTkFrame(left, fg_color="transparent")
        button_row.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 10))
        button_row.grid_columnconfigure((0, 1), weight=1)

        self._start_btn = ctk.CTkButton(button_row, text="Start Camera", command=self._start_camera)
        self._start_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._stop_btn = ctk.CTkButton(button_row, text="Stop Camera", command=self._stop_camera, state="disabled")
        self._stop_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Today’s Attendance", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 10)
        )

        self._recognition_label = ctk.CTkLabel(
            right,
            text="Waiting for a match...",
            fg_color=("gray85", "gray25"),
            corner_radius=8,
            padx=10,
            pady=8,
        )
        self._recognition_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))

        self._attendance_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._attendance_scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._attendance_scroll.grid_columnconfigure(0, weight=1)

    def _load_known_faces(self):
        from services.recognition_service import get_known_faces

        encodings, employee_ids = get_known_faces()
        self._known_encodings = encodings
        self._known_employee_ids = employee_ids

    def _refresh_attendance_list(self):
        for widget in self._attendance_scroll.winfo_children():
            widget.destroy()

        rows = get_recent_attendance(limit=8)
        if not rows:
            ctk.CTkLabel(self._attendance_scroll, text="No attendance records yet.", text_color="gray").grid(pady=10)
            return

        for row in rows:
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            line = f"{name} • {row.get('attendance_date')} • {row.get('status', 'present')}"
            ctk.CTkLabel(self._attendance_scroll, text=line, anchor="w").grid(sticky="ew", pady=3)

    def _set_status(self, message, error=False):
        color = "#E24B4A" if error else "#1D9E75"
        self._status_label.configure(text=message, text_color=color)

    def _start_camera(self):
        if self._running:
            return

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._set_status("Could not access the camera.", error=True)
            self._cap.release()
            self._cap = None
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._capture_thread = threading.Thread(target=self._read_frames, daemon=True)
        self._capture_thread.start()
        self._render_frame()

    def _read_frames(self):
        cap = self._cap
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                with self._lock:
                    self._current_frame = frame.copy()

                if len(self._known_encodings) and len(self._known_employee_ids):
                    employee_id, confidence, _ = recognize_face_from_frame(frame, self._known_encodings, self._known_employee_ids)
                    if employee_id is not None and employee_id not in self._marked_today:
                        emp = self._lookup_employee(employee_id)
                        if emp:
                            name = f"{emp['first_name']} {emp['last_name']}"
                            self._current_name = name
                            self._recognition_label.configure(text=f"Recognized: {name}")
                            record_attendance(employee_id)
                            self._marked_today.add(employee_id)
                            self._refresh_attendance_list()
                            self._set_status(f"Attendance recorded for {name}.")
        finally:
            cap.release()
            with self._lock:
                self._current_frame = None

    def _lookup_employee(self, employee_id):
        employees = get_all_employees()
        for employee in employees:
            if employee["id"] == employee_id:
                return employee
        return None

    def _render_frame(self):
        if not self._running:
            self._render_job = None
            return

        with self._lock:
            frame = self._current_frame.copy() if self._current_frame is not None else None

        if frame is not None:
            preview = cv2.resize(frame, (self.PREVIEW_W, self.PREVIEW_H))
            img = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self.PREVIEW_W, self.PREVIEW_H))
            self._video_label.configure(image=ctk_img, text="")
            self._video_label._ctk_image = ctk_img

        self._render_job = self.after(30, self._render_frame)

    def _stop_camera(self):
        if not self._running and self._cap is None:
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")
            self._video_label.configure(image=None, text="Camera stopped.")
            return

        self._running = False
        if self._render_job is not None:
            self.after_cancel(self._render_job)
            self._render_job = None

        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
        self._capture_thread = None
        self._cap = None

        self._video_label.configure(image=None, text="Camera stopped.")
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def destroy(self):
        self._stop_camera()
        super().destroy()
