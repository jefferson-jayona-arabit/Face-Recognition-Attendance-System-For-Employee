# coding: utf-8
import datetime as dt
import customtkinter as ctk

from Controller.attendance_controller import AttendanceController
from Controller.employee_controller import EmployeeController

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
ACCENT     = "#4F8EF7"
AMBER      = "#F5A623"
RED_SOFT   = "#E24B4A"
BG_CARD    = ("gray92", "#1E2130")
FG_MUTED   = ("gray45", "gray65")

STATUS_COLORS = {
    "present":  ("#d4f5e9", "#0a3d2b", "#22C98E"),
    "late":     ("#fff3cd", "#3d2e00", "#F5A623"),
    "half-day": ("#fde8e8", "#3d0a0a", "#E24B4A"),
    "absent":   ("#fde8e8", "#3d0a0a", "#E24B4A"),
}

TABLE_COLS = [
    ("Date",       110, "w"),
    ("Employee",   150, "w"),
    ("Dept",       120, "w"),
    ("Time In",     80, "center"),
    ("Time Out",    80, "center"),
    ("Status",      80, "center"),
]

QUICK_RANGES = [
    ("Today",       "today"),
    ("Yesterday",   "yesterday"),
    ("This Week",   "week"),
    ("This Month",  "month"),
    ("This Year",   "year"),
    ("All",         "all"),
]


