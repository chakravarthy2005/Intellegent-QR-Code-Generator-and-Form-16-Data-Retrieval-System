import customtkinter as ctk
from ui.theme import COLOR_PRIMARY, COLOR_SURFACE, COLOR_TEXT, FONT_BODY


class LoadingSpinner(ctk.CTkToplevel):
    def __init__(self, master, message: str = "Loading..."):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLOR_SURFACE)
        self._angle = 0
        self._running = False
        self.update_idletasks()
        px = master.winfo_rootx() + master.winfo_width() // 2 - 120
        py = master.winfo_rooty() + master.winfo_height() // 2 - 70
        self.geometry(f"240x140+{px}+{py}")
        self._canvas = ctk.CTkCanvas(self, width=50, height=50, bg=COLOR_SURFACE, highlightthickness=0)
        self._canvas.pack(pady=(20, 8))
        self._draw_arc()
        ctk.CTkLabel(self, text=message, font=FONT_BODY, text_color=COLOR_TEXT).pack()

    def _draw_arc(self):
        self._canvas.delete("all")
        self._canvas.create_arc(5, 5, 45, 45, start=self._angle, extent=280, outline=COLOR_PRIMARY, width=4, style="arc")

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        self.destroy()

    def _animate(self):
        if not self._running:
            return
        self._angle = (self._angle + 10) % 360
        self._draw_arc()
        self.after(30, self._animate)
