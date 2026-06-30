import customtkinter as ctk
from View.dashboard_view import DashboardView
from View.attendance_view import AttendanceView
from View.enrollment_view import EnrollmentView
from View.register_view import RegisterView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("1200x760")
        self.minsize(1000, 650)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        nav.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkButton(nav, text="Dashboard", command=lambda: self._show_screen("dashboard")).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(nav, text="Attendance", command=lambda: self._show_screen("attendance")).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(nav, text="Enrollment", command=lambda: self._show_screen("enrollment")).grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkButton(nav, text="Register", command=lambda: self._show_screen("register")).grid(row=0, column=3, padx=4, sticky="ew")

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._screens = {
            "dashboard": DashboardView(self._content, on_go_register=lambda: self._show_screen("register")),
            "attendance": AttendanceView(self._content),
            "enrollment": EnrollmentView(self._content),
            "register": RegisterView(self._content),
        }
        self._show_screen("dashboard")

    def _show_screen(self, name):
        for screen_name, screen in self._screens.items():
            screen.grid_forget()
        self._screens[name].grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    App().mainloop()