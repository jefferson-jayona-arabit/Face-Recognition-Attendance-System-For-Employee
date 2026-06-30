# coding: utf-8
"""
Schedule Management View
Allows admins to create / edit / delete work schedules and set one as active.
The active schedule controls:
  - Time-in window  (time_in_start → time_in_end)
  - Late cutoff     (late_cutoff)
  - Time-out window (time_out_start → time_out_end)
"""
import customtkinter as ctk
from tkinter import messagebox

from Controller.attendance_controller import AttendanceController
from DAO.schedule_dao import ScheduleDAO

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
ACCENT     = "#4F8EF7"
ACCENT_DK  = "#2F6FD8"
AMBER      = "#F5A623"
RED_SOFT   = "#E24B4A"
RED_DARK   = "#A32D2D"
BG_CARD    = ("gray92", "#1E2130")
FG_MUTED   = ("gray45", "gray65")


def _fmt(t) -> str:
    """Format a time/timedelta object as HH:MM."""
    if t is None:
        return "—"
    try:
        return t.strftime("%H:%M")
    except AttributeError:
        from datetime import timedelta
        if isinstance(t, timedelta):
            s = int(t.total_seconds())
            return f"{s//3600:02d}:{(s%3600)//60:02d}"
    return str(t)[:5]


class ScheduleView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_id = None
        self._schedules   = []
        self._build_ui()
        self._load()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ── Left: form (scrollable so buttons never get clipped) ────────────
        form_outer = ctk.CTkFrame(
            self, corner_radius=16, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        form_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        form_outer.grid_columnconfigure(0, weight=1)
        form_outer.grid_rowconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(form_outer, fg_color="transparent")
        form.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form, text="Work Schedule",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self._subtitle = ctk.CTkLabel(
            form, text="Define time-in / time-out windows.",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        ctk.CTkFrame(form, height=1, fg_color=("gray80", "gray30")).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(0, 16)
        )

        # Schedule label
        self._add_field(form, row=3,  label="Schedule Name",
                        key="label",          placeholder="e.g. Morning Shift")
        # Time-in window
        self._add_field(form, row=5,  label="Time-In Start (HH:MM)",
                        key="ti_start",       placeholder="06:00")
        self._add_field(form, row=7,  label="Time-In End   (HH:MM)",
                        key="ti_end",         placeholder="08:00")
        self._add_field(form, row=9,  label="Late Cutoff   (HH:MM)",
                        key="late_cutoff",    placeholder="08:01",
                        note="Arrivals at or after this time are marked Late")
        # Time-out window
        self._add_field(form, row=12, label="Time-Out Start (HH:MM)",
                        key="to_start",       placeholder="17:00")
        self._add_field(form, row=14, label="Time-Out End   (HH:MM)",
                        key="to_end",         placeholder="20:00")

        ctk.CTkFrame(form, height=1, fg_color=("gray80", "gray30")).grid(
            row=16, column=0, sticky="ew", padx=20, pady=(8, 16)
        )

        # Buttons
        bf = ctk.CTkFrame(form, fg_color="transparent")
        bf.grid(row=17, column=0, sticky="ew", padx=20, pady=(0, 6))
        bf.grid_columnconfigure((0, 1), weight=1)

        self._save_btn = ctk.CTkButton(
            bf, text="💾  Save",
            fg_color=GREEN, hover_color=GREEN_DARK,
            height=42, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._save,
        )
        self._save_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            bf, text="✖  Clear",
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            height=42, corner_radius=8,
            command=self._clear,
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self._delete_btn = ctk.CTkButton(
            form, text="🗑  Delete Schedule",
            fg_color=RED_SOFT, hover_color=RED_DARK,
            height=38, corner_radius=8,
            command=self._delete, state="disabled",
        )
        self._delete_btn.grid(row=18, column=0, sticky="ew", padx=20, pady=(6, 4))

        self._activate_btn = ctk.CTkButton(
            form, text="⚡  Set as Active",
            fg_color=ACCENT, hover_color=ACCENT_DK,
            height=38, corner_radius=8,
            command=self._set_active, state="disabled",
        )
        self._activate_btn.grid(row=19, column=0, sticky="ew", padx=20, pady=(4, 6))

        self._status_label = ctk.CTkLabel(
            form, text="",
            font=ctk.CTkFont(size=12), text_color=GREEN,
        )
        self._status_label.grid(row=20, column=0, pady=(0, 16))

        # ── Right: schedule list ─────────────────────────────────────────────
        right = ctk.CTkFrame(
            self, corner_radius=16, fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        rhdr = ctk.CTkFrame(right, fg_color="transparent")
        rhdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        rhdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            rhdr, text="Saved Schedules",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            rhdr, text="↻  Refresh",
            width=90, height=32,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            corner_radius=8, command=self._load,
        ).grid(row=0, column=1, sticky="e")

        self._list_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._list_scroll.grid_columnconfigure(0, weight=1)

        # Live clock showing current mode
        self._clock_label = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._clock_label.grid(row=2, column=0, pady=(0, 12))
        self._tick()

    def _add_field(self, parent, row: int, label: str, key: str,
                   placeholder: str = "", note: str = ""):
        ctk.CTkLabel(
            parent, text=label,
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 4))

        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder,
            height=38, corner_radius=8,
        )
        entry.grid(row=row + 1, column=0, sticky="ew", padx=20,
                   pady=(0, 4 if note else 10))
        setattr(self, f"_e_{key}", entry)

        if note:
            ctk.CTkLabel(
                parent, text=note,
                font=ctk.CTkFont(size=11), text_color=FG_MUTED, anchor="w",
            ).grid(row=row + 2, column=0, sticky="w", padx=20, pady=(0, 8))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _tick(self):
        """Update the live mode display every second."""
        try:
            mode  = AttendanceController.get_current_mode()
            sched = AttendanceController.get_active_schedule()
            import datetime as dt
            now = dt.datetime.now().strftime("%H:%M:%S")
            if mode == "time_in":
                mode_text = "🟢  TIME-IN window is open"
            elif mode == "time_out":
                mode_text = "🔵  TIME-OUT window is open"
            else:
                mode_text = "⚫  Outside attendance windows"
            self._clock_label.configure(
                text=f"{now}   ·   Active: {sched.label}   ·   {mode_text}"
            )
        except Exception:
            pass
        self.after(1000, self._tick)

    def _parse_time(self, raw: str) -> str:
        """Validate and normalise HH:MM → HH:MM:SS. Raises ValueError on bad input."""
        raw = raw.strip()
        parts = raw.replace(".", ":").split(":")
        if len(parts) < 2:
            raise ValueError(raw)
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError(raw)
        return f"{h:02d}:{m:02d}:00"

    # ── Data ─────────────────────────────────────────────────────────────────
    def _load(self):
        self._schedules = ScheduleDAO.get_all_schedules()
        self._render_list()

    def _render_list(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        if not self._schedules:
            ctk.CTkLabel(
                self._list_scroll,
                text="No schedules yet. Create one using the form.",
                text_color=FG_MUTED,
            ).grid(row=0, column=0, pady=24)
            return

        for idx, s in enumerate(self._schedules):
            is_sel    = self._selected_id == s.id
            is_active = s.is_active
            bg        = (ACCENT + "22", "#1a2a4a") if is_sel else (
                ("gray90", "#252839") if idx % 2 == 0 else BG_CARD
            )

            card = ctk.CTkFrame(
                self._list_scroll, fg_color=bg, corner_radius=10,
                border_width=2 if is_sel else 0,
                border_color=(ACCENT, ACCENT),
            )
            card.grid(sticky="ew", pady=4)
            card.grid_columnconfigure(0, weight=1)

            row0 = ctk.CTkFrame(card, fg_color="transparent")
            row0.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
            row0.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row0, text=s.label,
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
            ).grid(row=0, column=0, sticky="w")

            if is_active:
                af = ctk.CTkFrame(row0, fg_color=("#d4f5e9", "#0a3d2b"), corner_radius=6)
                af.grid(row=0, column=1, sticky="e")
                ctk.CTkLabel(
                    af, text="⚡ Active",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=GREEN,
                ).grid(padx=8, pady=3)

            detail = (
                f"Time-In: {s.time_in_start_str} – {s.time_in_end_str}   "
                f"Late after: {s.late_cutoff_str}   "
                f"Time-Out: {s.time_out_start_str} – {s.time_out_end_str}"
            )
            ctk.CTkLabel(
                card, text=detail,
                font=ctk.CTkFont(size=11), text_color=FG_MUTED, anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

            for w in card.winfo_children() + [card]:
                w.bind("<Button-1>", lambda e, sc=s: self._select(sc))

    # ── Form actions ─────────────────────────────────────────────────────────
    def _select(self, s):
        self._selected_id = s.id
        self._e_label.delete(0, "end");       self._e_label.insert(0, s.label)
        self._e_ti_start.delete(0, "end");    self._e_ti_start.insert(0, s.time_in_start_str)
        self._e_ti_end.delete(0, "end");      self._e_ti_end.insert(0, s.time_in_end_str)
        self._e_late_cutoff.delete(0, "end"); self._e_late_cutoff.insert(0, s.late_cutoff_str)
        self._e_to_start.delete(0, "end");    self._e_to_start.insert(0, s.time_out_start_str)
        self._e_to_end.delete(0, "end");      self._e_to_end.insert(0, s.time_out_end_str)
        self._delete_btn.configure(state="normal")
        self._activate_btn.configure(
            state="disabled" if s.is_active else "normal"
        )
        self._save_btn.configure(text="💾  Update")
        self._subtitle.configure(text=f"Editing: {s.label}")
        self._set_status("")
        self._render_list()

    def _clear(self):
        self._selected_id = None
        for key in ("label", "ti_start", "ti_end", "late_cutoff", "to_start", "to_end"):
            getattr(self, f"_e_{key}").delete(0, "end")
        self._delete_btn.configure(state="disabled")
        self._activate_btn.configure(state="disabled")
        self._save_btn.configure(text="💾  Save")
        self._subtitle.configure(text="Define time-in / time-out windows.")
        self._set_status("")
        self._render_list()

    def _save(self):
        try:
            label    = self._e_label.get().strip() or "Schedule"
            ti_start = self._parse_time(self._e_ti_start.get())
            ti_end   = self._parse_time(self._e_ti_end.get())
            late_c   = self._parse_time(self._e_late_cutoff.get())
            to_start = self._parse_time(self._e_to_start.get())
            to_end   = self._parse_time(self._e_to_end.get())
        except ValueError as e:
            self._set_status(f"Invalid time value: {e}. Use HH:MM format.", error=True)
            return

        result = ScheduleDAO.save_schedule(
            label, ti_start, ti_end, late_c, to_start, to_end,
            schedule_id=self._selected_id,
        )
        if result:
            self._set_status("✅  Schedule saved.")
            self._clear()
            self._load()
        else:
            self._set_status("Save failed.", error=True)

    def _delete(self):
        if not self._selected_id:
            return
        if messagebox.askyesno("Delete Schedule",
                                "Delete this schedule? This cannot be undone."):
            if ScheduleDAO.delete_schedule(self._selected_id):
                self._set_status("Schedule deleted.")
                self._clear()
                self._load()
            else:
                self._set_status("Delete failed.", error=True)

    def _set_active(self):
        if not self._selected_id:
            return
        if ScheduleDAO.set_active(self._selected_id):
            self._set_status("✅  Schedule set as active.")
            self._load()
            # Re-select to update button state
            for s in self._schedules:
                if s.id == self._selected_id:
                    self._select(s)
                    break
        else:
            self._set_status("Failed to set active.", error=True)

    def _set_status(self, msg: str, error: bool = False):
        self._status_label.configure(
            text=msg,
            text_color=RED_SOFT if error else GREEN,
        )
