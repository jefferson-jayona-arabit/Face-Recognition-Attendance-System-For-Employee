import customtkinter as ctk

# ─── Design Tokens ───────────────────────────────────────────────────────────
ACCENT      = "#4F8EF7"
ACCENT_DARK = "#2F6FD8"
GREEN       = "#22C98E"
GREEN_DARK  = "#14916A"
BG_CARD     = ("gray92", "#1E2130")
FG_MUTED    = ("gray45", "gray65")


class MainView(ctk.CTkFrame):
    def __init__(self, parent, on_proceed_login=None, on_start_attendance=None):
        super().__init__(parent, fg_color="transparent")
        self._on_proceed_login    = on_proceed_login
        self._on_start_attendance = on_start_attendance
        self._pulse_step = 0
        self._pulse_job  = None
        self._build_ui()
        self._start_pulse()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Centre wrapper — let it size naturally (no grid_propagate(False))
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=0, column=0)
        wrap.grid_columnconfigure(0, weight=1)

        # ── Hero card ────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            wrap, corner_radius=20,
            fg_color=BG_CARD,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        card.grid(row=0, column=0, padx=40, pady=40, ipadx=20, ipady=10)
        card.grid_columnconfigure(0, weight=1)

        # Animated pulse dot
        self._pulse_label = ctk.CTkLabel(
            card, text="●",
            font=ctk.CTkFont(size=22),
            text_color=GREEN,
        )
        self._pulse_label.grid(row=0, column=0, pady=(36, 0))

        # App icon
        ctk.CTkLabel(
            card, text="🎯",
            font=ctk.CTkFont(size=56),
        ).grid(row=1, column=0, pady=(6, 0))

        # App title
        ctk.CTkLabel(
            card, text="Face Recognition",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=2, column=0, pady=(14, 0))

        ctk.CTkLabel(
            card, text="Attendance Management System",
            font=ctk.CTkFont(size=14),
            text_color=FG_MUTED,
        ).grid(row=3, column=0, pady=(4, 0))

        # Divider
        ctk.CTkFrame(
            card, height=1,
            fg_color=("gray80", "gray30"),
        ).grid(row=4, column=0, sticky="ew", padx=50, pady=28)

        # ── Action buttons ───────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=50, pady=(0, 12), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="🔐  Admin Login",
            fg_color=ACCENT, hover_color=ACCENT_DARK,
            height=48, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_login,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="📷  Start Attendance",
            fg_color=GREEN, hover_color=GREEN_DARK,
            height=48, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_start_attendance,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # Footer note
        ctk.CTkLabel(
            card,
            text="Employees can mark attendance directly from the camera screen.",
            text_color=FG_MUTED, font=ctk.CTkFont(size=11),
            wraplength=420,
        ).grid(row=6, column=0, pady=(8, 32))

    # ── Pulse animation ──────────────────────────────────────────────────────
    _PULSE_COLORS = ["#22C98E", "#1DAE7C", "#179869", "#22C98E", "#2AE09F", "#22C98E"]

    def _start_pulse(self):
        self._animate_pulse()

    def _animate_pulse(self):
        try:
            self._pulse_label.configure(
                text_color=self._PULSE_COLORS[self._pulse_step % len(self._PULSE_COLORS)]
            )
            self._pulse_step += 1
            self._pulse_job = self.after(280, self._animate_pulse)
        except Exception:
            pass

    def _stop_pulse(self):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None

    # ── Handlers ────────────────────────────────────────────────────────────
    def _handle_login(self):
        if callable(self._on_proceed_login):
            self._on_proceed_login()

    def _handle_start_attendance(self):
        if callable(self._on_start_attendance):
            self._on_start_attendance()

    def destroy(self):
        self._stop_pulse()
        super().destroy()
