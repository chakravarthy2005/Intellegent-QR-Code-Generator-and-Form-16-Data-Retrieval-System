"""
OpenCV-based in-app QR scanner page for managers.
Live webcam feed with QR detection and HMAC verification.
"""
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_SUBHEADING, FONT_MONO, CORNER_RADIUS
)


class ScannerPage(ctk.CTkFrame):
    """
    Live webcam QR scanner page.
    Integrates with QRScannerService and verifies HMAC signatures.
    """

    def __init__(self, master, on_qr_verified: callable, on_back: callable,
                 app_secret: bytes, manager_username: str = ""):
        super().__init__(master, fg_color=COLOR_BG)
        self.on_qr_verified = on_qr_verified
        self.on_back = on_back
        self.app_secret = app_secret
        self.manager_username = manager_username
        self._scanner = None
        self._scanning = False
        self._scan_paused = False
        self._last_status = ""
        self._build()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=60, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", font=FONT_SMALL,
            fg_color="transparent", hover_color=COLOR_SURFACE_2,
            text_color=COLOR_TEXT_MUTED, width=80, height=32,
            command=self._on_back
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkLabel(
            top, text="🔍  QR Code Scanner",
            font=(FONT_BODY[0], 14, "bold"), text_color=COLOR_PRIMARY
        ).pack(side="left", padx=8, pady=14)

        # Status dot
        self._status_dot = ctk.CTkLabel(
            top, text="⚫  Camera Off",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self._status_dot.pack(side="right", padx=20, pady=20)

        # Main layout
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # ---- Left: camera feed -------------------------------------------
        left = ctk.CTkFrame(main, fg_color=COLOR_SURFACE, corner_radius=0)
        left.pack(side="left", fill="both", expand=True)

        cam_frame = ctk.CTkFrame(left, fg_color="transparent")
        cam_frame.pack(fill="both", expand=True, padx=24, pady=24)

        # Camera viewport
        self._cam_label = ctk.CTkLabel(
            cam_frame, text="",
            width=640, height=480,
            fg_color="#000000",
            corner_radius=12
        )
        self._cam_label.pack()

        # Overlay placeholder text
        self._cam_placeholder = ctk.CTkLabel(
            self._cam_label,
            text="📷\n\nCamera not started\n\nClick 'Start Scanner' to begin",
            font=(FONT_BODY[0], 14, "normal"),
            text_color=COLOR_TEXT_MUTED,
            justify="center"
        )
        self._cam_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # Scanner controls
        ctrl_row = ctk.CTkFrame(left, fg_color="transparent")
        ctrl_row.pack(pady=(0, 16))

        self._start_btn = ctk.CTkButton(
            ctrl_row, text="▶  Start Scanner",
            font=(FONT_BODY[0], 14, "bold"),
            fg_color=COLOR_SUCCESS, hover_color="#2EA043",
            text_color="#0D1117",
            height=44, width=180, corner_radius=CORNER_RADIUS,
            command=self._start_scanner
        )
        self._start_btn.pack(side="left", padx=8)

        self._stop_btn = ctk.CTkButton(
            ctrl_row, text="⏹  Stop",
            font=FONT_BODY,
            fg_color="transparent", hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            height=44, width=120, corner_radius=CORNER_RADIUS,
            command=self._stop_scanner,
            state="disabled"
        )
        self._stop_btn.pack(side="left", padx=8)

        # ---- Right: info panel -------------------------------------------
        right = ctk.CTkFrame(main, fg_color=COLOR_BG, width=340)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        right_inner = ctk.CTkScrollableFrame(
            right, fg_color="transparent",
            scrollbar_button_color=COLOR_BORDER
        )
        right_inner.pack(fill="both", expand=True, padx=16, pady=16)

        # Scan status card
        self._status_card = ctk.CTkFrame(
            right_inner, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        self._status_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            self._status_card, text="Scan Status",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT, anchor="w"
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkFrame(self._status_card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        self._scan_status_label = ctk.CTkLabel(
            self._status_card,
            text="Waiting for scan...",
            font=FONT_BODY, text_color=COLOR_TEXT_MUTED,
            wraplength=290, justify="left"
        )
        self._scan_status_label.pack(anchor="w", padx=16, pady=12)

        self._result_frame = ctk.CTkFrame(
            self._status_card, fg_color="transparent"
        )
        self._result_frame.pack(fill="x", padx=16, pady=(0, 16))

        # Instructions card
        inst_card = ctk.CTkFrame(
            right_inner, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        inst_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            inst_card, text="How to Scan",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT, anchor="w"
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkFrame(inst_card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        steps = [
            ("1", "Click 'Start Scanner'"),
            ("2", "Hold QR code in front of camera"),
            ("3", "Keep QR inside the green guide box"),
            ("4", "Enter authorization password"),
            ("5", "View decrypted Form 16"),
        ]
        for num, step in steps:
            row = ctk.CTkFrame(inst_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(
                row, text=num,
                font=(FONT_SMALL[0], 11, "bold"),
                fg_color=COLOR_PRIMARY, text_color="#0D1117",
                width=22, height=22, corner_radius=11
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(
                row, text=step, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w"
            ).pack(side="left")
        ctk.CTkFrame(inst_card, height=10, fg_color="transparent").pack()

        # Security badge
        sec_card = ctk.CTkFrame(
            right_inner, fg_color=COLOR_SURFACE_2,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        sec_card.pack(fill="x")
        ctk.CTkLabel(
            sec_card,
            text="🔒  App-Exclusive Scanner\n\n"
                 "QR codes from this system contain HMAC-SHA512 "
                 "cryptographic signatures. Only this app can verify "
                 "and decode them. Generic QR scanners will see only "
                 "an opaque encoded payload.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
            wraplength=290, justify="left"
        ).pack(padx=14, pady=14)

    # ---- Scanner Control ----------------------------------------------------

    def _start_scanner(self):
        from services.scanner_service import QRScannerService
        self._scanner = QRScannerService(
            on_detected=self._on_qr_detected,
            camera_index=0
        )
        ok = self._scanner.start()
        if not ok:
            self._set_status("❌  No camera found. Check connection.", COLOR_DANGER)
            return

        self._scanning = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_dot.configure(text="🟢  Camera Active", text_color=COLOR_SUCCESS)
        self._cam_placeholder.place_forget()
        self._set_status("📸  Scanning... Point QR code at camera.", COLOR_PRIMARY)
        self._update_feed()

    def _stop_scanner(self):
        self._scanning = False
        if self._scanner:
            self._scanner.stop()
            self._scanner = None
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._status_dot.configure(text="⚫  Camera Off", text_color=COLOR_TEXT_MUTED)
        self._cam_label.configure(image=None)
        self._cam_placeholder.place(relx=0.5, rely=0.5, anchor="center")
        self._set_status("Scanner stopped.", COLOR_TEXT_MUTED)

    def _update_feed(self):
        if not self._scanning:
            return
        if self._scanner:
            frame = self._scanner.get_frame()
            if frame is not None:
                try:
                    pil_img = Image.fromarray(frame)
                    ctk_img = ctk.CTkImage(
                        light_image=pil_img,
                        dark_image=pil_img,
                        size=(640, 480)
                    )
                    self._cam_label.configure(image=ctk_img)
                    self._cam_label.image = ctk_img
                except Exception:
                    pass
        self.after(33, self._update_feed)  # ~30 FPS

    def _on_qr_detected(self, qr_data: str):
        if self._scan_paused:
            return
        # Verify HMAC signature
        from security.qr_signer import verify_qr_payload
        hashed_eid = verify_qr_payload(qr_data, self.app_secret, manager_username=self.manager_username)
        if hashed_eid is None:
            self._set_status(
                "⚠️  Invalid QR code. Not from this system.\n"
                "Signature verification failed.",
                COLOR_DANGER
            )
            return
        # Valid — pause scanning, notify controller
        self._scan_paused = True
        self._set_status(
            "✅  Valid QR Code detected!\n"
            "Employee ID verified.\nPreparing authorization...",
            COLOR_SUCCESS
        )
        self._status_dot.configure(text="✅  QR Detected", text_color=COLOR_SUCCESS)
        # Call on main thread
        self.after(500, lambda: self._verified(hashed_eid))

    def _verified(self, hashed_eid: str):
        self._stop_scanner()
        self.on_qr_verified(hashed_eid)

    def _on_back(self):
        self._stop_scanner()
        self.on_back()

    # ---- Helpers ------------------------------------------------------------

    def _set_status(self, msg: str, color: str = None):
        kwargs = {"text": msg}
        if color:
            kwargs["text_color"] = color
        try:
            self._scan_status_label.configure(**kwargs)
        except Exception:
            pass

    def reset(self):
        """Reset scanner state when returning to this page."""
        self._scan_paused = False
        self._set_status("Waiting for scan...", COLOR_TEXT_MUTED)
        self._status_dot.configure(text="⚫  Camera Off", text_color=COLOR_TEXT_MUTED)
