"""
Landing page - role selection.
"""
import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, CORNER_RADIUS
)


class LandingPage(ctk.CTkFrame):
    def __init__(self, master, on_employee: callable, on_manager: callable):
        super().__init__(master, fg_color=COLOR_BG)
        self.on_employee = on_employee
        self.on_manager = on_manager
        self._build()

    def _build(self):
        left = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0, width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        stripe = ctk.CTkFrame(left, width=4, fg_color=COLOR_PRIMARY, corner_radius=0)
        stripe.place(relx=0, rely=0, relwidth=0.012, relheight=1)

        hero_inner = ctk.CTkFrame(left, fg_color="transparent")
        hero_inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(hero_inner, text="\U0001F510", font=("Segoe UI Emoji", 64)).pack(pady=(0, 16))
        ctk.CTkLabel(hero_inner, text="Form 16", font=FONT_TITLE, text_color=COLOR_PRIMARY).pack()
        ctk.CTkLabel(hero_inner, text="QR SCANNER", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(pady=(0, 8))
        ctk.CTkFrame(hero_inner, width=200, height=1, fg_color=COLOR_BORDER).pack(pady=12)

        features = [
            ("\U0001F512", "Triple AES-256 Encryption"),
            ("\U0001F511", "SHA-512 Employee ID Hashing"),
            ("\U0001F4F7", "Exclusive In-App QR Scanner"),
            ("\u2601", "Supabase Cloud Storage"),
        ]
        for icon, text in features:
            row = ctk.CTkFrame(hero_inner, fg_color="transparent")
            row.pack(anchor="w", pady=4)
            ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=text, font=("Segoe UI", 12), text_color=COLOR_TEXT_MUTED).pack(side="left")

        right = ctk.CTkFrame(self, fg_color=COLOR_BG)
        right.pack(side="right", fill="both", expand=True)

        content = ctk.CTkFrame(right, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text="Welcome Back", font=FONT_HEADING, text_color=COLOR_TEXT).pack(pady=(0, 4))
        ctk.CTkLabel(content, text="Select your role to continue", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=(0, 40))

        emp_card = self._role_card(content, icon="\U0001F464", title="Employee Portal", desc="Register, view your Form 16\nand manage your QR code", color=COLOR_PRIMARY, command=self.on_employee)
        emp_card.pack(pady=(0, 20), fill="x", padx=20)

        mgr_card = self._role_card(content, icon="\U0001F6E1", title="Manager Portal", desc="Scan QR codes and retrieve\nForm 16 with authorization", color=COLOR_SECONDARY, command=self.on_manager)
        mgr_card.pack(fill="x", padx=20)

        ctk.CTkLabel(content, text="v1.0.0  Secured with AES-256", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=(32, 0))

    def _role_card(self, master, icon, title, desc, color, command):
        card = ctk.CTkFrame(master, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER, cursor="hand2")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")
        icon_bg = ctk.CTkFrame(left, width=52, height=52, fg_color=COLOR_SURFACE_2, corner_radius=10)
        icon_bg.pack()
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon, font=("Segoe UI Emoji", 24)).place(relx=0.5, rely=0.5, anchor="center")
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        ctk.CTkLabel(right, text=title, font=("Segoe UI", 15, "bold"), text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(right, text=desc, font=("Segoe UI", 11), text_color=COLOR_TEXT_MUTED, anchor="w", justify="left").pack(anchor="w", pady=(4, 0))
        arrow = ctk.CTkLabel(inner, text="\u2192", font=("Segoe UI", 20, "bold"), text_color=color)
        arrow.pack(side="right")

        def on_enter(e):
            card.configure(border_color=color)
        def on_leave(e):
            card.configure(border_color=COLOR_BORDER)
        def on_click(e):
            command()

        for widget in [card, inner, left, right, arrow, icon_bg]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
        return card
