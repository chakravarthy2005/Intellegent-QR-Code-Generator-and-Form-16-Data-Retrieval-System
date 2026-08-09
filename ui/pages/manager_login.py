import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_SECONDARY, COLOR_DANGER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, CORNER_RADIUS, BUTTON_HEIGHT
)
from ui.components.form_fields import LabeledEntry


class ManagerLoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login: callable, on_back: callable, on_first_run_setup: callable, is_first_run: bool = False):
        super().__init__(master, fg_color=COLOR_BG)
        self.on_login = on_login
        self.on_back = on_back
        self.on_first_run_setup = on_first_run_setup
        self.is_first_run = is_first_run
        self._build()

    def _build(self):
        if self.on_back:
            ctk.CTkButton(self, text="\u2190 Back", font=FONT_SMALL, fg_color="transparent", hover_color=COLOR_SURFACE, text_color=COLOR_TEXT_MUTED, width=80, height=32, command=self.on_back).place(x=16, y=16)
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER, width=460)
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=40, fill="both")
        ctk.CTkLabel(inner, text="\U0001F6E1", font=("Segoe UI Emoji", 40)).pack(pady=(0, 8))
        ctk.CTkLabel(
            inner,
            text="Manager Portal",
            font=FONT_HEADING,
            text_color=COLOR_TEXT
        ).pack(pady=(0,10))

        self.mode = ctk.StringVar(value="Create Account" if self.is_first_run else "Sign In")

        self.segment = ctk.CTkSegmentedButton(
            inner,
            values=["Create Account", "Sign In"],
            variable=self.mode,
            command=self.switch_mode,
            height=36,
            corner_radius=10,
            fg_color=COLOR_SURFACE_2,
            selected_color=COLOR_SECONDARY,
            selected_hover_color=COLOR_SECONDARY,
        )
        self.segment.pack(fill="x", pady=(10, 16))

        self.form_title = ctk.CTkLabel(inner, text="", font=FONT_HEADING, text_color=COLOR_TEXT)
        self.form_title.pack(anchor="w", pady=(0, 10))

        self.form_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True)

        self._render_form()

    def _render_form(self):
        current_mode = self.mode.get()
        if current_mode == "Create Account":
            self.build_register()
        else:
            self.build_login()

    def switch_mode(self, value):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        if value == "Create Account":
            self.build_register()
        else:
            self.build_login()

    def build_login(self):
        self.form_title.configure(text="Sign In")

        self.username_field = LabeledEntry(self.form_frame, "Username", "Enter username", width=340)
        self.username_field.pack(fill="x", pady=(0, 10))

        self.password_field = LabeledEntry(self.form_frame, "Password", "Enter password", show="*", width=340)
        self.password_field.pack(fill="x", pady=(0, 10))

        self.error_label = ctk.CTkLabel(self.form_frame, text="", font=FONT_SMALL, text_color=COLOR_DANGER, anchor="w")
        self.error_label.pack(anchor="w", pady=(4, 10))

        self.action_btn = ctk.CTkButton(
            self.form_frame,
            text="Sign In",
            command=self._do_login,
            height=BUTTON_HEIGHT,
            corner_radius=CORNER_RADIUS,
        )
        self.action_btn.pack(fill="x", pady=(6, 0))

    def build_register(self):
        self.form_title.configure(text="Create Account")

        self.username_field = LabeledEntry(self.form_frame, "Username", "Choose username", width=340)
        self.username_field.pack(fill="x", pady=(0, 3))

        self.display_name_field = LabeledEntry(self.form_frame, "Display Name", "Your name", width=340)
        self.display_name_field.pack(fill="x", pady=(0,3))

        self.password_field = LabeledEntry(self.form_frame, "Password", "Minimum 8 characters", show="*", width=340)
        self.password_field.pack(fill="x", pady=(0, 3))

        self.confirm_field = LabeledEntry(self.form_frame, "Confirm Password", "Re-enter password", show="*", width=340)
        self.confirm_field.pack(fill="x", pady=(0, 3))

        self.error_label = ctk.CTkLabel(self.form_frame, text="", font=FONT_SMALL, text_color=COLOR_DANGER, anchor="w")
        self.error_label.pack(anchor="w", pady=(4, 3))

        button_text = "Initialize & Continue" if self.is_first_run else "Create Account"
        self.action_btn = ctk.CTkButton(
            self.form_frame,
            text=button_text,
            command=self._do_first_run if self.is_first_run else self._do_register,
            height=BUTTON_HEIGHT,
            corner_radius=CORNER_RADIUS,
        )
        self.action_btn.pack(fill="x", pady=(1, 0))

    def _do_register(self):
        username = self.username_field.get()
        display_name = self.display_name_field.get()
        password = self.password_field.get()
        confirm = self.confirm_field.get()
        if not username or not password:
            self.error_label.configure(text="Username and password are required.")
            return
        if len(password) < 8:
            self.error_label.configure(text="Password must be at least 8 characters.")
            return
        if password != confirm:
            self.error_label.configure(text="Passwords do not match.")
            return
        self.action_btn.configure(state="disabled", text="Creating account...")
        self.error_label.configure(text="")
        self.after(50, lambda: self._call_first_run(username, display_name, password))

    def _do_first_run(self):
        username = self.username_field.get()
        display_name = self.display_name_field.get()
        password = self.password_field.get()
        confirm = self.confirm_field.get()
        if not username or not password:
            self.error_label.configure(text="Username and password are required.")
            return
        if len(password) < 8:
            self.error_label.configure(text="Password must be at least 8 characters.")
            return
        if password != confirm:
            self.error_label.configure(text="Passwords do not match.")
            return
        self.action_btn.configure(state="disabled", text="Initializing...")
        self.error_label.configure(text="")
        self.after(50, lambda: self._call_first_run(username, display_name, password))

    def _call_first_run(self, username, display_name, password):
        try:
            self.on_first_run_setup(username, display_name, password)
        except Exception as e:
            self.error_label.configure(text=str(e))
            self.action_btn.configure(state="normal", text="Initialize & Continue")

    def _do_login(self):
        username = self.username_field.get()
        password = self.password_field.get()
        if not username or not password:
            self.error_label.configure(text="Please fill in all fields.")
            return
        self.action_btn.configure(state="disabled", text="Signing in...")
        self.error_label.configure(text="")
        self.after(50, lambda: self._call_login(username, password))

    def _call_login(self, username, password):
        try:
            self.on_login(username, password)
        except Exception as e:
            self.error_label.configure(text=str(e))
            self.action_btn.configure(state="normal", text="Sign In")
