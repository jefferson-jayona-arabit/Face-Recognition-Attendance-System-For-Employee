import customtkinter as ctk
from Controller.user_controller import UserController

# ─── Design Tokens ───────────────────────────────────────────────────────────
ACCENT      = "#4F8EF7"
ACCENT_DARK = "#2F6FD8"
BG_CARD     = ("gray92", "#1E2130")
FG_MUTED    = ("gray45", "gray65")
RED         = "#E24B4A"


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, on_success=None):
        super().__init__(parent, fg_color="transparent")
        self._on_success = on_success
        self._show_pw    = False
        self._build_ui()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Outer centering wrapper
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=0, column=0)
        wrap.grid_columnconfigure(0, weight=1)

        # ── Card — no fixed size, sizes to content ───────────────────────────
        card = ctk.CTkFrame(
            wrap, corner_radius=20,
            fg_color=BG_CARD,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        card.grid(row=0, column=0, padx=40, pady=40, ipadx=20, ipady=10)
        card.grid_columnconfigure(0, weight=1)

        # Icon
        ctk.CTkLabel(
            card, text="🔐",
            font=ctk.CTkFont(size=44),
        ).grid(row=0, column=0, pady=(36, 4))

        # Title
        ctk.CTkLabel(
            card, text="Admin Login",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=1, column=0, pady=(0, 2))

        ctk.CTkLabel(
            card, text="Enter your credentials to continue",
            font=ctk.CTkFont(size=12),
            text_color=FG_MUTED,
        ).grid(row=2, column=0, pady=(0, 20))

        # ── Error banner (hidden by default) ─────────────────────────────────
        self._error_frame = ctk.CTkFrame(
            card, fg_color=(RED, "#5a1a1a"), corner_radius=8,
        )
        self._error_label = ctk.CTkLabel(
            self._error_frame,
            text="Invalid username or password.",
            text_color="white",
            font=ctk.CTkFont(size=12),
        )
        self._error_label.grid(padx=12, pady=8)
        # Not gridded until needed

        # ── Form ─────────────────────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=4, column=0, sticky="ew", padx=44, pady=(0, 6))
        form.grid_columnconfigure(0, weight=1)

        # Username
        ctk.CTkLabel(
            form, text="Username",
            anchor="w", font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._username = ctk.CTkEntry(
            form, placeholder_text="admin",
            height=42, corner_radius=8, width=340,
        )
        self._username.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Password
        ctk.CTkLabel(
            form, text="Password",
            anchor="w", font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.grid(row=3, column=0, sticky="ew")
        pw_row.grid_columnconfigure(0, weight=1)

        self._password = ctk.CTkEntry(
            pw_row, placeholder_text="••••••••",
            height=42, corner_radius=8, show="•",
        )
        self._password.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._eye_btn = ctk.CTkButton(
            pw_row, text="👁",
            width=42, height=42,
            fg_color="transparent", border_width=1,
            text_color=("gray30", "gray70"),
            hover_color=("gray85", "gray25"),
            corner_radius=8,
            command=self._toggle_password,
        )
        self._eye_btn.grid(row=0, column=1)

        # ── Login button ──────────────────────────────────────────────────────
        ctk.CTkButton(
            card, text="Login",
            fg_color=ACCENT, hover_color=ACCENT_DARK,
            height=46, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_login,
        ).grid(row=5, column=0, sticky="ew", padx=44, pady=(20, 6))

        ctk.CTkLabel(
            card, text="Contact your administrator if you cannot log in.",
            text_color=FG_MUTED, font=ctk.CTkFont(size=11),
        ).grid(row=6, column=0, pady=(0, 32))

        # Bind Enter key
        self._username.bind("<Return>", lambda _: self._password.focus())
        self._password.bind("<Return>", lambda _: self._handle_login())
        self._username.focus()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _toggle_password(self):
        self._show_pw = not self._show_pw
        self._password.configure(show="" if self._show_pw else "•")
        self._eye_btn.configure(text="🙈" if self._show_pw else "👁")

    def _show_error(self, msg: str):
        self._error_label.configure(text=msg)
        self._error_frame.grid(row=3, column=0, sticky="ew", padx=44, pady=(0, 6))

    def _hide_error(self):
        self._error_frame.grid_forget()

    def _handle_login(self):
        self._hide_error()
        username = self._username.get().strip()
        password = self._password.get().strip()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        user = UserController.login(username, password)
        if user:
            if callable(self._on_success):
                self._on_success()
        else:
            self._show_error("Invalid username or password.")
            self._password.delete(0, "end")
            self._password.focus()
