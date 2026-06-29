import customtkinter as ctk

from services.report_service import get_dashboard_summary, get_recent_attendance


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, on_go_register=None):
        super().__init__(parent, fg_color="transparent")
        self._on_go_register = on_go_register
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Attendance Dashboard", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=16
        )

        self._summary_label = ctk.CTkLabel(header, text="Loading summary...", text_color="gray")
        self._summary_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        button_row = ctk.CTkFrame(header, fg_color="transparent")
        button_row.grid(row=1, column=1, sticky="e", padx=16, pady=(0, 16))
        button_row.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(button_row, text="Open Register", command=self._handle_register, fg_color="#1D9E75", hover_color="#0F6E56").grid(sticky="e")

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 12))
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._cards = []
        for idx, title in enumerate(["Active Employees", "Present Today", "Late Today", "Attendance Records"]):
            card = ctk.CTkFrame(cards, corner_radius=12)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0, 8) if idx < 3 else (8, 0), pady=0)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
            value_label = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=24, weight="bold"))
            value_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
            self._cards.append(value_label)

        recent = ctk.CTkFrame(self, corner_radius=12)
        recent.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=0, pady=(12, 0))
        recent.grid_columnconfigure(0, weight=1)
        recent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(recent, text="Recent Attendance", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )

        self._recent_scroll = ctk.CTkScrollableFrame(recent, fg_color="transparent")
        self._recent_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._recent_scroll.grid_columnconfigure(0, weight=1)

    def _refresh(self):
        summary = get_dashboard_summary()
        if summary:
            self._summary_label.configure(text=f"Summary for {summary.get('date', 'today')}")
            values = [
                summary.get("total_employees", 0),
                summary.get("present_today", 0),
                summary.get("late_today", 0),
                summary.get("total_today", 0),
            ]
            for label, value in zip(self._cards, values):
                label.configure(text=str(value))

        rows = get_recent_attendance(limit=8)
        for widget in self._recent_scroll.winfo_children():
            widget.destroy()
        if not rows:
            ctk.CTkLabel(self._recent_scroll, text="No recent activity.", text_color="gray").grid(pady=10)
            return
        for row in rows:
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            ctk.CTkLabel(self._recent_scroll, text=f"{name} • {row.get('attendance_date')} • {row.get('status', 'present')}", anchor="w").grid(sticky="ew", pady=3)

    def _handle_register(self):
        if callable(self._on_go_register):
            self._on_go_register()
