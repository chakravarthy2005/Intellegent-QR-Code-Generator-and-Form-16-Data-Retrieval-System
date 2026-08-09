"""
QR code display widget.
"""
import customtkinter as ctk
from PIL import Image
from ui.theme import COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_PRIMARY, FONT_BODY, FONT_SMALL, CORNER_RADIUS


class QRDisplay(ctk.CTkFrame):
    def __init__(self, master, size: int = 260, **kwargs):
        super().__init__(master, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER, **kwargs)
        self._size = size
        self._pil_image = None
        self._canvas_label = ctk.CTkLabel(self, text="", width=size, height=size)
        self._canvas_label.pack(padx=24, pady=(24, 8))
        self._info_label = ctk.CTkLabel(self, text="QR Code will appear here", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED)
        self._info_label.pack(pady=(0, 8))
        self._save_btn = ctk.CTkButton(self, text="⬇ Save QR Code", font=FONT_BODY, fg_color=COLOR_PRIMARY, hover_color="#00B894", text_color="#0D1117", height=36, corner_radius=CORNER_RADIUS, command=self._save_qr, state="disabled")
        self._save_btn.pack(pady=(0, 20), padx=24, fill="x")

    def set_image(self, pil_img: Image.Image):
        self._pil_image = pil_img.resize((self._size, self._size), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=self._pil_image, dark_image=self._pil_image, size=(self._size, self._size))
        self._canvas_label.configure(image=ctk_img, text="")
        self._canvas_label.image = ctk_img
        self._info_label.configure(text="Scan with Form16 Scanner app only")
        self._save_btn.configure(state="normal")

    def _save_qr(self):
        if not self._pil_image:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")], initialfile="form16_qr.png")
        if path:
            self._pil_image.save(path)
