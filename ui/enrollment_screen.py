import threading
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2
import face_recognition

from services.employee_service import get_all_employees, has_face_encoding
from services.enrollment_service import (
    encode_face_from_frame,
    average_encodings,
    save_face_encoding,
    delete_face_encoding,
)


class EnrollmentScreen(ctk.CTkFrame):
    CAPTURE_TARGET = 5
    PREVIEW_W, PREVIEW_H = 480, 360

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._cap = None
        self._running = False
        self._capture_thread = None      # NEW: keep a handle so we can join it
        self._selected_emp = None
        self._captured_encodings = []
        self._face_detected = False
        self._current_frame = None
        self._lock = threading.Lock()
        self._recog_lock = threading.Lock()  # serialize face_recognition calls
        self._render_job = None          # NEW: handle for the .after() loop
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

        ctk.CTkLabel(left, text="Select Employee",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ctk.CTkEntry(left, placeholder_text="Search employee...",
                     textvariable=self._search_var).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 12))
        self._scroll.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Face Enrollment",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self._emp_label = ctk.CTkLabel(
            right, text="No employee selected",
            fg_color=("gray85", "gray25"), corner_radius=8,
            padx=12, pady=8)
        self._emp_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        cam_frame = ctk.CTkFrame(right, fg_color="black", corner_radius=10)
        cam_frame.grid(row=2, column=0, padx=20, pady=(0, 8))

        self._video_label = ctk.CTkLabel(
            cam_frame, text="Camera feed will appear here",
            text_color="gray", width=self.PREVIEW_W, height=self.PREVIEW_H)
        self._video_label.pack(padx=4, pady=4)

        self._detect_bar = ctk.CTkLabel(
            right, text="● No face detected",
            fg_color=("gray80", "gray30"), corner_radius=6,
            padx=10, pady=6, text_color="gray")
        self._detect_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))

        pf = ctk.CTkFrame(right, fg_color="transparent")
        pf.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 4))
        pf.grid_columnconfigure(0, weight=1)

        self._progress_label = ctk.CTkLabel(pf, text="Samples: 0 / 5", text_color="gray")
        self._progress_label.grid(row=0, column=0, sticky="w")

        self._progress = ctk.CTkProgressBar(pf)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        bf = ctk.CTkFrame(right, fg_color="transparent")
        bf.grid(row=5, column=0, sticky="ew", padx=20, pady=(8, 4))
        bf.grid_columnconfigure((0, 1, 2), weight=1)

        self._start_btn = ctk.CTkButton(
            bf, text="Start Camera",
            fg_color="#1D9E75", hover_color="#0F6E56",
            command=self._start_camera, state="disabled")
        self._start_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._capture_btn = ctk.CTkButton(
            bf, text="Capture Face",
            fg_color="#378ADD", hover_color="#185FA5",
            command=self._capture, state="disabled")
        self._capture_btn.grid(row=0, column=1, padx=6, sticky="ew")

        self._delete_btn = ctk.CTkButton(
            bf, text="Remove Face",
            fg_color="#E24B4A", hover_color="#A32D2D",
            command=self._remove_face, state="disabled")
        self._delete_btn.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self._stop_btn = ctk.CTkButton(
            right, text="Stop Camera",
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._stop_camera, state="disabled")
        self._stop_btn.grid(row=6, column=0, padx=20, pady=(0, 4), sticky="ew")

        self._status_label = ctk.CTkLabel(right, text="", text_color="#1D9E75")
        self._status_label.grid(row=7, column=0, pady=(0, 12))

    def _load_employees(self):
        self._all_employees = get_all_employees()
        self._render_list(self._all_employees)

    def _render_list(self, employees):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not employees:
            ctk.CTkLabel(self._scroll, text="No employees found.",
                         text_color="gray").grid(row=0, column=0, pady=20)
            return

        for emp in employees:
            full_name = f"{emp['first_name']} {emp['last_name']}"
            has_face  = has_face_encoding(emp["id"])

            row = ctk.CTkFrame(self._scroll, corner_radius=8)
            row.grid(sticky="ew", pady=3)
            row.grid_columnconfigure(0, weight=1)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.grid(sticky="ew", padx=10, pady=8)
            inner.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(inner, text=full_name,
                         font=ctk.CTkFont(weight="bold"), anchor="w").grid(
                row=0, column=0, sticky="w")
            ctk.CTkLabel(inner, text=emp["employee_no"],
                         text_color="gray", font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=1, column=0, sticky="w")

            badge_color = "#1D9E75" if has_face else "#888780"
            badge_text  = "Enrolled" if has_face else "Not enrolled"
            ctk.CTkLabel(inner, text=badge_text,
                         fg_color=badge_color, text_color="white",
                         corner_radius=6, font=ctk.CTkFont(size=11),
                         padx=6, pady=2).grid(row=0, column=1, rowspan=2, sticky="e")

            for widget in [row, inner] + list(inner.winfo_children()):
                widget.bind("<Button-1>",
                            lambda e, emp=emp: self._select_employee(emp))

    def _filter_list(self):
        q = self._search_var.get().lower()
        filtered = [
            e for e in self._all_employees
            if q in e["first_name"].lower()
            or q in e["last_name"].lower()
            or q in e["employee_no"].lower()
        ]
        self._render_list(filtered)

    def _select_employee(self, emp):
        # NEW: switching employees while the camera is live used to leave
        # the old thread/cap running underneath the new selection. Force a
        # clean stop first so there's only ever one camera session at a time.
        if self._running:
            self._stop_camera()

        self._selected_emp = emp
        full_name = f"{emp['first_name']} {emp['last_name']}"
        has_face  = has_face_encoding(emp["id"])
        status    = "✅ Face enrolled" if has_face else "⚠ No face enrolled"
        self._emp_label.configure(
            text=f"{full_name}  ({emp['employee_no']})   {status}")
        self._start_btn.configure(state="normal")
        self._delete_btn.configure(state="normal" if has_face else "disabled")
        self._set_status("")
        self._reset_progress()

    def _start_camera(self):
        if not self._selected_emp:
            return
        if self._running:          # NEW: guard against double-start
            return

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._set_status("Cannot open camera.", error=True)
            self._cap.release()
            self._cap = None
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        self._running = True
        self._reset_progress()
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._capture_btn.configure(state="normal")

        # NEW: keep the thread handle so _stop_camera/destroy can join it
        # before the capture object is released.
        self._capture_thread = threading.Thread(target=self._read_frames, daemon=True)
        self._capture_thread.start()
        self._render_frame()

    def _read_frames(self):
        """
        Runs on a background thread. Owns self._cap exclusively while
        self._running is True: it is the ONLY thread that reads from it,
        and it is the thread that releases it, right after exiting its
        own loop. This avoids the main thread calling cap.release() while
        cap.read() is still in-flight on another thread, which is what was
        crashing the process at the native (OpenCV/dlib) level.
        """
        detect_every = 3
        count = 0
        cap = self._cap  # local reference; never reassigned by anyone else
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                count += 1

                if count % detect_every == 0:
                    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small = small[:, :, ::-1].copy()
                    with self._recog_lock:
                        locations = face_recognition.face_locations(rgb_small, model="hog")
                    self._face_detected = len(locations) > 0

                    for (top, right, bottom, left) in locations:
                        top *= 4; right *= 4; bottom *= 4; left *= 4
                        color = (29, 158, 117)
                        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                        cv2.rectangle(frame, (left, top - 28), (right, top), color, -1)
                        cv2.putText(frame, "Face detected",
                                    (left + 4, top - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                                    (255, 255, 255), 1)

                with self._lock:
                    self._current_frame = frame.copy()
        finally:
            # This thread owns `cap`: it is the one and only place that
            # releases it, and it only does so after its own loop has
            # fully stopped reading. The main thread never calls
            # cap.release() directly anymore.
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
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img,
                                   size=(self.PREVIEW_W, self.PREVIEW_H))
            self._video_label.configure(image=ctk_img, text="")
            self._video_label._ctk_image = ctk_img

            if self._face_detected:
                self._detect_bar.configure(
                    text="● Face detected — ready to capture",
                    text_color="#1D9E75",
                    fg_color=("#d4f5e9", "#0a3d2b"))
            else:
                self._detect_bar.configure(
                    text="● No face detected — position yourself in frame",
                    text_color="gray",
                    fg_color=("gray80", "gray30"))

        self._render_job = self.after(30, self._render_frame)

    def _stop_camera(self):
        if not self._running and self._cap is None:
            # already stopped; just make sure UI state is consistent
            self._start_btn.configure(state="normal" if self._selected_emp else "disabled")
            self._stop_btn.configure(state="disabled")
            self._capture_btn.configure(state="disabled")
            return

        # 1) Signal the background thread to stop.
        self._running = False

        # 2) Cancel the UI's polling loop so it stops touching _current_frame.
        if self._render_job is not None:
            self.after_cancel(self._render_job)
            self._render_job = None

        # 3) Wait for the capture thread to actually exit. It is the one
        #    that calls cap.release() (see _read_frames), so by the time
        #    join() returns, the camera handle is already gone and it is
        #    safe for us to drop our reference. This is the key fix: we
        #    NEVER call self._cap.release() here ourselves anymore, and we
        #    never touch self._cap while the thread might still be inside
        #    cap.read().
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
        self._capture_thread = None
        self._cap = None

        self._video_label.configure(image=None, text="Camera stopped.")
        self._start_btn.configure(state="normal" if self._selected_emp else "disabled")
        self._stop_btn.configure(state="disabled")
        self._capture_btn.configure(state="disabled")
        self._detect_bar.configure(
            text="● No face detected",
            text_color="gray",
            fg_color=("gray80", "gray30"))

    def _capture(self):
        if not self._running:
            return
        if not self._face_detected:
            self._set_status("No face in frame. Position yourself and try again.", error=True)
            return
        if len(self._captured_encodings) >= self.CAPTURE_TARGET:
            return

        with self._lock:
            frame = self._current_frame.copy() if self._current_frame is not None else None

        if frame is None:
            return

        with self._recog_lock:
            encoding = encode_face_from_frame(frame)
        if encoding is None:
            self._set_status("Could not encode face. Try again.", error=True)
            return

        self._captured_encodings.append(encoding)
        count = len(self._captured_encodings)
        self._progress.set(count / self.CAPTURE_TARGET)
        self._progress_label.configure(
            text=f"Samples: {count} / {self.CAPTURE_TARGET}",
            text_color="#1D9E75")
        self._set_status(f"Sample {count} of {self.CAPTURE_TARGET} captured. Keep still.")

        if count >= self.CAPTURE_TARGET:
            self._save_enrollment()

    def _save_enrollment(self):
        avg_encoding = average_encodings(self._captured_encodings)
        ok = save_face_encoding(self._selected_emp["id"], avg_encoding)
        if ok:
            name = f"{self._selected_emp['first_name']} {self._selected_emp['last_name']}"
            self._set_status(f"✅ Face enrolled successfully for {name}!")
            self._delete_btn.configure(state="normal")
            self._emp_label.configure(
                text=f"{name}  ({self._selected_emp['employee_no']})   ✅ Face enrolled")
            self._load_employees()
            self._stop_camera()
        else:
            self._set_status("Failed to save. Please try again.", error=True)
        self._reset_progress()

    def _remove_face(self):
        if not self._selected_emp:
            return
        name = f"{self._selected_emp['first_name']} {self._selected_emp['last_name']}"
        confirm = messagebox.askyesno("Remove Face",
                                      f"Remove face encoding for {name}?")
        if confirm:
            ok = delete_face_encoding(self._selected_emp["id"])
            if ok:
                self._set_status("Face encoding removed.")
                self._delete_btn.configure(state="disabled")
                self._emp_label.configure(
                    text=f"{name}  ({self._selected_emp['employee_no']})   ⚠ No face enrolled")
                self._load_employees()
            else:
                self._set_status("Failed to remove encoding.", error=True)

    def _reset_progress(self):
        self._captured_encodings.clear()
        self._progress.set(0)
        self._progress_label.configure(
            text=f"Samples: 0 / {self.CAPTURE_TARGET}",
            text_color="gray")

    def _set_status(self, msg, error=False):
        color = "#E24B4A" if error else "#1D9E75"
        self._status_label.configure(text=msg, text_color=color)

    def destroy(self):
        # NEW: same join-before-release discipline as _stop_camera, so
        # closing/switching screens can't crash either.
        self._running = False
        if self._render_job is not None:
            try:
                self.after_cancel(self._render_job)
            except Exception:
                pass
            self._render_job = None
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
        self._capture_thread = None
        self._cap = None
        super().destroy()