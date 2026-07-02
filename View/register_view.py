import customtkinter as ctk
from tkinter import messagebox

from Controller.employee_controller import EmployeeController
from events import AppEvents

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
ACCENT     = "#4F8EF7"
ACCENT_DK  = "#2F6FD8"
RED_SOFT   = "#E24B4A"
RED_DARK   = "#A32D2D"
BG_CARD    = ("gray92", "#1E2130")
FG_MUTED   = ("gray45", "gray65")

TABLE_COLS = [
    ("Emp. No.",   1, "w",      "w"),
    ("Name",       2, "w",      "w"),
    ("Department", 2, "w",      "w"),
    ("Position",   2, "w",      "w"),
    ("Status",     1, "center", "center"),
    ("Face",       1, "center", "center"),
]


class RegisterView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_employee_id = None
        self._dept_map             = {}
        self._all_employees        = []
        self._build_ui()
        self.after(100, self._deferred_init)
        AppEvents.on("employee_changed", self._on_employee_changed)

    def _deferred_init(self):
        self._load_departments()
        self._load_employees()

    def _on_employee_changed(self):
        self._load_departments()
        self._load_employees()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── Left: registration form ──────────────────────────────────────────
        form_card = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        form_card.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            form_card, text="Employee Registration",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self._form_subtitle = ctk.CTkLabel(
            form_card, text="Fill in the fields below to add a new employee.",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._form_subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        # Divider
        ctk.CTkFrame(form_card, height=1, fg_color=("gray80", "gray30")).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(0, 16)
        )

        # Form fields — explicit sequential rows to avoid overlap
        self._entries = {}

        # Row 3-4: Employee No.
        ctk.CTkLabel(
            form_card, text="Employee No. *",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 4))
        self._entries["employee_no"] = ctk.CTkEntry(
            form_card, placeholder_text="e.g. EMP-001",
            height=38, corner_radius=8,
        )
        self._entries["employee_no"].grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Row 5-6: First Name
        ctk.CTkLabel(
            form_card, text="First Name *",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=5, column=0, sticky="w", padx=20, pady=(0, 4))
        self._entries["first_name"] = ctk.CTkEntry(
            form_card, placeholder_text="e.g. Juan",
            height=38, corner_radius=8,
        )
        self._entries["first_name"].grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Row 7-8: Last Name
        ctk.CTkLabel(
            form_card, text="Last Name *",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=7, column=0, sticky="w", padx=20, pady=(0, 4))
        self._entries["last_name"] = ctk.CTkEntry(
            form_card, placeholder_text="e.g. Dela Cruz",
            height=38, corner_radius=8,
        )
        self._entries["last_name"].grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Row 9-10: Position
        ctk.CTkLabel(
            form_card, text="Position",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=9, column=0, sticky="w", padx=20, pady=(0, 4))
        self._entries["position"] = ctk.CTkEntry(
            form_card, placeholder_text="e.g. Software Engineer",
            height=38, corner_radius=8,
        )
        self._entries["position"].grid(row=10, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Row 11-12: Department dropdown
        ctk.CTkLabel(
            form_card, text="Department",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=11, column=0, sticky="w", padx=20, pady=(0, 4))
        self._dept_var = ctk.StringVar(value="Select department")
        self._dept_dropdown = ctk.CTkOptionMenu(
            form_card, variable=self._dept_var,
            values=["Loading…"], height=38,
        )
        self._dept_dropdown.grid(row=12, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Status dropdown
        ctk.CTkLabel(
            form_card, text="Status",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=13, column=0, sticky="w", padx=20, pady=(0, 4))
        self._status_var = ctk.StringVar(value="active")
        ctk.CTkOptionMenu(
            form_card, variable=self._status_var,
            values=["active", "inactive"], height=38,
        ).grid(row=14, column=0, sticky="ew", padx=20, pady=(0, 16))

        # Divider
        ctk.CTkFrame(form_card, height=1, fg_color=("gray80", "gray30")).grid(
            row=15, column=0, sticky="ew", padx=20, pady=(0, 16)
        )

        # Buttons
        btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_frame.grid(row=16, column=0, sticky="ew", padx=20, pady=(0, 6))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._save_btn = ctk.CTkButton(
            btn_frame, text="💾  Save Employee",
            fg_color=GREEN, hover_color=GREEN_DARK,
            height=42, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self._save,
        )
        self._save_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self._clear_btn = ctk.CTkButton(
            btn_frame, text="✖  Clear",
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            height=42, corner_radius=8,
            command=self._clear_form,
        )
        self._clear_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self._delete_btn = ctk.CTkButton(
            form_card, text="🗑  Delete Employee",
            fg_color=RED_SOFT, hover_color=RED_DARK,
            height=38, corner_radius=8,
            command=self._delete, state="disabled",
        )
        self._delete_btn.grid(row=17, column=0, sticky="ew", padx=20, pady=(6, 6))

        self._status_label = ctk.CTkLabel(
            form_card, text="",
            font=ctk.CTkFont(size=12), text_color=GREEN,
        )
        self._status_label.grid(row=18, column=0, pady=(0, 16))

        # ── Right: employee table ────────────────────────────────────────────
        list_card = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        list_card.grid(row=0, column=1, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(2, weight=1)

        # Table header bar
        table_top = ctk.CTkFrame(list_card, fg_color="transparent")
        table_top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        table_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            table_top, text="Registered Employees",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        search_row = ctk.CTkFrame(table_top, fg_color="transparent")
        search_row.grid(row=0, column=1, sticky="e")
        search_row.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ctk.CTkEntry(
            search_row, placeholder_text="🔍  Search…",
            textvariable=self._search_var,
            width=180, height=34, corner_radius=8,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            search_row, text="↻  Refresh",
            width=90, height=34,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._load_employees,
        ).grid(row=0, column=1)

        # Column headers — weights from TABLE_COLS
        col_hdr = ctk.CTkFrame(list_card, fg_color=("gray85", "#252839"), corner_radius=0)
        col_hdr.grid(row=1, column=0, sticky="ew")
        for i, (label, weight, h_anchor, _) in enumerate(TABLE_COLS):
            col_hdr.grid_columnconfigure(i, weight=weight)
            ctk.CTkLabel(
                col_hdr, text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=FG_MUTED,
                anchor=h_anchor,
            ).grid(row=0, column=i, sticky="ew",
                   padx=(14 if i == 0 else 6, 6), pady=8)

        # Scrollable rows — same weights as header
        self._scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 8))
        for i, (_, weight, _, _) in enumerate(TABLE_COLS):
            self._scroll.grid_columnconfigure(i, weight=weight)

        # Footer count
        self._emp_count_label = ctk.CTkLabel(
            list_card, text="",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._emp_count_label.grid(row=3, column=0, pady=(0, 10))

    # ── Data ─────────────────────────────────────────────────────────────────
    def _load_departments(self):
        departments = EmployeeController.list_departments()
        self._dept_map = {d.name: d.id for d in departments}
        names = list(self._dept_map.keys()) or ["No departments"]
        self._dept_dropdown.configure(values=names)
        self._dept_var.set(names[0] if names else "")

    def _load_employees(self):
        self._all_employees = EmployeeController.list_employees()
        self._render_table(self._all_employees)
        self._emp_count_label.configure(text=f"{len(self._all_employees)} employee(s) registered")

    def _render_table(self, employees):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not employees:
            ctk.CTkLabel(
                self._scroll, text="No employees found.",
                text_color=FG_MUTED,
            ).grid(row=0, column=0, columnspan=len(TABLE_COLS), pady=24)
            return

        for r_idx, emp in enumerate(employees):
            enrolled  = EmployeeController.employee_has_face_encoding(emp.id)
            is_sel    = self._selected_employee_id == emp.id
            bg        = (ACCENT + "22", "#1a2a4a") if is_sel else (
                ("gray90", "#252839") if r_idx % 2 == 0 else BG_CARD
            )
            border_w  = 2 if is_sel else 0

            row_frame = ctk.CTkFrame(
                self._scroll, fg_color=bg,
                corner_radius=4,
                border_width=border_w,
                border_color=(ACCENT, ACCENT),
            )
            row_frame.grid(row=r_idx, column=0, columnspan=len(TABLE_COLS),
                           sticky="ew", padx=0, pady=1)
            # Row column weights MUST match header weights exactly.
            for i, (_, weight, _, _) in enumerate(TABLE_COLS):
                row_frame.grid_columnconfigure(i, weight=weight)

            # Status badge
            s_light  = ("#d4f5e9", "#0a3d2b") if emp.status == "active" else ("gray82", "gray35")
            s_fg     = GREEN if emp.status == "active" else ("gray50", "gray55")

            # Face badge
            f_light  = ("#d4f5e9", "#0a3d2b") if enrolled else ("gray82", "gray35")
            f_fg     = GREEN if enrolled else ("gray50", "gray55")
            f_text   = "✓" if enrolled else "—"

            cells = [
                (emp.employee_no, 0, "w"),
                (emp.full_name,   1, "w"),
                (emp.department or "—", 2, "w"),
                (emp.position or "—",   3, "w"),
            ]
            for (text, c_idx, anchor) in cells:
                lbl = ctk.CTkLabel(
                    row_frame, text=text,
                    font=ctk.CTkFont(size=12,
                                     weight="bold" if c_idx == 1 else "normal"),
                    anchor=anchor,
                )
                lbl.grid(row=0, column=c_idx, sticky="ew",
                         padx=(14 if c_idx == 0 else 6, 6), pady=9)
                lbl.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))

            # Status badge cell — wrapper fills column, badge centered inside
            status_wrapper = ctk.CTkFrame(row_frame, fg_color="transparent", corner_radius=0)
            status_wrapper.grid(row=0, column=4, sticky="nsew", padx=4, pady=4)
            status_wrapper.grid_columnconfigure(0, weight=1)
            status_wrapper.grid_rowconfigure(0, weight=1)
            sbf = ctk.CTkFrame(status_wrapper, fg_color=s_light, corner_radius=5)
            sbf.grid(row=0, column=0)
            slbl = ctk.CTkLabel(
                sbf, text=emp.status.capitalize(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=s_fg,
            )
            slbl.grid(padx=7, pady=3)
            status_wrapper.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))
            sbf.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))
            slbl.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))

            # Face badge cell — wrapper fills column, badge centered inside
            face_wrapper = ctk.CTkFrame(row_frame, fg_color="transparent", corner_radius=0)
            face_wrapper.grid(row=0, column=5, sticky="nsew", padx=4, pady=4)
            face_wrapper.grid_columnconfigure(0, weight=1)
            face_wrapper.grid_rowconfigure(0, weight=1)
            fbf = ctk.CTkFrame(face_wrapper, fg_color=f_light, corner_radius=5)
            fbf.grid(row=0, column=0)
            flbl = ctk.CTkLabel(
                fbf, text=f_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=f_fg,
            )
            flbl.grid(padx=7, pady=3)
            face_wrapper.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))
            fbf.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))
            flbl.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))
            row_frame.bind("<Button-1>", lambda e, em=emp: self._select_employee(em))

    def _filter_list(self):
        q = self._search_var.get().lower()
        filtered = [
            e for e in self._all_employees
            if q in e.first_name.lower()
            or q in e.last_name.lower()
            or q in e.employee_no.lower()
            or (e.department or "").lower().startswith(q)
        ]
        self._render_table(filtered)

    # ── Form actions ─────────────────────────────────────────────────────────
    def _select_employee(self, emp):
        self._selected_employee_id = emp.id
        self._entries["employee_no"].delete(0, "end")
        self._entries["employee_no"].insert(0, emp.employee_no)
        self._entries["first_name"].delete(0, "end")
        self._entries["first_name"].insert(0, emp.first_name)
        self._entries["last_name"].delete(0, "end")
        self._entries["last_name"].insert(0, emp.last_name)
        self._entries["position"].delete(0, "end")
        self._entries["position"].insert(0, emp.position or "")
        self._dept_var.set(emp.department or "")
        self._status_var.set(emp.status)
        self._delete_btn.configure(state="normal")
        self._save_btn.configure(text="💾  Update Employee")
        self._form_subtitle.configure(text=f"Editing: {emp.full_name}")
        self._set_status("")
        self._render_table(self._all_employees)

    def _clear_form(self):
        self._selected_employee_id = None
        for entry in self._entries.values():
            entry.delete(0, "end")
        names = list(self._dept_map.keys())
        if names:
            self._dept_var.set(names[0])
        self._status_var.set("active")
        self._delete_btn.configure(state="disabled")
        self._save_btn.configure(text="💾  Save Employee")
        self._form_subtitle.configure(
            text="Fill in the fields below to add a new employee."
        )
        self._set_status("")
        self._render_table(self._all_employees)

    def _save(self):
        employee_no = self._entries["employee_no"].get().strip()
        first_name  = self._entries["first_name"].get().strip()
        last_name   = self._entries["last_name"].get().strip()
        position    = self._entries["position"].get().strip()
        dept_name   = self._dept_var.get()
        status      = self._status_var.get()

        if not all([employee_no, first_name, last_name]):
            self._set_status("Employee No., First Name, and Last Name are required.", error=True)
            return

        dept_id = self._dept_map.get(dept_name)
        if not dept_id:
            self._set_status("Please select a valid department.", error=True)
            return

        if self._selected_employee_id:
            if EmployeeController.employee_no_exists(employee_no, self._selected_employee_id):
                self._set_status("Employee No. already exists.", error=True)
                return
        else:
            if EmployeeController.employee_no_exists(employee_no):
                self._set_status("Employee No. already exists.", error=True)
                return

        result = EmployeeController.save_employee(
            employee_no, first_name, last_name, dept_id, position,
            employee_id=self._selected_employee_id, status=status,
        )

        if result:
            self._set_status("✅  Employee saved successfully.")
            self._clear_form()
            self._load_employees()
        else:
            self._set_status("Save failed. Please try again.", error=True)

    def _delete(self):
        if not self._selected_employee_id:
            return
        if messagebox.askyesno(
            "Confirm Delete",
            "Delete this employee?\nTheir face encoding and attendance records will also be removed.",
        ):
            if EmployeeController.delete_employee(self._selected_employee_id):
                self._set_status("Employee deleted.")
                self._clear_form()
                self._load_employees()
            else:
                self._set_status("Delete failed.", error=True)

    def _set_status(self, message: str, error: bool = False):
        self._status_label.configure(
            text=message,
            text_color=RED_SOFT if error else GREEN,
        )
