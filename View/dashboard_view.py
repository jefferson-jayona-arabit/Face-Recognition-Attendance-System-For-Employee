import customtkinter as ctk
from Controller.attendance_controller import AttendanceController

# ─── Design Tokens ───────────────────────────────────────────────────────────
ACCENT      = "#4F8EF7"
GREEN       = "#22C98E"
GREEN_DARK  = "#14916A"
AMBER       = "#F5A623"
RED_SOFT    = "#E24B4A"
BG_CARD     = ("gray92", "#1E2130")
BG_ROW_ALT  = ("gray88", "#252839")
FG_MUTED    = ("gray45", "gray65")

STATUS_COLORS = {
    "present": ("#d4f5e9", "#0a3d2b", "#22C98E"),
    "late":    ("#fff3cd", "#3d2e00", "#F5A623"),
    "absent":  ("#fde8e8", "#3d0a0a", "#E24B4A"),
}

CARD_CONFIGS = [
    ("👥", "Active Employees", ACCENT,    "#1A2A5E"),
    ("✅", "Present Today",    GREEN,     "#0a3d2b"),
    ("⏰", "Late Today",       AMBER,     "#3d2e00"),
    ("📋", "Total Records",    "#A78BFA", "#2a1a5e"),
]

TABLE_COLS = [
    ("Date",       110, "w"),
    ("Employee",   150, "w"),
    ("Department", 130, "w"),
    ("Time In",    80,  "center"),
    ("Time Out",   80,  "center"),
    ("Status",     80,  "center"),
]


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, on_go_register=None):
        super().__init__(parent, fg_color="transparent")
        self._on_go_register = on_go_register
        self._build_ui()
        self._refresh()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._date_label = ctk.CTkLabel(
            top, text="",
            font=ctk.CTkFont(size=13),
            text_color=FG_MUTED,
        )
        self._date_label.grid(row=1, column=0, sticky="w")

        btn_bar = ctk.CTkFrame(top, fg_color="transparent")
        btn_bar.grid(row=0, column=1, rowspan=2, sticky="e")

        ctk.CTkButton(
            btn_bar, text="↻  Refresh",
            width=110, height=36,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._refresh,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btn_bar, text="+ New Employee",
            width=150, height=36,
            fg_color=GREEN, hover_color=GREEN_DARK,
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._handle_register,
        ).grid(row=0, column=1)

        # ── Stat cards ───────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._card_values = []
        for col, (icon, title, fg, bg) in enumerate(CARD_CONFIGS):
            card = ctk.CTkFrame(
                cards_frame, corner_radius=14,
                fg_color=BG_CARD,
                border_width=1,
                border_color=("gray80", "gray25"),
            )
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0, 10) if col < 3 else 0)
            card.grid_columnconfigure(0, weight=1)

            icon_lbl = ctk.CTkLabel(
                card, text=icon,
                font=ctk.CTkFont(size=26),
            )
            icon_lbl.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 2))

            val_lbl = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color=fg,
            )
            val_lbl.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 4))

            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=12),
                text_color=FG_MUTED,
            ).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 18))

            self._card_values.append(val_lbl)

        # ── Recent attendance table ──────────────────────────────────────────
        table_card = ctk.CTkFrame(
            self, corner_radius=14,
            fg_color=BG_CARD,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        table_card.grid(row=2, column=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(2, weight=1)

        # Section header
        hdr = ctk.CTkFrame(table_card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Recent Attendance",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            hdr, text="Latest 10 records",
            font=ctk.CTkFont(size=12),
            text_color=FG_MUTED,
        ).grid(row=0, column=1, sticky="e")

        # Table column headers
        col_hdr = ctk.CTkFrame(table_card, fg_color=("gray85", "#252839"), corner_radius=0)
        col_hdr.grid(row=1, column=0, sticky="ew", padx=0)
        for i, (label, width, anchor) in enumerate(TABLE_COLS):
            col_hdr.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                col_hdr, text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=FG_MUTED,
                anchor=anchor, width=width,
            ).grid(row=0, column=i, sticky="ew", padx=(16 if i == 0 else 8, 8), pady=8)

        # Scrollable rows
        self._table_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self._table_scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 8))
        for i in range(len(TABLE_COLS)):
            self._table_scroll.grid_columnconfigure(i, weight=1)

    # ── Data ─────────────────────────────────────────────────────────────────
    def _refresh(self):
        summary = AttendanceController.get_dashboard_summary()
        if summary:
            self._date_label.configure(text=f"Summary for {summary.date}")
            values = [
                summary.total_employees,
                summary.present_today,
                summary.late_today,
                summary.total_today,
            ]
            for lbl, val in zip(self._card_values, values):
                lbl.configure(text=str(val))

        # Clear old rows
        for w in self._table_scroll.winfo_children():
            w.destroy()

        rows = AttendanceController.get_recent_attendance(limit=10)
        if not rows:
            ctk.CTkLabel(
                self._table_scroll,
                text="No recent attendance records.",
                text_color=FG_MUTED,
            ).grid(row=0, column=0, columnspan=len(TABLE_COLS), pady=24)
            return

        for r_idx, row in enumerate(rows):
            bg = ("gray90", "#252839") if r_idx % 2 == 0 else ("gray92", "#1E2130")
            name     = f"{row.first_name} {row.last_name}".strip()
            dept     = row.department_name or "—"
            time_in  = str(row.time_in)[:5]  if row.time_in  else "—"
            time_out = str(row.time_out)[:5] if row.time_out else "—"
            status   = row.status or "—"

            s_light, s_dark, s_fg = STATUS_COLORS.get(status.lower(), ("#eee", "#333", "#888"))

            row_frame = ctk.CTkFrame(
                self._table_scroll,
                fg_color=bg, corner_radius=0,
            )
            row_frame.grid(row=r_idx, column=0, columnspan=len(TABLE_COLS),
                           sticky="ew", padx=0, pady=0)
            row_frame.grid_columnconfigure(list(range(len(TABLE_COLS))), weight=1)

            # Columns 0-4: text cells; column 5: status badge
            cells = [str(row.attendance_date), name, dept, time_in, time_out, ""]
            for c_idx, (text, (_, width, anchor)) in enumerate(zip(cells, TABLE_COLS)):
                if c_idx == 5:
                    badge_frame = ctk.CTkFrame(
                        row_frame, fg_color=(s_light, s_dark), corner_radius=6,
                    )
                    badge_frame.grid(row=0, column=c_idx, padx=8, pady=6, sticky="")
                    ctk.CTkLabel(
                        badge_frame, text=status.capitalize(),
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=s_fg,
                    ).grid(padx=8, pady=3)
                else:
                    ctk.CTkLabel(
                        row_frame, text=text,
                        font=ctk.CTkFont(size=12),
                        anchor=anchor,
                    ).grid(row=0, column=c_idx, sticky="ew",
                           padx=(16 if c_idx == 0 else 8, 8), pady=10)

    def _handle_register(self):
        if callable(self._on_go_register):
            self._on_go_register()
