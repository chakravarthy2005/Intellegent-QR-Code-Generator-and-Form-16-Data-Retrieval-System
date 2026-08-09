import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_DANGER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, CORNER_RADIUS, BUTTON_HEIGHT
)
from ui.components.form_fields import LabeledEntry


class EmployeeLoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login: callable, on_register: callable, on_back: callable):
        super().__init__(master, fg_color=COLOR_BG)
        self.on_login = on_login
        self.on_register = on_register
        self.on_back = on_back
        self._build()

    def _build(self):
        ctk.CTkButton(self, text="\u2190 Back", font=FONT_SMALL, fg_color="transparent", hover_color=COLOR_SURFACE, text_color=COLOR_TEXT_MUTED, width=80, height=32, command=self.on_back).place(x=16, y=16)
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER, width=420)
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=40, fill="both")
        ctk.CTkLabel(inner, text="\U0001F464", font=("Segoe UI Emoji", 40)).pack(pady=(0, 8))
        ctk.CTkLabel(inner, text="Employee Login", font=FONT_HEADING, text_color=COLOR_TEXT).pack()
        ctk.CTkLabel(inner, text="Sign in to access your Form 16", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=(4, 24))
        self.email_field = LabeledEntry(inner, "Email Address", "you@company.com", width=340)
        self.email_field.pack(fill="x", pady=(0, 12))
        self.password_field = LabeledEntry(inner, "Password", "Enter password", show="*", width=340)
        self.password_field.pack(fill="x", pady=(0, 8))
        self.error_label = ctk.CTkLabel(inner, text="", font=FONT_SMALL, text_color=COLOR_DANGER, wraplength=340)
        self.error_label.pack(pady=(0, 8))
        self.login_btn = ctk.CTkButton(inner, text="Sign In", font=("Segoe UI", 14, "bold"), fg_color=COLOR_PRIMARY, hover_color="#00B894", text_color="#0D1117", height=BUTTON_HEIGHT, corner_radius=CORNER_RADIUS, command=self._do_login)
        self.login_btn.pack(fill="x", pady=(0, 8))

    def _do_login(self):
        email = self.email_field.get()
        password = self.password_field.get()
        if not email or not password:
            self.error_label.configure(text="Please fill in all fields.")
            return
        self.login_btn.configure(state="disabled", text="Signing in...")
        self.error_label.configure(text="")
        self.after(50, lambda: self._call_login(email, password))

    def _call_login(self, email, password):
        try:
            self.on_login(email, password)
        except Exception as e:
            # Only update UI if the widget still exists (login failed, page still visible)
            if self.winfo_exists():
                self.error_label.configure(text=str(e))
        finally:
            # Page may have been destroyed on successful login — guard before configuring
            try:
                if self.login_btn.winfo_exists():
                    self.login_btn.configure(state="normal", text="Sign In")
            except Exception:
                pass
