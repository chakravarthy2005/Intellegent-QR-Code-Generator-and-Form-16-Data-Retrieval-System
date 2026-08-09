"""
Employee dashboard - shows QR code and Form 16 summary.
"""
import customtkinter as ctk
from PIL import Image
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_SUBHEADING, FONT_MONO, CORNER_RADIUS
)
from ui.components.qr_display import QRDisplay


class EmployeeDashboard(ctk.CTkFrame):
    """Dashboard shown after employee login with QR and Form 16 overview."""

    def __init__(self, master, employee_data: dict, on_logout: callable,
                 on_view_form16: callable = None):
        super().__init__(master, fg_color=COLOR_BG)
        self.employee_data = employee_data  # Raw DB row (encrypted)
        self.on_logout = on_logout
        self.on_view_form16 = on_view_form16
        self._qr_image: Image.Image | None = None
        self._build()

    def set_qr_image(self, pil_img: Image.Image):
        """Called externally to display the QR code."""
        self._qr_image = pil_img
        self._qr_widget.set_image(pil_img)

    def _build(self):
        # ---- Top navbar -------------------------------------------------
        nav = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=60, corner_radius=0)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        # Logo
        ctk.CTkLabel(
            nav, text="  🔐 Form16 Scanner",
            font=(FONT_BODY[0], 14, "bold"),
            text_color=COLOR_PRIMARY
        ).pack(side="left", padx=20, pady=18)

        # Right side controls
        right_nav = ctk.CTkFrame(nav, fg_color="transparent")
        right_nav.pack(side="right", padx=20, pady=10)

        ctk.CTkLabel(
            right_nav, text="👤  Employee Portal",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            right_nav, text="Logout",
            font=FONT_SMALL,
            fg_color="transparent",
            hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            height=32, width=80, corner_radius=CORNER_RADIUS,
            command=self.on_logout
        ).pack(side="left")

        # ---- Main content -----------------------------------------------
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # Left: QR + info
        left_panel = ctk.CTkFrame(main, fg_color=COLOR_SURFACE, width=340, corner_radius=0)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        left_inner = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_inner.pack(fill="both", expand=True, padx=20, pady=20)

        # Employee badge
        badge = ctk.CTkFrame(
            left_inner, fg_color=COLOR_SURFACE_2,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        badge.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            badge, text="👤",
            font=("Segoe UI Emoji", 32)
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            badge, text="Employee Account",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT
        ).pack()

        emp_id_short = str(self.employee_data.get("employee_id", ""))[:8] + "..."
        ctk.CTkLabel(
            badge, text=f"ID: {emp_id_short}",
            font=FONT_MONO, text_color=COLOR_TEXT_MUTED
        ).pack(pady=(2, 16))

        # Status indicators
        status_frame = ctk.CTkFrame(left_inner, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 16))

        self._status_items = {}
        statuses = [
            ("form16", "Form 16", "⏳ Generating..."),
            ("qr", "QR Code", "⏳ Loading..."),
            ("encryption", "Encryption", "✅ AES-256 Active"),
        ]
        for key, label, value in statuses:
            row = ctk.CTkFrame(status_frame, fg_color=COLOR_SURFACE_2, corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
                         anchor="w").pack(side="left", padx=12, pady=8)
            val_lbl = ctk.CTkLabel(row, text=value, font=FONT_SMALL,
                                   text_color=COLOR_SUCCESS, anchor="e")
            val_lbl.pack(side="right", padx=12, pady=8)
            self._status_items[key] = val_lbl

        # QR Display
        self._qr_widget = QRDisplay(left_inner, size=240)
        self._qr_widget.pack(fill="x", pady=(0, 12))

        # Security info
        sec_box = ctk.CTkFrame(
            left_inner, fg_color=COLOR_SURFACE_2,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER
        )
        sec_box.pack(fill="x")
        ctk.CTkLabel(
            sec_box,
            text="🔒 This QR code can only be\nscanned by the Form16 Scanner app.\nGeneric QR scanners cannot decode it.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
            justify="left"
        ).pack(padx=12, pady=10)

        # Right panel: Form 16 summary
        right_panel = ctk.CTkScrollableFrame(
            main, fg_color=COLOR_BG,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_PRIMARY
        )
        right_panel.pack(side="right", fill="both", expand=True)

        # Welcome header
        header = ctk.CTkFrame(right_panel, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 20))
        ctk.CTkLabel(header, text="Your Form 16 Summary",
                     font=FONT_HEADING, text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(header, text="All data is stored encrypted in the cloud",
                     font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        # Info banner
        banner = ctk.CTkFrame(
            right_panel, fg_color=COLOR_SURFACE_2,
            corner_radius=10, border_width=1, border_color=COLOR_BORDER
        )
        banner.pack(fill="x", padx=32, pady=(0, 20))
        ctk.CTkLabel(
            banner,
            text="ℹ️  Your Form 16 data is stored with triple AES-256-GCM encryption. "
                 "Only authorized managers with the master key can view full details.",
            font=FONT_SMALL, text_color=COLOR_TEXT, wraplength=600, justify="left"
        ).pack(padx=16, pady=12)

        # Summary cards grid
        self._summary_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        self._summary_frame.pack(fill="x", padx=32, pady=(0, 24))
        self._build_summary_cards()

    def _build_summary_cards(self):
        cards_data = [
            ("📋", "Form 16 Status", "Registered", COLOR_SUCCESS),
            ("💰", "Gross Salary", "Encrypted", COLOR_PRIMARY),
            ("🏦", "Tax Payable", "Encrypted", COLOR_WARNING),
            ("📊", "TDS Records", "Q1 - Q4", COLOR_SECONDARY),
        ]
        for i, (icon, title, value, color) in enumerate(cards_data):
            row = i // 2
            col = i % 2

            card = ctk.CTkFrame(
                self._summary_frame,
                fg_color=COLOR_SURFACE,
                corner_radius=12,
                border_width=1,
                border_color=COLOR_BORDER
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self._summary_frame.grid_columnconfigure(col, weight=1)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=20, pady=16, fill="both", expand=True)

            icon_frame = ctk.CTkFrame(
                inner, width=44, height=44,
                fg_color=COLOR_SURFACE_2, corner_radius=8
            )
            icon_frame.pack(anchor="w")
            icon_frame.pack_propagate(False)
            ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 20)
                         ).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(inner, text=title, font=FONT_SMALL,
                         text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w", pady=(10, 2))
            ctk.CTkLabel(inner, text=value, font=FONT_SUBHEADING,
                         text_color=COLOR_TEXT, anchor="w").pack(anchor="w")

    def update_status(self, key: str, text: str, color: str = None):
        if key in self._status_items:
            kwargs = {"text": text}
            if color:
                kwargs["text_color"] = color
            self._status_items[key].configure(**kwargs)
