import threading
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2

from Controller.enrollment_controller import EnrollmentController
from Controller.employee_controller import EmployeeController


class EnrollmentView(ctk.CTkFrame):
    CAPTURE_TARGET = 5
    PREVIEW_W, PREVIEW_H = 480, 360

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._cap = None
        self._running = False
        self._capture_thread = None
        self._render_job = None
        self._lock = threading.Lock()
        self._selected_emp = None
        self._captured_encodings = []
        self._face_detected = False
        self._current_frame = None
        self._build_ui()
        self._load_employees()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Select Employee", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 8)
        )

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ctk.CTkEntry(left, placeholder_text="Search employee...", textvariable=self._search_var).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 8)
        )

        self._scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 12))
        self._scroll.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Face Enrollment", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 8)
        )

        self._emp_label = ctk.CTkLabel(right, text="No employee selected", fg_color=("gray85", "gray25"), corner_radius=8, padx=12, pady=8)
        self._emp_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        cam_frame = ctk.CTkFrame(right, fg_color="black", corner_radius=10)
        cam_frame.grid(row=2, column=0, padx=20, pady=(0, 8))

        self._video_label = ctk.CTkLabel(cam_frame, text="Camera feed will appear here", text_color="gray", width=self.PREVIEW_W, height=self.PREVIEW_H)
        self._video_label.pack(padx=4, pady=4)

        self._detect_bar = ctk.CTkLabel(right, text="● No face detected", fg_color=("gray80", "gray30"), corner_radius=6, padx=10, pady=6, text_color="gray")
        self._detect_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))

        pf = ctk.CTkFrame(right, fg_color="transparent")
        pf.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 4))
        pf.grid_columnconfigure(0, weight=1)

        self._progress_label = ctk.CTkLabel(pf, text=f"Samples: 0 / {self.CAPTURE_TARGET}", text_color="gray")
        self._progress_label.grid(row=0, column=0, sticky="w")

        self._progress = ctk.CTkProgressBar(pf)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        bf = ctk.CTkFrame(right, fg_color="transparent")
        bf.grid(row=5, column=0, sticky="ew", padx=20, pady=(8, 4))
        bf.grid_columnconfigure((0, 1, 2), weight=1)

        self._start_btn = ctk.CTkButton(bf, text="Start Camera", fg_color="#1D9E75", hover_color="#0F6E56", command=self._start_camera, state="disabled")
        self._start_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._capture_btn = ctk.CTkButton(bf, text="Capture Face", fg_color="#378ADD", hover_color="#185FA5", command=self._capture, state="disabled")
        self._capture_btn.grid(row=0, column=1, padx=6, sticky="ew")

        self._delete_btn = ctk.CTkButton(bf, text="Remove Face", fg_color="#E24B4A", hover_color="#A32D2D", command=self._remove_face, state="disabled")
        self._delete_btn.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self._stop_btn = ctk.CTkButton(right, text="Stop Camera", fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=self._stop_camera, state="disabled")
        self._stop_btn.grid(row=6, column=0, padx=20, pady=(0, 4), sticky="ew")

        self._status_label = ctk.CTkLabel(right, text="", text_color="#1D9E75")
        self._status_label.grid(row=7, column=0, pady=(0, 12))

    def _load_employees(self):
        self._all_employees = EmployeeController.list_employees()
        self._render_list(self._all_employees)

    def _render_list(self, employees):
        for widget in self._scroll.winfo_children():
            widget.destroy()

        if not employees:
            ctk.CTkLabel(self._scroll, text="No employees found.", text_color="gray").grid(row=0, column=0, pady=20)
            return

        for emp in employees:
            badge_text = "Enrolled" if EmployeeController.employee_has_face_encoding(emp.id) else "Not enrolled"
            badge_color = "#1D9E75" if badge_text == "Enrolled" else "#888780"

            row = ctk.CTkFrame(self._scroll, corner_radius=8)
            row.grid(sticky="ew", pady=3)
            row.grid_columnconfigure(0, weight=1)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.grid(sticky="ew", padx=10, pady=8)
            inner.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(inner, text=emp.full_name, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(inner, text=emp.employee_no, text_color="gray", font=ctk.CTkFont(size=12), anchor="w").grid(row=1, column=0, sticky="w")
            ctk.CTkLabel(inner, text=badge_text, fg_color=badge_color, text_color="white", corner_radius=6, font=ctk.CTkFont(size=11), padx=6, pady=2).grid(row=0, column=1, rowspan=2, sticky="e")

            for widget in [row, inner] + list(inner.winfo_children()):
                widget.bind("<Button-1>", lambda e, emp=emp: self._select_employee(emp))

    def _filter_list(self):
        query = self._search_var.get().lower()
        filtered = [
            emp for emp in self._all_employees
            if query in emp.first_name.lower()
            or query in emp.last_name.lower()
            or query in emp.employee_no.lower()
        ]
        self._render_list(filtered)

    def _select_employee(self, emp):
        if self._running:
            self._stop_camera()

        self._selected_emp = emp
        self._emp_label.configure(text=f"{emp.full_name} ({emp.employee_no})")
        self._start_btn.configure(state="normal")
        self._delete_btn.configure(state="normal" if EmployeeController.employee_has_face_encoding(emp.id) else "disabled")
        self._reset_progress()
        self._set_status("")

    def _start_camera(self):
        if not self._selected_emp or self._running:
            return

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._set_status("Cannot open camera.", error=True)
            self._cap.release()
            self._cap = None
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._capture_btn.configure(state="normal")

        self._capture_thread = threading.Thread(target=self._read_frames, daemon=True)
        self._capture_thread.start()
        self._render_frame()

    def _read_frames(self):
        cap = self._cap
        detect_every = 3
        count = 0
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                count += 1
                if count % detect_every == 0:
                    rgb_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)[:, :, ::-1].copy()
                    classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    self._face_detected = len(classifier.detectMultiScale(rgb_small, scaleFactor=1.1, minNeighbors=5)) > 0
                with self._lock:
                    self._current_frame = frame.copy()
        finally:
            cap.release()
            with self._lock:
                self._current_frame = None

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

            if self._face_detected:
                self._detect_bar.configure(text="● Face detected — ready to capture", text_color="#1D9E75", fg_color=("#d4f5e9", "#0a3d2b"))
            else:
                self._detect_bar.configure(text="● No face detected — position yourself in frame", text_color="gray", fg_color=("gray80", "gray30"))

        self._render_job = self.after(30, self._render_frame)

    def _stop_camera(self):
        if not self._running and self._cap is None:
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")
            self._capture_btn.configure(state="disabled")
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
        self._capture_btn.configure(state="disabled")

    def _capture(self):
        if not self._running or not self._face_detected:
            self._set_status("No face detected.", error=True)
            return
        if len(self._captured_encodings) >= self.CAPTURE_TARGET:
            return

        with self._lock:
            frame = self._current_frame.copy() if self._current_frame is not None else None

        if frame is None:
            return

        encoding = EnrollmentController.extract_encoding(frame)
        if encoding is None:
            self._set_status("Could not encode face. Try again.", error=True)
            return

        self._captured_encodings.append(encoding)
        count = len(self._captured_encodings)
        self._progress.set(count / self.CAPTURE_TARGET)
        self._progress_label.configure(text=f"Samples: {count} / {self.CAPTURE_TARGET}", text_color="#1D9E75")
        self._set_status(f"Sample {count} captured.")
        if count >= self.CAPTURE_TARGET:
            self._save_enrollment()

    def _save_enrollment(self):
        if not self._selected_emp:
            return
        encoding = EnrollmentController.average_encodings(self._captured_encodings)
        if EnrollmentController.save_face_encoding(self._selected_emp.id, encoding):
            self._set_status(f"Face enrolled for {self._selected_emp.full_name}.")
            self._delete_btn.configure(state="normal")
            self._load_employees()
            self._stop_camera()
        else:
            self._set_status("Failed to save encoding.", error=True)
        self._reset_progress()

    def _remove_face(self):
        if not self._selected_emp:
            return
        if messagebox.askyesno("Remove Face", f"Remove face encoding for {self._selected_emp.full_name}?" ):
            if EnrollmentController.delete_face_encoding(self._selected_emp.id):
                self._set_status("Face encoding removed.")
                self._delete_btn.configure(state="disabled")
                self._load_employees()
            else:
                self._set_status("Failed to remove encoding.", error=True)

    def _reset_progress(self):
        self._captured_encodings.clear()
        self._progress.set(0)
        self._progress_label.configure(text=f"Samples: 0 / {self.CAPTURE_TARGET}", text_color="gray")

    def _set_status(self, message: str, error: bool = False):
        self._status_label.configure(text=message, text_color=("#E24B4A" if error else "#1D9E75"))

    def destroy(self):
        self._stop_camera()
        super().destroy()
