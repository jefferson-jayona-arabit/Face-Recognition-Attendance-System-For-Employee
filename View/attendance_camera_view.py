# coding: utf-8
import threading
import datetime as dt
import customtkinter as ctk
from PIL import Image
import cv2
import numpy as np

from Controller.attendance_controller import AttendanceController
from Controller.face_controller import FaceController
from Controller.employee_controller import EmployeeController

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
AMBER      = "#F5A623"
RED_SOFT   = "#E24B4A"
BLUE       = "#4F8EF7"
BG_CARD    = ("gray92", "#1E2130")
FG_MUTED   = ("gray45", "gray65")

# BGR for cv2 boxes
CV_GREEN = (50,  200, 130)   # newly recorded
CV_BLUE  = (220, 140,  50)   # time-out recorded
CV_AMBER = (50,  180, 240)   # already recorded
CV_GRAY  = (140, 140, 140)   # unknown


class AttendanceCameraView(ctk.CTkFrame):
    

    PREVIEW_W, PREVIEW_H = 760, 500
    _RECOG_INTERVAL = 8          # run face recognition every N frames

    # ── Session-persistent class-level state ─────────────────────────────────
    _marked_today:  set  = set()
    _timeout_today: set  = set()
    _emp_cache:     dict = {}

    def __init__(self, parent, on_back=None):
        super().__init__(parent, fg_color="transparent")
        self._on_back            = on_back
        self._cap                = None
        self._running            = False
        self._capture_thread     = None
        self._render_job         = None
        self._mode_job           = None
        self._lock               = threading.Lock()
        self._known_encodings    = []
        self._known_employee_ids = []
        self._current_frame      = None
        self._last_results       = []
        self._frame_count        = 0
        self._flash_job          = None
        self._blink_job          = None
        self._blink_state        = True
        self._shown_already: set = set()   # suppresses repeat "already" log entries
        self._build_ui()
        self._load_known_faces()

    # ── Show hook ────────────────────────────────────────────────────────────
    def grid(self, **kwargs):
        super().grid(**kwargs)
        if not self._running:
            self._load_known_faces()
            self.after(200, self._start_camera)

    # ═══════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ═══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew",
                 padx=16, pady=(12, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="← Back",
            width=90, height=34,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._handle_back,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top, text="Face Attendance",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1)

        # Mode badge (TIME-IN / TIME-OUT / CLOSED)
        self._mode_badge = ctk.CTkLabel(
            top, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=GREEN,
        )
        self._mode_badge.grid(row=0, column=2, sticky="e", padx=(0, 12))

        self._live_badge = ctk.CTkLabel(
            top, text="⬤  LIVE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray60", "gray50"),
        )
        self._live_badge.grid(row=0, column=3, sticky="e")

        # ── Camera panel ─────────────────────────────────────────────────────
        cam_card = ctk.CTkFrame(
            self, corner_radius=16, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        cam_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        cam_card.grid_columnconfigure(0, weight=1)
        cam_card.grid_rowconfigure(1, weight=1)

        cam_hdr = ctk.CTkFrame(cam_card, fg_color="transparent")
        cam_hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        cam_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cam_hdr, text="📷  Camera Feed",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._face_count_label = ctk.CTkLabel(
            cam_hdr, text="",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._face_count_label.grid(row=0, column=1, sticky="e")

        self._video_label = ctk.CTkLabel(
            cam_card,
            text="⏳  Starting camera…",
            font=ctk.CTkFont(size=14), text_color=FG_MUTED,
            width=self.PREVIEW_W, height=self.PREVIEW_H,
        )
        self._video_label.grid(row=1, column=0, padx=12, pady=(0, 6))

        self._flash_bar = ctk.CTkLabel(
            cam_card, text="",
            fg_color=("gray85", "#252839"),
            corner_radius=10, padx=14, pady=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=FG_MUTED,
            wraplength=680,
        )
        self._flash_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            cam_card,
            text="Multiple employees can scan at once — time-in and time-out detected automatically.",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        ).grid(row=3, column=0, pady=(0, 6))

        # ── Color legend ──────────────────────────────────────────────────────
        legend = ctk.CTkFrame(cam_card, fg_color="transparent")
        legend.grid(row=4, column=0, pady=(0, 12))

        _legend_items = [
            (CV_GREEN, "Recognized — recording"),
            (CV_AMBER, "Already recorded today"),
            (CV_GRAY,  "Unknown / not enrolled"),
        ]
        for col, (bgr, text) in enumerate(_legend_items):
            r, g, b = bgr[2], bgr[1], bgr[0]   # BGR → RGB hex
            hex_col = f"#{r:02x}{g:02x}{b:02x}"
            item = ctk.CTkFrame(legend, fg_color="transparent")
            item.grid(row=0, column=col, padx=14)
            ctk.CTkLabel(
                item, text="■",
                font=ctk.CTkFont(size=16),
                text_color=hex_col,
            ).grid(row=0, column=0, padx=(0, 4))
            ctk.CTkLabel(
                item, text=text,
                font=ctk.CTkFont(size=11),
                text_color=FG_MUTED,
            ).grid(row=0, column=1)

        # ── Side log ─────────────────────────────────────────────────────────
        log_card = ctk.CTkFrame(
            self, corner_radius=16, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        log_card.grid(row=1, column=1, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        log_hdr = ctk.CTkFrame(log_card, fg_color="transparent")
        log_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 6))
        log_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_hdr, text="📋  Session Log",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._log_count_label = ctk.CTkLabel(
            log_hdr, text="0 events",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._log_count_label.grid(row=0, column=1, sticky="e")

        self._log_scroll = ctk.CTkScrollableFrame(log_card, fg_color="transparent")
        self._log_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._log_scroll.grid_columnconfigure(0, weight=1)

        self._enrolled_label = ctk.CTkLabel(
            log_card, text="",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._enrolled_label.grid(row=2, column=0, pady=(0, 12))

        self._log_event_count = 0

    # ═══════════════════════════════════════════════════════════════════════
    # CAMERA
    # ═══════════════════════════════════════════════════════════════════════
    def _load_known_faces(self):
        try:
            self._known_encodings, self._known_employee_ids = \
                FaceController.load_known_faces()
        except Exception:
            self._known_encodings, self._known_employee_ids = [], []
        try:
            self._enrolled_label.configure(
                text=f"{len(self._known_employee_ids)} enrolled face(s)"
            )
        except Exception:
            pass

    def _start_camera(self):
        if self._running:
            return
        try:
            self._video_label.configure(image=None, text="⏳  Starting camera…")
        except Exception:
            pass

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            try:
                self._video_label.configure(text="❌  Could not access camera.")
            except Exception:
                pass
            if self._cap:
                self._cap.release()
            self._cap = None
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._running     = True
        self._frame_count = 0
        self._last_results = []
        self._set_flash("👀  Watching for faces…", "neutral")
        self._update_mode_badge()
        self._blink_live()
        self._capture_thread = threading.Thread(
            target=self._read_frames, daemon=True
        )
        self._capture_thread.start()
        self._render_frame()

    def _update_mode_badge(self):
        if not self._running:
            return
        mode = AttendanceController.get_current_mode()
        sched = AttendanceController.get_active_schedule()
        if mode == "time_in":
            text  = f"🟢  TIME-IN  ({sched.time_in_start_str}–{sched.time_in_end_str})"
            color = GREEN
        elif mode == "time_out":
            text  = f"🔵  TIME-OUT  ({sched.time_out_start_str}–{sched.time_out_end_str})"
            color = BLUE
        else:
            text  = "⚫  Outside window"
            color = ("gray55", "gray55")
        try:
            self._mode_badge.configure(text=text, text_color=color)
        except Exception:
            pass
        self._mode_job = self.after(5000, self._update_mode_badge)

    def _blink_live(self):
        if not self._running:
            return
        try:
            self._live_badge.configure(
                text_color=RED_SOFT if self._blink_state else ("gray55", "gray45")
            )
            self._blink_state = not self._blink_state
            self._blink_job = self.after(700, self._blink_live)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # RECOGNITION THREAD
    # ═══════════════════════════════════════════════════════════════════════
    def _read_frames(self):
        cap = self._cap
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                self._frame_count += 1

                results = self._last_results

                if (self._frame_count % self._RECOG_INTERVAL == 0
                        and self._known_encodings):
                    results = FaceController.recognize_all_faces_from_frame(
                        frame,
                        self._known_encodings,
                        self._known_employee_ids,
                    )
                    self._last_results = results

                    matched = [eid for (eid, _, _) in results if eid is not None]
                    if matched:
                        mode = AttendanceController.get_current_mode()
                        self.after(
                            0,
                            lambda ids=matched, m=mode: self._process_matches(ids, m),
                        )

                annotated = self._draw_boxes(frame.copy(), results)
                with self._lock:
                    self._current_frame = annotated

        finally:
            if cap:
                cap.release()
            with self._lock:
                self._current_frame = None

    def _draw_boxes(self, frame, results):
        mode = AttendanceController.get_current_mode()
        for emp_id, _, loc in results:
            top, right, bottom, left = loc

            if emp_id is None:
                colour, label = CV_GRAY, "Unknown"
            else:
                emp  = AttendanceCameraView._emp_cache.get(emp_id)
                name = emp.full_name if emp else f"ID {emp_id}"

                # Sync session sets from DB on first draw encounter
                if emp_id not in AttendanceCameraView._marked_today:
                    if AttendanceController.has_timed_in(emp_id):
                        AttendanceCameraView._marked_today.add(emp_id)
                if emp_id not in AttendanceCameraView._timeout_today:
                    if AttendanceController.has_timed_out(emp_id):
                        AttendanceCameraView._timeout_today.add(emp_id)

                if mode == "time_out":
                    if emp_id in AttendanceCameraView._timeout_today:
                        colour = CV_AMBER
                        label  = f"{name} — Already Timed Out"
                    else:
                        colour = CV_GREEN
                        label  = f"{name} — Time-Out Recording..."
                else:
                    if emp_id in AttendanceCameraView._marked_today:
                        colour = CV_AMBER
                        label  = f"{name} — Already Timed In"
                    else:
                        colour = CV_GREEN
                        label  = f"{name} — Time-In Recording..."

            cv2.rectangle(frame, (left, top), (right, bottom), colour, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame, (left, top - th - 10), (left + tw + 10, top), colour, -1)
            cv2.putText(frame, label, (left + 5, top - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        return frame

    # ═══════════════════════════════════════════════════════════════════════
    # ATTENDANCE RECORDING  (main thread)
    # ═══════════════════════════════════════════════════════════════════════
    def _process_matches(self, emp_ids, mode):
        newly_in    = []
        newly_out   = []

        for emp_id in emp_ids:
            # Cache employee object
            if emp_id not in AttendanceCameraView._emp_cache:
                emp = EmployeeController.get_employee(emp_id)
                if emp:
                    AttendanceCameraView._emp_cache[emp_id] = emp

            emp = AttendanceCameraView._emp_cache.get(emp_id)
            if not emp:
                continue

            if mode == "time_out":
                if emp_id not in AttendanceCameraView._timeout_today:
                    # First encounter this session — check DB in case they timed out
                    # in a previous session or before the app restarted
                    if AttendanceController.has_timed_out(emp_id):
                        # Already in DB — sync the session set
                        AttendanceCameraView._timeout_today.add(emp_id)
                        if emp_id not in self._shown_already:
                            self._shown_already.add(emp_id)
                            self._add_log_entry(emp, event="already_out")
                    else:
                        ok = AttendanceController.record_time_out(emp_id)
                        if ok:
                            AttendanceCameraView._timeout_today.add(emp_id)
                            newly_out.append(emp.full_name)
                            self._add_log_entry(emp, event="time_out")
                        else:
                            # No time-in row at all for today
                            if emp_id not in self._shown_already:
                                self._shown_already.add(emp_id)
                                self._add_log_entry(emp, event="no_timein")
                elif emp_id not in self._shown_already:
                    self._shown_already.add(emp_id)
                    self._add_log_entry(emp, event="already_out")

            elif mode == "time_in":
                if emp_id not in AttendanceCameraView._marked_today:
                    # Check DB in case they timed in before this session
                    if AttendanceController.has_timed_in(emp_id):
                        AttendanceCameraView._marked_today.add(emp_id)
                        if emp_id not in self._shown_already:
                            self._shown_already.add(emp_id)
                            self._add_log_entry(emp, event="already_in")
                    else:
                        AttendanceController.record_attendance(emp_id)
                        AttendanceCameraView._marked_today.add(emp_id)
                        newly_in.append(emp.full_name)
                        self._add_log_entry(emp, event="time_in")
                elif emp_id not in self._shown_already:
                    self._shown_already.add(emp_id)
                    self._add_log_entry(emp, event="already_in")

            else:  # closed
                if emp_id not in self._shown_already:
                    self._shown_already.add(emp_id)
                    self._add_log_entry(emp, event="closed")

        # Face count badge
        visible = len(self._last_results)
        matched = sum(1 for (eid, _, _) in self._last_results if eid is not None)
        try:
            self._face_count_label.configure(
                text=f"{visible} face(s)  ·  {matched} matched"
            )
        except Exception:
            pass

        # Flash banner
        if newly_in:
            names = ", ".join(newly_in)
            n = len(newly_in)
            msg = (f"✅  Time-In recorded: {names}"
                   if n == 1
                   else f"✅  {n} employees timed in: {names}")
            self._set_flash(msg, "success")
            self._reschedule_flash()

        elif newly_out:
            names = ", ".join(newly_out)
            n = len(newly_out)
            msg = (f"✅  Time-Out recorded: {names}"
                   if n == 1
                   else f"✅  {n} employees timed out: {names}")
            self._set_flash(msg, "info")
            self._reschedule_flash()

        # Update log count
        try:
            self._log_count_label.configure(
                text=f"{len(AttendanceCameraView._marked_today)} timed-in  ·  "
                     f"{len(AttendanceCameraView._timeout_today)} timed-out"
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # FEEDBACK
    # ═══════════════════════════════════════════════════════════════════════
    def _set_flash(self, text: str, mode: str):
        cfgs = {
            "success": {"fg_color": ("#d4f5e9", "#0a3d2b"),  "text_color": GREEN},
            "info":    {"fg_color": ("#dbeafe", "#1a2a4a"),  "text_color": BLUE},
            "warning": {"fg_color": ("#fff3cd", "#3d2e00"),  "text_color": AMBER},
            "neutral": {"fg_color": ("gray85",  "#252839"),  "text_color": FG_MUTED},
        }
        cfg = cfgs.get(mode, cfgs["neutral"])
        try:
            self._flash_bar.configure(text=text, **cfg)
        except Exception:
            pass

    def _reschedule_flash(self):
        if self._flash_job:
            self.after_cancel(self._flash_job)
        self._flash_job = self.after(5000, self._reset_flash)

    def _reset_flash(self):
        self._set_flash("👀  Watching for faces…", "neutral")

    _EVENT_CONFIGS = {
        "time_in":    ("✅ Time-In Recorded",     ("#d4f5e9", "#0a3d2b"), GREEN),
        "time_out":   ("✅ Time-Out Recorded",    ("#d4f5e9", "#0a3d2b"), GREEN),
        "already_in": ("⚠ Already Timed In",     ("#fff3cd", "#3d2e00"), AMBER),
        "already_out":("⚠ Already Timed Out",    ("#fff3cd", "#3d2e00"), AMBER),
        "no_timein":  ("⚠ No Time-In Found",     ("#fde8e8", "#3d0a0a"), RED_SOFT),
        "closed":     ("⚫ Outside Window",       ("gray82",  "gray35"),  ("gray50", "gray55")),
    }

    def _add_log_entry(self, emp, event: str):
        label_text, badge_bg, badge_fg = self._EVENT_CONFIGS.get(
            event, ("Event", ("gray82", "gray35"), ("gray50", "gray55"))
        )
        time_str = dt.datetime.now().strftime("%H:%M:%S")
        bg_map = {
            "time_in":    ("#eafaf3", "#0d2b1e"),
            "time_out":   ("#eafaf3", "#0d2b1e"),
            "already_in": ("#fef9e7", "#2d2200"),
            "already_out":("#fef9e7", "#2d2200"),
            "no_timein":  ("#fde8e8", "#3d0a0a"),
            "closed":     ("gray90",  "#252839"),
        }
        bg = bg_map.get(event, ("gray90", "#252839"))

        entry = ctk.CTkFrame(self._log_scroll, fg_color=bg, corner_radius=8)
        entry.grid(sticky="ew", pady=3)
        entry.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            entry, text=emp.full_name,
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(6, 1))

        info = ctk.CTkFrame(entry, fg_color="transparent")
        info.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info, text=time_str,
            font=ctk.CTkFont(size=11), text_color=FG_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        badge = ctk.CTkFrame(info, fg_color=badge_bg, corner_radius=5)
        badge.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            badge, text=label_text,
            font=ctk.CTkFont(size=10, weight="bold"), text_color=badge_fg,
        ).grid(padx=7, pady=2)

        self._log_event_count += 1
        try:
            self._log_count_label.configure(
                text=f"{self._log_event_count} event(s)"
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # RENDER LOOP
    # ═══════════════════════════════════════════════════════════════════════
    def _render_frame(self):
        if not self._running:
            self._render_job = None
            return

        with self._lock:
            frame = self._current_frame.copy() if self._current_frame is not None else None

        if frame is not None:
            preview = cv2.resize(frame, (self.PREVIEW_W, self.PREVIEW_H))
            img     = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(
                light_image=img, dark_image=img,
                size=(self.PREVIEW_W, self.PREVIEW_H),
            )
            self._video_label.configure(image=ctk_img, text="")
            self._video_label._ctk_image = ctk_img

        self._render_job = self.after(30, self._render_frame)

    # ═══════════════════════════════════════════════════════════════════════
    # STOP / CLEANUP
    # ═══════════════════════════════════════════════════════════════════════
    def _stop_camera(self):
        if not self._running and self._cap is None:
            return
        self._running = False

        for job in (self._blink_job, self._flash_job,
                    self._render_job, self._mode_job):
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        self._blink_job = self._flash_job = self._render_job = self._mode_job = None

        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        self._capture_thread = None
        self._cap = None

        try:
            self._video_label.configure(image=None, text="Camera stopped.")
            self._live_badge.configure(text_color=("gray60", "gray50"))
            self._mode_badge.configure(text="")
        except Exception:
            pass

    def destroy(self):
        self._stop_camera()
        super().destroy()

    def _handle_back(self):
        self._stop_camera()
        if callable(self._on_back):
            self._on_back()
