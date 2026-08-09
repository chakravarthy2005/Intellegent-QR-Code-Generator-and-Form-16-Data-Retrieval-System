"""
Reusable labeled form field components for CustomTkinter.
"""
import customtkinter as ctk
from ui.theme import (
    COLOR_SURFACE, COLOR_SURFACE_2, COLOR_BORDER, COLOR_PRIMARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_DANGER,
    FONT_BODY, FONT_SMALL, FONT_SUBHEADING, CORNER_RADIUS, INPUT_HEIGHT
)


class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, label: str, placeholder: str = "",
                 show: str = "", width: int = 300, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w", padx=2, pady=(0, 4))
        self._entry = ctk.CTkEntry(self, placeholder_text=placeholder, show=show, width=width, height=INPUT_HEIGHT, corner_radius=CORNER_RADIUS, border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT, font=FONT_BODY)
        self._entry.pack(fill="x")
        self._error_label = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=COLOR_DANGER, anchor="w")
        self._error_label.pack(anchor="w", padx=2)

    def get(self) -> str:
        return self._entry.get().strip()

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def set_error(self, msg: str):
        self._error_label.configure(text=msg)

    def clear_error(self):
        self._error_label.configure(text="")


class LabeledDropdown(ctk.CTkFrame):
    def __init__(self, master, label: str, values: list, width: int = 300, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w", padx=2, pady=(0, 4))
        self._combo = ctk.CTkComboBox(self, values=values, width=width, height=INPUT_HEIGHT, corner_radius=CORNER_RADIUS, border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_2, button_color=COLOR_PRIMARY, button_hover_color="#00B894", text_color=COLOR_TEXT, font=FONT_BODY)
        self._combo.pack(fill="x")

    def get(self) -> str:
        return self._combo.get()

    def set(self, value: str):
        self._combo.set(value)


class SectionHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        accent = ctk.CTkFrame(self, width=4, height=40, fg_color=COLOR_PRIMARY, corner_radius=2)
        accent.pack(side="left", padx=(0, 12), pady=4)
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(text_frame, text=title, font=FONT_SUBHEADING, text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(text_frame, text=subtitle, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")


class FormCard(ctk.CTkFrame):
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(master, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER, **kwargs)
        if title:
            ctk.CTkLabel(self, text=title, font=FONT_SUBHEADING, text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(16, 4))
            ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=20, pady=(0, 12))
