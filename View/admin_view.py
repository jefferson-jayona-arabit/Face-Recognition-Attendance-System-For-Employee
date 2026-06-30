import customtkinter as ctk
from tkinter import messagebox

from Controller.user_controller import UserController

# ─── Design Tokens ───────────────────────────────────────────────────────────
GREEN      = "#22C98E"
GREEN_DARK = "#14916A"
ACCENT     = "#4F8EF7"
ACCENT_DK  = "#2F6FD8"
RED_SOFT   = "#E24B4A"
RED_DARK   = "#A32D2D"
AMBER      = "#F5A623"
BG_CARD    = ("gray92", "#1E2130")
FG_MUTED   = ("gray45", "gray65")

ROLE_COLORS = {
    "admin":    ("#dbeafe", "#1a2a4a", ACCENT),
    "hr":       ("#fef3c7", "#3d2e00", AMBER),
    "employee": ("#d4f5e9", "#0a3d2b", GREEN),
}

TABLE_COLS = [
    ("Username",   160, "w"),
    ("Role",       90,  "center"),
    ("Created",    140, "w"),
]


class AdminView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._selected_user_id = None
        self._all_users        = []
        self._build_ui()
        self._load_users()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ── Left: form ───────────────────────────────────────────────────────
        form_card = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        form_card.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            form_card, text="Admin Accounts",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self._form_subtitle = ctk.CTkLabel(
            form_card,
            text="Create and manage admin / HR accounts.",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED,
        )
        self._form_subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        ctk.CTkFrame(form_card, height=1, fg_color=("gray80", "gray30")).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(0, 16)
        )

        # Username
        ctk.CTkLabel(
            form_card, text="Username *",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 4))
        self._username_entry = ctk.CTkEntry(
            form_card, placeholder_text="e.g. jsmith",
            height=38, corner_radius=8,
        )
        self._username_entry.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 12))

        # Password
        ctk.CTkLabel(
            form_card, text="Password *",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=5, column=0, sticky="w", padx=20, pady=(0, 4))

        pw_row = ctk.CTkFrame(form_card, fg_color="transparent")
        pw_row.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 4))
        pw_row.grid_columnconfigure(0, weight=1)

        self._password_entry = ctk.CTkEntry(
            pw_row, placeholder_text="••••••••",
            height=38, corner_radius=8, show="•",
        )
        self._password_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._eye_btn = ctk.CTkButton(
            pw_row, text="👁", width=38, height=38,
            fg_color="transparent", border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._toggle_pw,
        )
        self._eye_btn.grid(row=0, column=1)
        self._show_pw = False

        self._pw_hint = ctk.CTkLabel(
            form_card,
            text="Leave blank to keep current password when editing.",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._pw_hint.grid(row=7, column=0, sticky="w", padx=20, pady=(0, 12))

        # Role
        ctk.CTkLabel(
            form_card, text="Role",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).grid(row=8, column=0, sticky="w", padx=20, pady=(0, 4))
        self._role_var = ctk.StringVar(value="admin")
        ctk.CTkOptionMenu(
            form_card, variable=self._role_var,
            values=["admin", "hr", "employee"],
            height=38, corner_radius=8,
        ).grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkFrame(form_card, height=1, fg_color=("gray80", "gray30")).grid(
            row=10, column=0, sticky="ew", padx=20, pady=(0, 16)
        )

        # Buttons
        btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_frame.grid(row=11, column=0, sticky="ew", padx=20, pady=(0, 6))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._save_btn = ctk.CTkButton(
            btn_frame, text="💾  Save Account",
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
            form_card, text="🗑  Delete Account",
            fg_color=RED_SOFT, hover_color=RED_DARK,
            height=38, corner_radius=8,
            command=self._delete, state="disabled",
        )
        self._delete_btn.grid(row=12, column=0, sticky="ew", padx=20, pady=(6, 6))

        self._status_label = ctk.CTkLabel(
            form_card, text="",
            font=ctk.CTkFont(size=12), text_color=GREEN,
        )
        self._status_label.grid(row=13, column=0, pady=(0, 16))

        # ── Right: user table ────────────────────────────────────────────────
        list_card = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=BG_CARD,
            border_width=1, border_color=("gray80", "gray25"),
        )
        list_card.grid(row=0, column=1, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(2, weight=1)

        # Table top bar
        top = ctk.CTkFrame(list_card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="Registered Accounts",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            top, text="↻  Refresh",
            width=90, height=32,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._load_users,
        ).grid(row=0, column=1, sticky="e")

        # Column headers
        col_hdr = ctk.CTkFrame(list_card, fg_color=("gray85", "#252839"), corner_radius=0)
        col_hdr.grid(row=1, column=0, sticky="ew")
        for i, (label, width, anchor) in enumerate(TABLE_COLS):
            col_hdr.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                col_hdr, text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=FG_MUTED,
                anchor=anchor, width=width,
            ).grid(row=0, column=i, sticky="ew",
                   padx=(14 if i == 0 else 8, 8), pady=8)

        # Scrollable rows
        self._scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 8))
        for i in range(len(TABLE_COLS)):
            self._scroll.grid_columnconfigure(i, weight=1)

        self._count_label = ctk.CTkLabel(
            list_card, text="",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        )
        self._count_label.grid(row=3, column=0, pady=(0, 10))

    # ── Data ─────────────────────────────────────────────────────────────────
    def _load_users(self):
        self._all_users = UserController.list_users()
        self._render_table(self._all_users)
        self._count_label.configure(text=f"{len(self._all_users)} account(s)")

    def _render_table(self, users):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not users:
            ctk.CTkLabel(
                self._scroll,
                text="No accounts found. Create one using the form.",
                text_color=FG_MUTED,
            ).grid(row=0, column=0, columnspan=len(TABLE_COLS), pady=24)
            return

        for r_idx, user in enumerate(users):
            is_sel   = self._selected_user_id == user.id
            bg       = (ACCENT + "22", "#1a2a4a") if is_sel else (
                ("gray90", "#252839") if r_idx % 2 == 0 else BG_CARD
            )
            r_light, r_dark, r_fg = ROLE_COLORS.get(user.role, ("#eee", "#333", "#888"))

            row_frame = ctk.CTkFrame(
                self._scroll, fg_color=bg,
                corner_radius=4,
                border_width=2 if is_sel else 0,
                border_color=(ACCENT, ACCENT),
            )
            row_frame.grid(row=r_idx, column=0, columnspan=len(TABLE_COLS),
                           sticky="ew", padx=0, pady=1)
            row_frame.grid_columnconfigure(list(range(len(TABLE_COLS))), weight=1)

            # Username cell
            lbl = ctk.CTkLabel(
                row_frame, text=user.username,
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
            )
            lbl.grid(row=0, column=0, sticky="ew", padx=(14, 6), pady=10)
            lbl.bind("<Button-1>", lambda e, u=user: self._select_user(u))

            # Role badge
            badge_frame = ctk.CTkFrame(row_frame, fg_color=(r_light, r_dark), corner_radius=5)
            badge_frame.grid(row=0, column=1, padx=8, pady=6)
            badge_lbl = ctk.CTkLabel(
                badge_frame, text=user.role.capitalize(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=r_fg,
            )
            badge_lbl.grid(padx=8, pady=3)

            # Created date
            created = str(user.created_at)[:10] if user.created_at else "—"
            date_lbl = ctk.CTkLabel(
                row_frame, text=created,
                font=ctk.CTkFont(size=12), anchor="w",
                text_color=FG_MUTED,
            )
            date_lbl.grid(row=0, column=2, sticky="ew", padx=(8, 14), pady=10)

            # Bind clicks
            for w in [row_frame, badge_frame, badge_lbl, date_lbl]:
                w.bind("<Button-1>", lambda e, u=user: self._select_user(u))

    # ── Form actions ─────────────────────────────────────────────────────────
    def _select_user(self, user):
        self._selected_user_id = user.id
        self._username_entry.delete(0, "end")
        self._username_entry.insert(0, user.username)
        self._password_entry.delete(0, "end")
        self._role_var.set(user.role)
        self._delete_btn.configure(state="normal")
        self._save_btn.configure(text="💾  Update Account")
        self._form_subtitle.configure(text=f"Editing: {user.username}")
        self._set_status("")
        self._render_table(self._all_users)

    def _clear_form(self):
        self._selected_user_id = None
        self._username_entry.delete(0, "end")
        self._password_entry.delete(0, "end")
        self._role_var.set("admin")
        self._delete_btn.configure(state="disabled")
        self._save_btn.configure(text="💾  Save Account")
        self._form_subtitle.configure(text="Create and manage admin / HR accounts.")
        self._set_status("")
        self._render_table(self._all_users)

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self._password_entry.configure(show="" if self._show_pw else "•")
        self._eye_btn.configure(text="🙈" if self._show_pw else "👁")

    def _save(self):
        username = self._username_entry.get().strip()
        password = self._password_entry.get().strip()
        role     = self._role_var.get()

        if not username:
            self._set_status("Username is required.", error=True)
            return

        if self._selected_user_id:
            # Update — password optional
            if UserController.username_exists(username, exclude_id=self._selected_user_id):
                self._set_status("Username already taken.", error=True)
                return
            ok = UserController.update_user(
                self._selected_user_id, username, role,
                password=password or None,
            )
            if ok:
                self._set_status("✅  Account updated.")
                self._clear_form()
                self._load_users()
            else:
                self._set_status("Update failed.", error=True)
        else:
            # New account — password required
            if not password:
                self._set_status("Password is required for new accounts.", error=True)
                return
            if len(password) < 6:
                self._set_status("Password must be at least 6 characters.", error=True)
                return
            if UserController.username_exists(username):
                self._set_status("Username already taken.", error=True)
                return
            result = UserController.add_user(username, password, role)
            if result:
                self._set_status(f"✅  Account '{username}' created.")
                self._clear_form()
                self._load_users()
            else:
                self._set_status("Failed to create account.", error=True)

    def _delete(self):
        if not self._selected_user_id:
            return
        username = self._username_entry.get().strip()
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete account '{username}'?\nThis cannot be undone.",
        ):
            return
        if UserController.delete_user(self._selected_user_id):
            self._set_status("Account deleted.")
            self._clear_form()
            self._load_users()
        else:
            self._set_status("Delete failed.", error=True)

    def _set_status(self, message: str, error: bool = False):
        self._status_label.configure(
            text=message,
            text_color=RED_SOFT if error else GREEN,
        )
