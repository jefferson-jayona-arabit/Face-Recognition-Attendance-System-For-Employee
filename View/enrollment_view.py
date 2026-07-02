import threading
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2

from Controller.enrollment_controller import EnrollmentController
from Controller.employee_controller import EmployeeController
from events import AppEvents

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
BLUE       = "#4F8EF7"
BLUE_DARK  = "#2F6FD8"
RED_SOFT   = "#E24B4A"
RED_DARK   = "#A32D2D"
AMBER      = "#F5A623"
BG_CARD    = ("gray92", "#1E2130")
BG_ROW_ALT = ("gray88", "#252839")
FG_MUTED   = ("gray45", "gray65")


class EnrollmentView(ctk.CTkFrame):
    CAPTURE_TARGET = 5
    PREVIEW_W, PREVIEW_H = 500, 375

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._cap               = None
        self._running           = False
        self._capture_thread    = None
        self._render_job        = None
        self._lock              = threading.Lock()
        self._selected_emp      = None
        self._captured_encodings = []
        self._face_detected     = False
        self._current_frame     = None
        self._build_ui()
        self.after(100, self._load_employees)
        AppEvents.on("employee_changed", self._load_employees)

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── Left: employee list ──────────────────────────────────────────────
        left = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            left, text="Employees",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ctk.CTkEntry(
            left, placeholder_text="🔍  Search employee…",
            textvariable=self._search_var,
            height=36, corner_radius=8,
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 8))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._emp_count_label = ctk.CTkLabel(
            left, text="",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._emp_count_label.grid(row=3, column=0, pady=(0, 10))

        # ── Right: enrollment panel ──────────────────────────────────────────
        right = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        # Section title
        ctk.CTkLabel(
            right, text="Face Enrollment",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        # Selected employee badge
        self._emp_label = ctk.CTkLabel(
            right, text="No employee selected",
            fg_color=("gray85", "#252839"),
            corner_radius=10, padx=14, pady=10,
            font=ctk.CTkFont(size=13),
        )
        self._emp_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Camera container
        cam_wrap = ctk.CTkFrame(right, fg_color=("gray20", "#0d0f18"), corner_radius=12)
        cam_wrap.grid(row=2, column=0, padx=16, pady=(0, 8))

        self._video_label = ctk.CTkLabel(
            cam_wrap,
            text="Camera feed will appear here",
            text_color=FG_MUTED,
            font=ctk.CTkFont(size=13),
            width=self.PREVIEW_W, height=self.PREVIEW_H,
        )
        self._video_label.pack(padx=4, pady=4)

        # Face detection indicator
        self._detect_bar = ctk.CTkLabel(
            right, text="● No face detected",
            fg_color=("gray85", "#252839"),
            corner_radius=8, padx=12, pady=8,
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._detect_bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Progress section
        prog_frame = ctk.CTkFrame(right, fg_color="transparent")
        prog_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 6))
        prog_frame.grid_columnconfigure(0, weight=1)

        pf_header = ctk.CTkFrame(prog_frame, fg_color="transparent")
        pf_header.grid(row=0, column=0, sticky="ew")
        pf_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            pf_header, text="Capture Progress",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._progress_label = ctk.CTkLabel(
            pf_header, text=f"0 / {self.CAPTURE_TARGET}",
            font=ctk.CTkFont(size=12),
            text_color=FG_MUTED,
        )
        self._progress_label.grid(row=0, column=1, sticky="e")

        self._progress = ctk.CTkProgressBar(prog_frame, height=10, corner_radius=5)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Step dots
        self._dots_frame = ctk.CTkFrame(prog_frame, fg_color="transparent")
        self._dots_frame.grid(row=2, column=0, pady=(6, 0))
        self._dots = []
        for i in range(self.CAPTURE_TARGET):
            dot = ctk.CTkLabel(
                self._dots_frame, text="○",
                font=ctk.CTkFont(size=18),
                text_color=("gray70", "gray50"),
            )
            dot.grid(row=0, column=i, padx=6)
            self._dots.append(dot)

        # Action buttons
        bf = ctk.CTkFrame(right, fg_color="transparent")
        bf.grid(row=5, column=0, sticky="ew", padx=16, pady=(12, 4))
        bf.grid_columnconfigure((0, 1, 2), weight=1)

        self._start_btn = ctk.CTkButton(
            bf, text="▶  Start",
            fg_color=GREEN, hover_color=GREEN_DARK,
            height=40, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._start_camera, state="disabled",
        )
        self._start_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self._capture_btn = ctk.CTkButton(
            bf, text="📸  Capture",
            fg_color=BLUE, hover_color=BLUE_DARK,
            height=40, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._capture, state="disabled",
        )
        self._capture_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self._delete_btn = ctk.CTkButton(
            bf, text="🗑  Remove",
            fg_color=RED_SOFT, hover_color=RED_DARK,
            height=40, corner_radius=8,
            command=self._remove_face, state="disabled",
        )
        self._delete_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        self._stop_btn = ctk.CTkButton(
            right, text="⏹  Stop Camera",
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            height=36, corner_radius=8,
            command=self._stop_camera, state="disabled",
        )
        self._stop_btn.grid(row=6, column=0, padx=16, pady=(4, 6), sticky="ew")

        self._status_label = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont(size=12),
            text_color=GREEN,
        )
        self._status_label.grid(row=7, column=0, pady=(0, 14))

    # ── Data ─────────────────────────────────────────────────────────────────
    def _load_employees(self):
        """Fetch employee data in a background thread, render on main thread."""
        self._emp_count_label.configure(text="Loading…")
        threading.Thread(target=self._fetch_employees, daemon=True).start()

    def _fetch_employees(self):
        """Runs on background thread — fetches all data, then schedules render."""
        employees = EmployeeController.list_employees()
        # Pre-fetch face encoding status for all employees in bulk
        enrollment_status = {
            emp.id: EmployeeController.employee_has_face_encoding(emp.id)
            for emp in employees
        }
        # Schedule UI update on main thread
        self.after(0, lambda: self._render_list(employees, enrollment_status))

    def _render_list(self, employees, enrollment_status: dict = None):
        if enrollment_status is None:
            enrollment_status = {}

        for w in self._scroll.winfo_children():
            w.destroy()

        self._all_employees = employees
        self._emp_count_label.configure(text=f"{len(employees)} employee(s)")

        if not employees:
            ctk.CTkLabel(
                self._scroll, text="No employees found.",
                text_color=FG_MUTED,
            ).grid(row=0, column=0, pady=20)
            return

        for emp in employees:
            enrolled   = enrollment_status.get(emp.id, False)
            badge_text = "Enrolled" if enrolled else "Not enrolled"
            badge_fg   = GREEN if enrolled else ("gray55", "gray55")
            badge_bg   = ("#d4f5e9", "#0a3d2b") if enrolled else ("gray80", "gray35")

            is_selected = self._selected_emp and self._selected_emp.id == emp.id
            row_bg = (BLUE + "22", "#1a2a4a") if is_selected else "transparent"

            row = ctk.CTkFrame(
                self._scroll, corner_radius=10,
                fg_color=row_bg,
                border_width=2 if is_selected else 0,
                border_color=(BLUE, BLUE),
            )
            row.grid(sticky="ew", pady=3)
            row.grid_columnconfigure(0, weight=1)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.grid(sticky="ew", padx=10, pady=9)
            inner.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                inner, text=emp.full_name,
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                inner, text=f"{emp.employee_no}  ·  {emp.department or '—'}",
                text_color=FG_MUTED,
                font=ctk.CTkFont(size=11), anchor="w",
            ).grid(row=1, column=0, sticky="w")

            badge_frame = ctk.CTkFrame(inner, fg_color=badge_bg, corner_radius=6)
            badge_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=(6, 0))
            ctk.CTkLabel(
                badge_frame, text=badge_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=badge_fg,
            ).grid(padx=7, pady=3)

            for w in [row, inner] + list(inner.winfo_children()) + [badge_frame] + list(badge_frame.winfo_children()):
                w.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))

    def _filter_list(self):
        q = self._search_var.get().lower()
        filtered = [
            e for e in self._all_employees
            if q in e.first_name.lower() or q in e.last_name.lower() or q in e.employee_no.lower()
        ]
        # Re-fetch enrollment status only for filtered subset (fast — already cached by DB)
        enrollment_status = {
            emp.id: EmployeeController.employee_has_face_encoding(emp.id)
            for emp in filtered
        }
        self._render_list(filtered, enrollment_status)

    def _select_employee(self, emp):
        if self._running:
            self._stop_camera()

        self._selected_emp = emp
        self._emp_label.configure(
            text=f"👤  {emp.full_name}  ({emp.employee_no})",
            text_color=("gray10", "gray90"),
        )
        self._start_btn.configure(state="normal")
        enrolled = EmployeeController.employee_has_face_encoding(emp.id)
        self._delete_btn.configure(state="normal" if enrolled else "disabled")
        self._reset_progress()
        self._set_status("")
        # Refresh list to show selection highlight (use cached enrollment status)
        self._load_employees()

    # ── Camera ───────────────────────────────────────────────────────────────
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
                    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)[:, :, ::-1].copy()
                    clf = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                    self._face_detected = len(clf.detectMultiScale(small, scaleFactor=1.1, minNeighbors=5)) > 0
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
            img     = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self.PREVIEW_W, self.PREVIEW_H))
            self._video_label.configure(image=ctk_img, text="")
            self._video_label._ctk_image = ctk_img

            if self._face_detected:
                self._detect_bar.configure(
                    text="✅  Face detected — ready to capture",
                    text_color=GREEN,
                    fg_color=("#d4f5e9", "#0a3d2b"),
                )
                self._capture_btn.configure(state="normal")
            else:
                self._detect_bar.configure(
                    text="● No face detected — position yourself in frame",
                    text_color=FG_MUTED,
                    fg_color=("gray85", "#252839"),
                )

        self._render_job = self.after(30, self._render_frame)

    def _stop_camera(self):
        self._running = False
        if self._render_job:
            self.after_cancel(self._render_job)
            self._render_job = None
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        self._capture_thread = None
        self._cap = None

        try:
            self._video_label.configure(image=None, text="Camera stopped.")
            self._start_btn.configure(state="normal" if self._selected_emp else "disabled")
            self._stop_btn.configure(state="disabled")
            self._capture_btn.configure(state="disabled")
            self._detect_bar.configure(
                text="● No face detected",
                text_color=FG_MUTED,
                fg_color=("gray85", "#252839"),
            )
        except Exception:
            pass

    # ── Capture / Enrollment ─────────────────────────────────────────────────
    def _capture(self):
        if not self._running or not self._face_detected:
            self._set_status("No face detected. Position yourself in frame.", error=True)
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
        self._progress_label.configure(
            text=f"{count} / {self.CAPTURE_TARGET}",
            text_color=GREEN,
        )
        # Update step dots
        for i, dot in enumerate(self._dots):
            dot.configure(
                text="●" if i < count else "○",
                text_color=GREEN if i < count else ("gray70", "gray50"),
            )
        self._set_status(f"Sample {count} of {self.CAPTURE_TARGET} captured.")
        if count >= self.CAPTURE_TARGET:
            self._save_enrollment()

    def _save_enrollment(self):
        if not self._selected_emp:
            return
        encoding = EnrollmentController.average_encodings(self._captured_encodings)
        if EnrollmentController.save_face_encoding(self._selected_emp.id, encoding):
            self._set_status(f"✅  Face enrolled for {self._selected_emp.full_name}.")
            self._delete_btn.configure(state="normal")
            self._load_employees()
            self._stop_camera()
        else:
            self._set_status("Failed to save encoding.", error=True)
        self._reset_progress()

    def _remove_face(self):
        if not self._selected_emp:
            return
        if messagebox.askyesno(
            "Remove Face Encoding",
            f"Remove face encoding for {self._selected_emp.full_name}?\nThey will need to be re-enrolled.",
        ):
            if EnrollmentController.delete_face_encoding(self._selected_emp.id):
                self._set_status("Face encoding removed.")
                self._delete_btn.configure(state="disabled")
                self._load_employees()
            else:
                self._set_status("Failed to remove encoding.", error=True)

    def _reset_progress(self):
        self._captured_encodings.clear()
        self._progress.set(0)
        self._progress_label.configure(text=f"0 / {self.CAPTURE_TARGET}", text_color=FG_MUTED)
        for dot in self._dots:
            dot.configure(text="○", text_color=("gray70", "gray50"))

    def _set_status(self, message: str, error: bool = False):
        self._status_label.configure(
            text=message,
            text_color=RED_SOFT if error else GREEN,
        )

    def destroy(self):
        self._stop_camera()
        super().destroy()
