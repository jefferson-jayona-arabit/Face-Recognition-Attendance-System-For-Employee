import customtkinter as ctk
from tkinter import messagebox
from services.employee_service import (
    get_all_departments,
    get_all_employees,
    add_employee,
    update_employee,
    delete_employee,
    employee_no_exists,
    has_face_encoding,
)


class RegisterScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_employee_id = None
        self._dept_map = {}
        self._build_ui()
        self._load_departments()
        self._load_employees()

    # ------------------------------------------------------------------ #
    #  UI BUILDER                                                          #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ── Left panel: form ──────────────────────────────────────────── #
        form_card = ctk.CTkFrame(self, corner_radius=12)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        form_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_card, text="Employee Registration",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 16))

        fields = [
            ("Employee No.", "employee_no"),
            ("First Name",   "first_name"),
            ("Last Name",    "last_name"),
            ("Position",     "position"),
        ]
        self._entries = {}
        for i, (label, key) in enumerate(fields, start=1):
            ctk.CTkLabel(form_card, text=label).grid(
                row=i, column=0, sticky="w", padx=(20, 8), pady=6)
            entry = ctk.CTkEntry(form_card, placeholder_text=f"Enter {label.lower()}")
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 20), pady=6)
            self._entries[key] = entry

        # Department dropdown
        ctk.CTkLabel(form_card, text="Department").grid(
            row=5, column=0, sticky="w", padx=(20, 8), pady=6)
        self._dept_var = ctk.StringVar(value="Select department")
        self._dept_dropdown = ctk.CTkOptionMenu(
            form_card, variable=self._dept_var, values=["Loading..."])
        self._dept_dropdown.grid(row=5, column=1, sticky="ew", padx=(0, 20), pady=6)

        # Status dropdown (edit mode only)
        ctk.CTkLabel(form_card, text="Status").grid(
            row=6, column=0, sticky="w", padx=(20, 8), pady=6)
        self._status_var = ctk.StringVar(value="active")
        self._status_dropdown = ctk.CTkOptionMenu(
            form_card, variable=self._status_var, values=["active", "inactive"])
        self._status_dropdown.grid(row=6, column=1, sticky="ew", padx=(0, 20), pady=6)

        # Buttons
        btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 20))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._save_btn = ctk.CTkButton(
            btn_frame, text="Save Employee",
            fg_color="#1D9E75", hover_color="#0F6E56",
            command=self._save)
        self._save_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._clear_btn = ctk.CTkButton(
            btn_frame, text="Clear Form",
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._clear_form)
        self._clear_btn.grid(row=0, column=1, padx=6, sticky="ew")

        self._delete_btn = ctk.CTkButton(
            btn_frame, text="Delete",
            fg_color="#E24B4A", hover_color="#A32D2D",
            command=self._delete, state="disabled")
        self._delete_btn.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        # Status label
        self._status_label = ctk.CTkLabel(form_card, text="", text_color="#1D9E75")
        self._status_label.grid(row=8, column=0, columnspan=2, pady=(0, 12))

        # ── Right panel: employee list ────────────────────────────────── #
        list_card = ctk.CTkFrame(self, corner_radius=12)
        list_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(list_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Registered Employees",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ctk.CTkEntry(header, placeholder_text="Search...",
                     textvariable=self._search_var, width=140).grid(
            row=0, column=1, sticky="e")

        self._scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 12))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._employee_rows = []
        self._all_employees = []

    # ------------------------------------------------------------------ #
    #  DATA LOADING                                                        #
    # ------------------------------------------------------------------ #
    def _load_departments(self):
        depts = get_all_departments()
        self._dept_map = {d["name"]: d["id"] for d in depts}
        names = list(self._dept_map.keys()) or ["No departments found"]
        self._dept_dropdown.configure(values=names)
        self._dept_var.set(names[0] if names else "")

    def _load_employees(self):
        self._all_employees = get_all_employees()
        self._render_list(self._all_employees)

    def _render_list(self, employees):
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._employee_rows.clear()

        if not employees:
            ctk.CTkLabel(self._scroll, text="No employees found.",
                         text_color="gray").grid(row=0, column=0, pady=20)
            return

        for emp in employees:
            full_name = f"{emp['first_name']} {emp['last_name']}"
            dept = emp.get("department") or "—"
            has_face = has_face_encoding(emp["id"])

            row = ctk.CTkFrame(self._scroll, corner_radius=8)
            row.grid(sticky="ew", pady=3)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
            info.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(info, text=full_name,
                         font=ctk.CTkFont(weight="bold"), anchor="w").grid(
                row=0, column=0, sticky="w")
            ctk.CTkLabel(info,
                         text=f"{emp['employee_no']}  •  {dept}",
                         text_color="gray", anchor="w", font=ctk.CTkFont(size=12)).grid(
                row=1, column=0, sticky="w")

            badge_color = "#1D9E75" if has_face else "#888780"
            badge_text  = "Face enrolled" if has_face else "No face"
            ctk.CTkLabel(info, text=badge_text,
                         fg_color=badge_color, text_color="white",
                         corner_radius=6, font=ctk.CTkFont(size=11),
                         padx=6, pady=2).grid(row=0, column=1, rowspan=2, sticky="e")

            row.bind("<Button-1>", lambda e, emp=emp: self._select_employee(emp))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, emp=emp: self._select_employee(emp))
                for grandchild in child.winfo_children():
                    grandchild.bind("<Button-1>", lambda e, emp=emp: self._select_employee(emp))

            self._employee_rows.append(row)

    def _filter_list(self):
        query = self._search_var.get().lower()
        filtered = [
            e for e in self._all_employees
            if query in e["first_name"].lower()
            or query in e["last_name"].lower()
            or query in e["employee_no"].lower()
        ]
        self._render_list(filtered)

    # ------------------------------------------------------------------ #
    #  FORM ACTIONS                                                        #
    # ------------------------------------------------------------------ #
    def _select_employee(self, emp):
        self._selected_employee_id = emp["id"]
        self._entries["employee_no"].delete(0, "end")
        self._entries["employee_no"].insert(0, emp["employee_no"])
        self._entries["first_name"].delete(0, "end")
        self._entries["first_name"].insert(0, emp["first_name"])
        self._entries["last_name"].delete(0, "end")
        self._entries["last_name"].insert(0, emp["last_name"])
        self._entries["position"].delete(0, "end")
        self._entries["position"].insert(0, emp.get("position") or "")

        dept_name = emp.get("department") or ""
        if dept_name in self._dept_map:
            self._dept_var.set(dept_name)

        self._status_var.set(emp.get("status") or "active")
        self._delete_btn.configure(state="normal")
        self._save_btn.configure(text="Update Employee")
        self._set_status("")

    def _clear_form(self):
        self._selected_employee_id = None
        for entry in self._entries.values():
            entry.delete(0, "end")
        dept_names = list(self._dept_map.keys())
        if dept_names:
            self._dept_var.set(dept_names[0])
        self._status_var.set("active")
        self._delete_btn.configure(state="disabled")
        self._save_btn.configure(text="Save Employee")
        self._set_status("")

    def _save(self):
        employee_no = self._entries["employee_no"].get().strip()
        first_name  = self._entries["first_name"].get().strip()
        last_name   = self._entries["last_name"].get().strip()
        position    = self._entries["position"].get().strip()
        dept_name   = self._dept_var.get()
        status      = self._status_var.get()

        if not all([employee_no, first_name, last_name]):
            self._set_status("Employee No., First Name and Last Name are required.", error=True)
            return

        dept_id = self._dept_map.get(dept_name)
        if not dept_id:
            self._set_status("Please select a valid department.", error=True)
            return

        if self._selected_employee_id:
            # UPDATE
            if employee_no_exists(employee_no, exclude_id=self._selected_employee_id):
                self._set_status("Employee No. already exists.", error=True)
                return
            ok = update_employee(
                self._selected_employee_id, employee_no,
                first_name, last_name, dept_id, position, status)
            if ok:
                self._set_status("Employee updated successfully.")
                self._clear_form()
                self._load_employees()
            else:
                self._set_status("Update failed. Please try again.", error=True)
        else:
            # INSERT
            if employee_no_exists(employee_no):
                self._set_status("Employee No. already exists.", error=True)
                return
            new_id = add_employee(employee_no, first_name, last_name, dept_id, position)
            if new_id:
                self._set_status(f"Employee saved! (ID: {new_id})")
                self._clear_form()
                self._load_employees()
            else:
                self._set_status("Save failed. Please try again.", error=True)

    def _delete(self):
        if not self._selected_employee_id:
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this employee?\n"
            "Their face encoding and attendance records will also be removed.")
        if confirm:
            ok = delete_employee(self._selected_employee_id)
            if ok:
                self._set_status("Employee deleted.")
                self._clear_form()
                self._load_employees()
            else:
                self._set_status("Delete failed.", error=True)

    def _set_status(self, msg, error=False):
        color = "#E24B4A" if error else "#1D9E75"
        self._status_label.configure(text=msg, text_color=color)