class AttendanceView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._dept_map   = {}   # name → id
        self._active_range = "today"
        self._build_ui()
        self._load_departments()
        self._apply_filters()

    # ═══════════════════════════════════════════════════════════════════════
    # BUILD
    # ═══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top: page title ──────────────────────────────────────────────────
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_bar, text="Attendance Records",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._result_count = ctk.CTkLabel(
            title_bar, text="",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._result_count.grid(row=0, column=1, sticky="e")

        # ── Main body: filter sidebar + table ────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_filter_panel(body)
        self._build_table_panel(body)

    # ── Filter sidebar ───────────────────────────────────────────────────────
    def _build_filter_panel(self, parent):
        sidebar = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
            width=240,
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar, text="🔍  Filters",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 10))

        # ── Quick range buttons ──────────────────────────────────────────────
        ctk.CTkLabel(
            sidebar, text="Quick Range",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        self._range_btns = {}
        for i, (label, key) in enumerate(QUICK_RANGES):
            btn = ctk.CTkButton(
                sidebar, text=label, height=30, corner_radius=6,
                fg_color=ACCENT if key == self._active_range else "transparent",
                hover_color=("gray82", "#252839"),
                text_color="white" if key == self._active_range else ("gray20", "gray80"),
                font=ctk.CTkFont(size=12),
                command=lambda k=key: self._set_quick_range(k),
            )
            btn.grid(row=2 + i, column=0, sticky="ew", padx=12, pady=2)
            self._range_btns[key] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color=("gray80", "gray30")).grid(
            row=8, column=0, sticky="ew", padx=16, pady=(10, 10)
        )

        # ── Custom date range ────────────────────────────────────────────────
        ctk.CTkLabel(
            sidebar, text="Date From",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=9, column=0, sticky="w", padx=16, pady=(0, 3))
        self._date_from = ctk.CTkEntry(
            sidebar, placeholder_text="YYYY-MM-DD",
            height=32, corner_radius=6,
        )
        self._date_from.grid(row=10, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            sidebar, text="Date To",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=11, column=0, sticky="w", padx=16, pady=(0, 3))
        self._date_to = ctk.CTkEntry(
            sidebar, placeholder_text="YYYY-MM-DD",
            height=32, corner_radius=6,
        )
        self._date_to.grid(row=12, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkFrame(sidebar, height=1, fg_color=("gray80", "gray30")).grid(
            row=13, column=0, sticky="ew", padx=16, pady=(4, 10)
        )

        # ── Name / Employee No search ────────────────────────────────────────
        ctk.CTkLabel(
            sidebar, text="Name / Emp. No.",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=14, column=0, sticky="w", padx=16, pady=(0, 3))
        self._name_search = ctk.CTkEntry(
            sidebar, placeholder_text="Search…",
            height=32, corner_radius=6,
        )
        self._name_search.grid(row=15, column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── Department dropdown ──────────────────────────────────────────────
        ctk.CTkLabel(
            sidebar, text="Department",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=16, column=0, sticky="w", padx=16, pady=(0, 3))
        self._dept_var = ctk.StringVar(value="All Departments")
        self._dept_menu = ctk.CTkOptionMenu(
            sidebar, variable=self._dept_var,
            values=["All Departments"],
            height=32, corner_radius=6,
            command=lambda _: None,
        )
        self._dept_menu.grid(row=17, column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── Status filter ────────────────────────────────────────────────────
        ctk.CTkLabel(
            sidebar, text="Status",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=FG_MUTED,
        ).grid(row=18, column=0, sticky="w", padx=16, pady=(0, 3))
        self._status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            sidebar, variable=self._status_var,
            values=["All", "present", "late", "half-day"],
            height=32, corner_radius=6,
            command=lambda _: None,
        ).grid(row=19, column=0, sticky="ew", padx=12, pady=(0, 10))

        ctk.CTkFrame(sidebar, height=1, fg_color=("gray80", "gray30")).grid(
            row=20, column=0, sticky="ew", padx=16, pady=(4, 10)
        )

        # ── Action buttons ───────────────────────────────────────────────────
        ctk.CTkButton(
            sidebar, text="Apply Filters",
            fg_color=GREEN, hover_color=GREEN_DARK,
            height=36, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._apply_filters,
        ).grid(row=21, column=0, sticky="ew", padx=12, pady=(0, 6))

        ctk.CTkButton(
            sidebar, text="Clear Filters",
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            height=36, corner_radius=8,
            command=self._clear_filters,
        ).grid(row=22, column=0, sticky="ew", padx=12, pady=(0, 16))

    # ── Table panel ──────────────────────────────────────────────────────────
    def _build_table_panel(self, parent):
        table_card = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)

        # Column header row
        col_hdr = ctk.CTkFrame(table_card, fg_color=("gray85", "#252839"), corner_radius=0)
        col_hdr.grid(row=0, column=0, sticky="ew")
        for i, (label, width, anchor) in enumerate(TABLE_COLS):
            col_hdr.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                col_hdr, text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=FG_MUTED, anchor=anchor, width=width,
            ).grid(row=0, column=i, sticky="ew",
                   padx=(14 if i == 0 else 8, 8), pady=10)

        self._table_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self._table_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 8))
        for i in range(len(TABLE_COLS)):
            self._table_scroll.grid_columnconfigure(i, weight=1)

    # ═══════════════════════════════════════════════════════════════════════
    # DATA HELPERS
    # ═══════════════════════════════════════════════════════════════════════
    def _load_departments(self):
        depts = EmployeeController.list_departments()
        self._dept_map = {d.name: d.id for d in depts}
        names = ["All Departments"] + list(self._dept_map.keys())
        self._dept_menu.configure(values=names)

    def _get_date_range(self):
        """Return (start_date_str, end_date_str) for the active quick range."""
        today = dt.date.today()
        r = self._active_range
        if r == "today":
            return today.isoformat(), today.isoformat()
        if r == "yesterday":
            d = today - dt.timedelta(days=1)
            return d.isoformat(), d.isoformat()
        if r == "week":
            start = today - dt.timedelta(days=today.weekday())
            return start.isoformat(), today.isoformat()
        if r == "month":
            start = today.replace(day=1)
            return start.isoformat(), today.isoformat()
        if r == "year":
            start = today.replace(month=1, day=1)
            return start.isoformat(), today.isoformat()
        return None, None   # "all"

    def _set_quick_range(self, key: str):
        self._active_range = key
        # Update button styles
        for k, btn in self._range_btns.items():
            active = k == key
            btn.configure(
                fg_color=ACCENT if active else "transparent",
                text_color="white" if active else ("gray20", "gray80"),
            )
        # Clear custom date fields when quick range chosen
        self._date_from.delete(0, "end")
        self._date_to.delete(0, "end")
        self._apply_filters()

    def _clear_filters(self):
        self._active_range = "today"
        for k, btn in self._range_btns.items():
            btn.configure(
                fg_color=ACCENT if k == "today" else "transparent",
                text_color="white" if k == "today" else ("gray20", "gray80"),
            )
        self._date_from.delete(0, "end")
        self._date_to.delete(0, "end")
        self._name_search.delete(0, "end")
        self._dept_var.set("All Departments")
        self._status_var.set("All")
        self._apply_filters()

    def _apply_filters(self):
        # Date range — custom fields override quick range
        custom_from = self._date_from.get().strip()
        custom_to   = self._date_to.get().strip()

        if custom_from or custom_to:
            start_date = custom_from or None
            end_date   = custom_to   or None
            # Deactivate quick-range highlight
            for btn in self._range_btns.values():
                btn.configure(fg_color="transparent",
                              text_color=("gray20", "gray80"))
            self._active_range = "custom"
        else:
            start_date, end_date = self._get_date_range()

        name_q  = self._name_search.get().strip() or None
        dept_n  = self._dept_var.get()
        dept_id = self._dept_map.get(dept_n) if dept_n != "All Departments" else None
        status  = self._status_var.get()
        status  = status if status != "All" else None

        rows = AttendanceController.get_attendance_report(
            start_date=start_date,
            end_date=end_date,
            department_id=dept_id,
            name_search=name_q,
            status=status,
        )
        self._render_table(rows)

    # ═══════════════════════════════════════════════════════════════════════
    # TABLE RENDER
    # ═══════════════════════════════════════════════════════════════════════
    def _render_table(self, rows):
        for w in self._table_scroll.winfo_children():
            w.destroy()

        self._result_count.configure(text=f"{len(rows)} record(s) found")

        if not rows:
            ctk.CTkLabel(
                self._table_scroll,
                text="No records match the selected filters.",
                text_color=FG_MUTED, font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, columnspan=len(TABLE_COLS), pady=40)
            return

        for r_idx, row in enumerate(rows):
            bg       = ("gray90", "#252839") if r_idx % 2 == 0 else BG_CARD
            name     = f"{row.first_name} {row.last_name}".strip()
            dept     = row.department_name or "—"
            time_in  = str(row.time_in)[:5]  if row.time_in  else "—"
            time_out = str(row.time_out)[:5] if row.time_out else "—"
            status   = row.status or "—"
            s_light, s_dark, s_fg = STATUS_COLORS.get(
                status.lower(), ("#eee", "#333", "#888")
            )

            rf = ctk.CTkFrame(self._table_scroll, fg_color=bg, corner_radius=0)
            rf.grid(row=r_idx, column=0, columnspan=len(TABLE_COLS),
                    sticky="ew", padx=0, pady=0)
            rf.grid_columnconfigure(list(range(len(TABLE_COLS))), weight=1)

            cells = [str(row.attendance_date), name, dept, time_in, time_out, ""]
            for c_idx, (text, (_, width, anchor)) in enumerate(zip(cells, TABLE_COLS)):
                if c_idx == 5:
                    bf = ctk.CTkFrame(rf, fg_color=(s_light, s_dark), corner_radius=6)
                    bf.grid(row=0, column=c_idx, padx=8, pady=6)
                    ctk.CTkLabel(
                        bf, text=status.capitalize(),
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=s_fg,
                    ).grid(padx=8, pady=3)
                else:
                    ctk.CTkLabel(
                        rf, text=text,
                        font=ctk.CTkFont(size=12), anchor=anchor,
                    ).grid(row=0, column=c_idx, sticky="ew",
                           padx=(14 if c_idx == 0 else 8, 8), pady=9)
