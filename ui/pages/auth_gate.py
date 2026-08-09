"""
Auth gate - Password prompt before decrypting Form 16 data.
"""
import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_SECONDARY, COLOR_DANGER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, CORNER_RADIUS, BUTTON_HEIGHT
)
from ui.components.form_fields import LabeledEntry


class AuthGatePage(ctk.CTkFrame):
    """
    Authorization gate shown after QR scan.
    Manager must re-enter their password to decrypt and view the Form 16.
    """

    def __init__(self, master, manager_username: str, hashed_eid: str,
                 on_authorized: callable, on_cancel: callable):
        super().__init__(master, fg_color=COLOR_BG)
        self.manager_username = manager_username
        self.hashed_eid = hashed_eid
        self.on_authorized = on_authorized
        self.on_cancel = on_cancel
        self._build()

    def _build(self):
        # Background subtle pattern overlay
        ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0).place(
            relx=0, rely=0, relwidth=1, relheight=1
        )

        # Center card
        card = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=20,
            border_width=2, border_color=COLOR_SECONDARY,
            width=480
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=44, fill="both")

        # Lock icon with glow effect
        icon_bg = ctk.CTkFrame(
            inner, width=80, height=80,
            fg_color=COLOR_SURFACE_2, corner_radius=20
        )
        icon_bg.pack(pady=(0, 20))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(
            icon_bg, text="🔑",
            font=("Segoe UI Emoji", 36)
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="Authorization Required",
            font=FONT_HEADING, text_color=COLOR_TEXT
        ).pack()

        ctk.CTkLabel(
            inner,
            text="QR code verified successfully.\n"
                 "Enter your manager password to decrypt and view the Form 16.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
            justify="center", wraplength=380
        ).pack(pady=(6, 24))

        # Manager info badge
        badge = ctk.CTkFrame(
            inner, fg_color=COLOR_SURFACE_2,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER
        )
        badge.pack(fill="x", pady=(0, 20))
        row = ctk.CTkFrame(badge, fg_color="transparent")
        row.pack(padx=16, pady=10)
        ctk.CTkLabel(row, text="Manager:", font=FONT_SMALL,
                     text_color=COLOR_TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(row, text=f"  {self.manager_username}",
                     font=(FONT_SMALL[0], 12, "bold"),
                     text_color=COLOR_TEXT).pack(side="left")

        # Password field
        self.password_field = LabeledEntry(
            inner, "Master Password", "Enter decryption password",
            show="*", width=390
        )
        self.password_field.pack(fill="x", pady=(0, 8))

        # Error display
        self.error_label = ctk.CTkLabel(
            inner, text="", font=FONT_SMALL,
            text_color=COLOR_DANGER, wraplength=390
        )
        self.error_label.pack(pady=(0, 16))

        # Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row, text="Cancel",
            font=FONT_BODY,
            fg_color="transparent",
            hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            height=BUTTON_HEIGHT, corner_radius=CORNER_RADIUS,
            command=self.on_cancel
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._auth_btn = ctk.CTkButton(
            btn_row, text="🔓  Decrypt & View",
            font=(FONT_BODY[0], 14, "bold"),
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            text_color="#FFFFFF",
            height=BUTTON_HEIGHT, corner_radius=CORNER_RADIUS,
            command=self._do_auth
        )
        self._auth_btn.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # Warning
        warn = ctk.CTkFrame(
            inner, fg_color=COLOR_SURFACE_2, corner_radius=8,
            border_width=1, border_color=COLOR_DANGER
        )
        warn.pack(fill="x", pady=(20, 0))
        ctk.CTkLabel(
            warn,
            text="⚠️  Access is logged. Unauthorized access attempts are monitored.",
            font=FONT_SMALL, text_color="#F85149",
            wraplength=380, justify="left"
        ).pack(padx=12, pady=8)

        # Bind Enter key
        self.password_field._entry.bind("<Return>", lambda e: self._do_auth())
        self.after(100, lambda: self.password_field._entry.focus_set())

    def _do_auth(self):
        password = self.password_field.get()
        if not password:
            self.error_label.configure(text="Password is required.")
            return
        self._auth_btn.configure(state="disabled", text="Decrypting...")
        self.error_label.configure(text="")
        self.after(50, lambda: self._call_auth(password))

    def _call_auth(self, password: str):
        try:
            self.on_authorized(password, self.hashed_eid)
        except Exception as e:
            self.error_label.configure(text=str(e))
            self._auth_btn.configure(state="normal", text="🔓  Decrypt & View")
