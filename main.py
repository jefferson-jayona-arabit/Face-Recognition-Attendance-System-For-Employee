import customtkinter as ctk
from View.dashboard_view import DashboardView
from View.attendance_view import AttendanceView
from View.enrollment_view import EnrollmentView
from View.register_view import RegisterView
from View.main_view import MainView
from View.login_view import LoginView
from View.attendance_camera_view import AttendanceCameraView
from View.admin_view import AdminView
from View.schedule_view import ScheduleView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_NAV_ITEMS = [
    ("dashboard",  "🏠  Dashboard"),
    ("attendance", "📷  Attendance"),
    ("enrollment", "🎯  Enrollment"),
    ("register",   "👥  Register"),
    ("schedule",   "🕐  Schedule"),
    ("admin",      "🔑  Admins"),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("1280x800")
        self.minsize(1024, 680)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top navigation bar (hidden until logged in) ───────────────────
        self._nav = ctk.CTkFrame(
            self,
            fg_color=("gray88", "#171A26"),
            corner_radius=0,
        )
        self._nav.grid_columnconfigure(1, weight=1)

        # App logo / title
        ctk.CTkLabel(
            self._nav,
            text="🎯  FaceAttend",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#4F8EF7", "#4F8EF7"),
        ).grid(row=0, column=0, padx=(20, 32), pady=10)

        # Nav buttons container
        self._nav_btn_frame = ctk.CTkFrame(self._nav, fg_color="transparent")
        self._nav_btn_frame.grid(row=0, column=1, sticky="w")

        self._nav_btns = {}
        for i, (screen, label) in enumerate(_NAV_ITEMS):
            btn = ctk.CTkButton(
                self._nav_btn_frame,
                text=label,
                width=130, height=34,
                fg_color="transparent",
                hover_color=("gray78", "#252839"),
                text_color=("gray25", "gray75"),
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                command=lambda s=screen: self._show_screen(s),
            )
            btn.grid(row=0, column=i, padx=3, pady=8)
            self._nav_btns[screen] = btn

        # Logout button (right side)
        ctk.CTkButton(
            self._nav,
            text="Logout",
            width=90, height=32,
            fg_color="transparent", border_width=1,
            border_color=("gray70", "gray40"),
            text_color=("gray30", "gray70"),
            hover_color=("gray82", "gray25"),
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda: self._show_screen("main"),
        ).grid(row=0, column=2, padx=(0, 16), sticky="e")

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(16, 20))
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Add main and login screens, and keep existing screens
        self._screens = {
            "main": MainView(self._content, on_proceed_login=lambda: self._show_screen("login"), on_start_attendance=lambda: self._show_screen("attendance_camera")),
            "login": LoginView(self._content, on_success=lambda: self._show_screen("dashboard")),
            "dashboard": DashboardView(self._content, on_go_register=lambda: self._show_screen("register")),
            "attendance": AttendanceView(self._content),
            "attendance_camera": AttendanceCameraView(self._content, on_back=lambda: self._show_screen("main")),
            "enrollment": EnrollmentView(self._content),
            "register": RegisterView(self._content),
            "admin": AdminView(self._content),
            "schedule": ScheduleView(self._content),
        }
        self._show_screen("main")

    def _show_screen(self, name):
        # Stop cameras on screens being hidden; skip the screen we're showing
        for screen_name, screen in self._screens.items():
            if screen_name == name:
                continue   # will be shown below — don't stop or hide it yet
            try:
                stop = getattr(screen, "_stop_camera", None)
                if callable(stop):
                    stop()
            except Exception:
                pass
            screen.grid_forget()

        self._screens[name].grid(row=0, column=0, sticky="nsew")

        # Highlight active nav button
        for s, btn in self._nav_btns.items():
            btn.configure(
                fg_color=("#4F8EF7", "#1a2a4a") if s == name else "transparent",
                text_color=("white", "white") if s == name else ("gray25", "gray75"),
                font=ctk.CTkFont(size=13, weight="bold" if s == name else "normal"),
            )

        if name in ("dashboard", "attendance", "enrollment", "register", "admin", "schedule"):
            self._show_nav()
        else:
            self._hide_nav()

    def _show_nav(self):
        if not self._nav.winfo_ismapped():
            self._nav.grid(row=0, column=0, sticky="ew")

    def _hide_nav(self):
        try:
            self._nav.grid_forget()
        except Exception:
            pass


if __name__ == "__main__":
    App().mainloop()