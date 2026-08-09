"""
Manager Dashboard — main hub after login.
Contains: Connection Panel (USB/WiFi/Bluetooth), CSV Import, and Scan History.
"""
import customtkinter as ctk
from ui.pages.authorized_scanners_page import AuthorizedScannersPage
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, COLOR_INFO,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_SUBHEADING, FONT_MONO, CORNER_RADIUS
)


class ManagerDashboard(ctk.CTkFrame):
    """Manager home screen: connection panel, CSV import, scan history."""

    def __init__(self, master, manager_data: dict, local_ip: str,
                 on_logout: callable, on_import_csv: callable = None,
                 on_connection_mode_changed: callable = None,
                 on_manage_scanners: callable = None,
                 scan_history: list = None):
        super().__init__(master, fg_color=COLOR_BG)
        self.manager_data = manager_data
        self.is_admin = (self.manager_data.get("role", "scanner") == "admin")
        username = self.manager_data.get("username", "")
        from security.authorized_scanners import can_user_upload
        self.can_upload = can_user_upload(username, self.is_admin)

        self.local_ip = local_ip
        self.on_logout = on_logout
        self.on_import_csv = on_import_csv
        self.on_connection_mode_changed = on_connection_mode_changed
        self.on_manage_scanners = on_manage_scanners
        self._scan_history = list(scan_history) if scan_history else []
        self._current_conn_mode = "usb"
        self._build()
        self._refresh_history()

    def _show_authorized_scanners_page(self):
        if not self.is_admin:
            self.show_scan_error("Access Denied: Only Admin can manage authorized scanners.")
            return
        self._clear_page_content()
        page = AuthorizedScannersPage(self, on_back=self._show_dashboard_content)
        page.pack(fill="both", expand=True)

    def _show_dashboard_content(self):
        self._clear_page_content()
        self._build_dashboard_content()

    def _clear_page_content(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _build_dashboard_content(self):
        # ── Top navbar ─────────────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=64, corner_radius=0)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkLabel(
            nav, text="⚡  Form 16 Manager Portal",
            font=(FONT_HEADING[0], 16, "bold"), text_color=COLOR_PRIMARY
        ).pack(side="left", padx=24, pady=20)

        name = self.manager_data.get("display_name") or self.manager_data.get("username", "Manager")
        role_label = "👑 Admin" if self.is_admin else "🔍 Scanner"
        ctk.CTkLabel(
            nav, text=f"👤  {name}  ({role_label})",
            font=FONT_BODY, text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            nav, text="Logout", font=FONT_SMALL,
            fg_color="transparent", hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED, height=32, width=80,
            command=self.on_logout
        ).pack(side="right", padx=24, pady=16)

        # Global connection dot
        self._conn_status_dot = ctk.CTkLabel(
            nav, text="⚫  No phone connected",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self._conn_status_dot.pack(side="right", padx=8)

        # ── Main split layout ──────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # ── LEFT PANEL ─────────────────────────────────────────────────────────
        left = ctk.CTkScrollableFrame(
            main, fg_color=COLOR_BG, width=380,
            scrollbar_button_color=COLOR_BORDER
        )
        left.pack(side="left", fill="y", padx=(0, 1))

        left_inner = ctk.CTkFrame(left, fg_color="transparent")
        left_inner.pack(fill="x", padx=16, pady=16)

        # ── Connection Panel ───────────────────────────────────────────────────
        conn_card = ctk.CTkFrame(
            left_inner, fg_color=COLOR_SURFACE,
            corner_radius=16, border_width=1, border_color=COLOR_BORDER
        )
        conn_card.pack(fill="x", pady=(0, 16))

        conn_hdr = ctk.CTkFrame(conn_card, fg_color="transparent")
        conn_hdr.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            conn_hdr, text="📡  Connection Mode",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT, anchor="w"
        ).pack(side="left")
        ctk.CTkFrame(conn_card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=20)

        # Tab selector
        self._conn_tabs = ctk.CTkSegmentedButton(
            conn_card,
            values=["🔌 USB", "📶 WiFi"],
            command=self._on_conn_tab_changed,
            font=(FONT_SMALL[0], 12, "bold"),
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY,
            unselected_color=COLOR_SURFACE_2,
            unselected_hover_color=COLOR_SURFACE_2,
            text_color="#0D1117",
            text_color_disabled=COLOR_TEXT_MUTED,
        )
        self._conn_tabs.pack(fill="x", padx=20, pady=12)
        self._conn_tabs.set("🔌 USB")

        # Tab content frame (swapped when tab changes)
        self._conn_content = ctk.CTkFrame(conn_card, fg_color="transparent")
        self._conn_content.pack(fill="x", padx=20, pady=(0, 16))

        self._build_usb_tab()   # start with USB

        # ── CSV Import Card ────────────────────────────────────────────────────
        import_card = ctk.CTkFrame(
            left_inner, fg_color=COLOR_SURFACE,
            corner_radius=16, border_width=1, border_color=COLOR_BORDER
        )
        import_card.pack(fill="x", pady=(0, 16))
        import_inner = ctk.CTkFrame(import_card, fg_color="transparent")
        import_inner.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(import_inner, text="📂", font=("Segoe UI Emoji", 32)).pack(pady=(0, 6))
        ctk.CTkLabel(import_inner, text="Bulk Import CSV",
                     font=FONT_SUBHEADING, text_color=COLOR_TEXT).pack()
        
        if self.can_upload:
            ctk.CTkLabel(
                import_inner,
                text="Upload a Form 16 CSV to register employees\nand generate private QR codes automatically.",
                font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, justify="center"
            ).pack(pady=(4, 10))

            self._import_status_label = ctk.CTkLabel(
                import_inner, text="No file imported yet.",
                font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
                wraplength=320, justify="center"
            )
            self._import_status_label.pack(pady=(0, 10))

            ctk.CTkButton(
                import_inner, text="📁  Select CSV & Import",
                font=(FONT_BODY[0], 13, "bold"),
                fg_color=COLOR_PRIMARY, hover_color="#00B894",
                text_color="#0D1117",
                height=44, corner_radius=CORNER_RADIUS,
                command=self._pick_csv
            ).pack(fill="x")

            if self.is_admin:
                ctk.CTkButton(
                    import_inner, text="🔐  Authorized Scanners",
                    font=FONT_SMALL,
                    fg_color=COLOR_SURFACE_2, hover_color=COLOR_BORDER,
                    text_color=COLOR_TEXT,
                    height=38, corner_radius=CORNER_RADIUS,
                    command=self._show_authorized_scanners_page
                ).pack(fill="x", pady=(8, 0))
        else:
            ctk.CTkLabel(
                import_inner,
                text="🔒 Upload Access Required\n\nCSV bulk upload is restricted to\nAdmin or scanners with Upload permission.",
                font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, justify="center"
            ).pack(pady=(6, 12))

            ctk.CTkButton(
                import_inner, text="🔒  CSV Import (Restricted)",
                font=FONT_SMALL,
                fg_color=COLOR_SURFACE_2, text_color=COLOR_TEXT_MUTED,
                height=38, corner_radius=CORNER_RADIUS, state="disabled"
            ).pack(fill="x")



        # ── Security info ──────────────────────────────────────────────────────
        for icon, label, value, color in [
            ("🔒", "Encryption", "AES-256-GCM × 3", COLOR_PRIMARY),
            ("🔑", "Signature",  "HMAC-SHA512",     COLOR_SECONDARY),
            ("📡", "Storage",    "Supabase Cloud",  COLOR_SUCCESS),
        ]:
            card = ctk.CTkFrame(
                left_inner, fg_color=COLOR_SURFACE,
                corner_radius=10, border_width=1, border_color=COLOR_BORDER
            )
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(inner, text=icon, font=("Segoe UI Emoji", 18)).pack(side="left", padx=(0, 10))
            tf = ctk.CTkFrame(inner, fg_color="transparent")
            tf.pack(side="left")
            ctk.CTkLabel(tf, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
            ctk.CTkLabel(tf, text=value, font=(FONT_SMALL[0], 11, "bold"), text_color=color, anchor="w").pack(anchor="w")

        # ── RIGHT PANEL: Scan History ──────────────────────────────────────────
        right = ctk.CTkFrame(main, fg_color=COLOR_SURFACE, corner_radius=0)
        right.pack(side="right", fill="both", expand=True)

        right_inner = ctk.CTkFrame(right, fg_color="transparent")
        right_inner.pack(fill="both", expand=True, padx=28, pady=24)

        hdr = ctk.CTkFrame(right_inner, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            hdr, text="Scan History",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT, anchor="w"
        ).pack(side="left")
        self._history_count = ctk.CTkLabel(
            hdr, text="0 scans this session",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self._history_count.pack(side="right")

        ctk.CTkFrame(right_inner, height=1, fg_color=COLOR_BORDER).pack(fill="x", pady=(0, 16))

        self._history_frame = ctk.CTkScrollableFrame(
            right_inner, fg_color="transparent",
            scrollbar_button_color=COLOR_BORDER
        )
        self._history_frame.pack(fill="both", expand=True)

        self._empty_label = ctk.CTkLabel(
            self._history_frame,
            text="📋\n\nNo scans yet this session.\nScan a QR code to see results here.",
            font=FONT_BODY, text_color=COLOR_TEXT_MUTED, justify="center"
        )
        self._empty_label.pack(expand=True, pady=60)

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_scan_record(self, employee_name: str, timestamp: str):
        self._scan_history.insert(0, {"name": employee_name, "time": timestamp})
        self._refresh_history()

    def update_import_status(self, msg: str, color: str = None):
        try:
            if self.winfo_exists():
                kw = {"text": msg}
                if color:
                    kw["text_color"] = color
                self._import_status_label.configure(**kw)
        except Exception:
            pass

    def update_usb_status(self, msg: str, color: str = None):
        try:
            if self.winfo_exists():
                kw = {"text": msg}
                if color:
                    kw["text_color"] = color
                self._usb_status_label.configure(**kw)
        except Exception:
            pass

    def update_connection_status(self, phone_ip: str):
        """Called when phone sends PING — show it's alive."""
        try:
            if self.winfo_exists():
                src = "USB" if phone_ip == "127.0.0.1" else f"WiFi ({phone_ip})"
                self._conn_status_dot.configure(
                    text=f"🟢  Phone connected via {src}",
                    text_color=COLOR_SUCCESS
                )
        except Exception:
            pass

    def show_scan_error(self, msg: str):
        try:
            if self.winfo_exists():
                self._conn_status_dot.configure(text=msg, text_color=COLOR_DANGER)
        except Exception:
            pass

    def _manage_scanners(self):
        """Backward-compatible handler for older dashboard builds."""
        handler = getattr(self, "on_manage_scanners", None)
        if callable(handler):
            try:
                handler()
            except Exception:
                pass
        else:
            try:
                if self.winfo_exists():
                    self._conn_status_dot.configure(
                        text="🔐 Authorized scanners management is not configured yet.",
                        text_color=COLOR_WARNING
                    )
            except Exception:
                pass

    # ── Build UI ───────────────────────────────────────────────────────────────

    def _build(self):
        self._build_dashboard_content()

    # ── Connection Tab Builders ────────────────────────────────────────────────

    def _clear_conn_content(self):
        for w in self._conn_content.winfo_children():
            w.destroy()

    def _on_conn_tab_changed(self, value: str):
        mode_map = {"🔌 USB": "usb", "📶 WiFi": "wifi"}
        mode = mode_map.get(value, "usb")
        self._current_conn_mode = mode
        self._clear_conn_content()
        if mode == "usb":
            self._build_usb_tab()
        elif mode == "wifi":
            self._build_wifi_tab()
        if self.on_connection_mode_changed:
            self.on_connection_mode_changed(mode)

    def _build_usb_tab(self):
        self._clear_conn_content()

        ctk.CTkLabel(
            self._conn_content,
            text="🔌  USB via ADB Forwarding",
            font=(FONT_BODY[0], 13, "bold"), text_color=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            self._conn_content,
            text="Most secure — data never leaves the physical cable.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        self._usb_status_label = ctk.CTkLabel(
            self._conn_content,
            text="🔄  Setting up USB forwarding...",
            font=FONT_SMALL, text_color=COLOR_WARNING,
            wraplength=330, justify="left"
        )
        self._usb_status_label.pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            self._conn_content, text="🔄  Re-setup USB",
            font=FONT_SMALL,
            fg_color=COLOR_SURFACE_2, hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            height=36, corner_radius=CORNER_RADIUS,
            command=self._retrigger_usb
        ).pack(fill="x")

        ctk.CTkLabel(
            self._conn_content,
            text="Step 1: Connect phone via USB cable\nStep 2: Allow USB Debugging on phone\nStep 3: Click 'Re-setup USB' if needed\nStep 4: Open Android app → USB → Scan QR",
            font=(FONT_SMALL[0], 10, "normal"), text_color=COLOR_TEXT_MUTED,
            justify="left", anchor="w"
        ).pack(anchor="w", pady=(10, 0))

        # Auto-trigger setup
        self._retrigger_usb()

    def _build_wifi_tab(self):
        self._clear_conn_content()

        ctk.CTkLabel(
            self._conn_content,
            text="📶  WiFi — Same Local Network",
            font=(FONT_BODY[0], 13, "bold"), text_color=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self._conn_content,
            text="Phone and laptop must be on the same network.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        ip_box = ctk.CTkFrame(
            self._conn_content, fg_color=COLOR_SURFACE_2,
            corner_radius=10, border_width=1, border_color=COLOR_BORDER
        )
        ip_box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            ip_box, text="Your Laptop IP Address:",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        ).pack(padx=16, pady=(12, 2), anchor="w")
        ctk.CTkLabel(
            ip_box, text=self.local_ip,
            font=(FONT_MONO[0], 22, "bold"), text_color=COLOR_PRIMARY
        ).pack(padx=16, pady=(0, 12))

        ctk.CTkLabel(
            self._conn_content,
            text="Enter this IP in the Android app → WiFi → IP field\nPort: 12345  (pre-filled in the app)",
            font=(FONT_SMALL[0], 10, "normal"), text_color=COLOR_TEXT_MUTED,
            justify="left", anchor="w"
        ).pack(anchor="w")



    def _retrigger_usb(self):
        """Callback for Re-setup USB button."""
        if self.on_connection_mode_changed:
            self.on_connection_mode_changed("usb")
        if hasattr(self, "_usb_status_label"):
            self._usb_status_label.configure(
                text="🔄  Setting up USB...", text_color=COLOR_WARNING
            )

    # ── CSV Import ─────────────────────────────────────────────────────────────

    def _pick_csv(self):
        if not self.is_admin:
            if hasattr(self, "_import_status_label"):
                self.update_import_status("❌ Access Denied: Only Admin can import CSV files.", COLOR_DANGER)
            return
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Form 16 CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path and self.on_import_csv:
            self.update_import_status("⏳ Importing... please wait.", COLOR_WARNING)
            self.on_import_csv(path)


    # ── History Panel ──────────────────────────────────────────────────────────

    def _refresh_history(self):
        for w in self._history_frame.winfo_children():
            w.destroy()

        count = len(self._scan_history)
        self._history_count.configure(
            text=f"{count} scan{'s' if count != 1 else ''} this session"
        )

        if not self._scan_history:
            self._empty_label = ctk.CTkLabel(
                self._history_frame,
                text="📋\n\nNo scans yet.\nScan a QR code to see results here.",
                font=FONT_BODY, text_color=COLOR_TEXT_MUTED, justify="center"
            )
            self._empty_label.pack(pady=60)
            return

        for record in self._scan_history:
            row = ctk.CTkFrame(
                self._history_frame, fg_color=COLOR_SURFACE_2,
                corner_radius=10, border_width=1, border_color=COLOR_BORDER
            )
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)

            ctk.CTkLabel(inner, text="✅", font=("Segoe UI Emoji", 18)).pack(side="left", padx=(0, 12))
            tf = ctk.CTkFrame(inner, fg_color="transparent")
            tf.pack(side="left")
            ctk.CTkLabel(tf, text=record["name"],
                         font=(FONT_BODY[0], 13, "bold"), text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(tf, text=record["time"],
                         font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
            ctk.CTkLabel(inner, text="Form 16 Retrieved",
                         font=FONT_SMALL, text_color=COLOR_SUCCESS).pack(side="right")
