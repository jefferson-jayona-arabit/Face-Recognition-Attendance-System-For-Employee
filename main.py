import customtkinter as ctk
from ui.enrollment_screen import EnrollmentScreen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        screen = EnrollmentScreen(self)
        screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)


if __name__ == "__main__":
    App().mainloop()