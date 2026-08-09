import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_TEXT,
    COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_SUCCESS, COLOR_DANGER, COLOR_SECONDARY,
    FONT_HEADING, FONT_BODY, FONT_SMALL, CORNER_RADIUS, BUTTON_HEIGHT
)
from security.authorized_scanners import (
    get_authorized_scanners, get_authorized_scanners_detail,
    add_authorized_scanner, update_scanner_permissions, remove_authorized_scanner, is_valid_account
)
from database.qr_repo import get_all_managers


class AuthorizedScannersPage(ctk.CTkFrame):
    def __init__(self, master, on_back: callable):
        super().__init__(master, fg_color=COLOR_BG)
        self.on_back = on_back
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=64, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back",
            font=FONT_SMALL,
            fg_color="transparent", hover_color=COLOR_SURFACE_2,
            text_color=COLOR_TEXT_MUTED, width=90, height=32,
            command=self.on_back
        ).pack(side="left", padx=16, pady=16)

        ctk.CTkLabel(
            top, text="🔐 Authorized Scanners & Permissions",
            font=(FONT_HEADING[0], 16, "bold"), text_color=COLOR_PRIMARY
        ).pack(side="left", padx=8, pady=16)

        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER, width=580)
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(inner, text="Add Authorized Scanner Account", font=FONT_HEADING, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            inner,
            text="Select or type a created manager account. Specify permissions for scanning, uploading CSV, or editing data.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, wraplength=500, justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # Quick selector from created accounts in DB
        db_accounts = []
        try:
            db_accounts = [m.get("username") for m in get_all_managers() if m.get("username")]
        except Exception:
            pass

        if db_accounts:
            select_frame = ctk.CTkFrame(inner, fg_color="transparent")
            select_frame.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(select_frame, text="Select Created Account:", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, 4))
            self.account_dropdown = ctk.CTkOptionMenu(
                select_frame,
                values=db_accounts,
                command=self._on_account_selected,
                height=34,
                fg_color=COLOR_SURFACE_2,
                button_color=COLOR_PRIMARY,
                button_hover_color="#00B894",
                text_color=COLOR_TEXT,
            )
            self.account_dropdown.pack(fill="x")

        self.username_entry = ctk.CTkEntry(inner, placeholder_text="Enter username from created accounts", width=480, height=BUTTON_HEIGHT)
        self.username_entry.pack(fill="x", pady=(0, 8))

        # Permission checkboxes for adding
        perm_box = ctk.CTkFrame(inner, fg_color=COLOR_SURFACE_2, corner_radius=8)
        perm_box.pack(fill="x", pady=(0, 8))
        perm_inner = ctk.CTkFrame(perm_box, fg_color="transparent")
        perm_inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(perm_inner, text="Scanner Permissions:", font=(FONT_SMALL[0], 11, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=(0, 12))

        self.chk_upload_var = ctk.BooleanVar(value=False)
        self.chk_upload = ctk.CTkCheckBox(perm_inner, text="Allow Upload CSV", variable=self.chk_upload_var, font=FONT_SMALL, text_color=COLOR_TEXT)
        self.chk_upload.pack(side="left", padx=8)

        self.chk_edit_var = ctk.BooleanVar(value=False)
        self.chk_edit = ctk.CTkCheckBox(perm_inner, text="Allow Editing Data", variable=self.chk_edit_var, font=FONT_SMALL, text_color=COLOR_TEXT)
        self.chk_edit.pack(side="left", padx=8)

        self.status_label = ctk.CTkLabel(inner, text="", font=FONT_SMALL, text_color=COLOR_SUCCESS, anchor="w", wraplength=480)
        self.status_label.pack(anchor="w", pady=(2, 6))

        ctk.CTkButton(
            inner, text="➕ Add Authorized Scanner",
            command=self._add_scanner,
            height=BUTTON_HEIGHT,
            corner_radius=CORNER_RADIUS,
            fg_color=COLOR_PRIMARY,
            hover_color="#00B894",
            text_color="#0D1117"
        ).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(inner, text="Currently Authorized Scanners:", font=(FONT_SMALL[0], 11, "bold"), text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, 6))

        self.listbox = ctk.CTkScrollableFrame(inner, fg_color=COLOR_SURFACE_2, corner_radius=10, height=200)
        self.listbox.pack(fill="both", expand=True)
        self._refresh_list()

    def _on_account_selected(self, username: str):
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, username)

    def _refresh_list(self):
        for child in self.listbox.winfo_children():
            child.destroy()
        details = get_authorized_scanners_detail()
        if not details:
            ctk.CTkLabel(self.listbox, text="No authorized scanners configured yet.", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12, pady=12)
            return

        for user_key, cfg in details.items():
            user = cfg.get("username", user_key)
            can_upload = cfg.get("can_upload_csv", False)
            can_edit = cfg.get("can_edit_data", False)

            row = ctk.CTkFrame(self.listbox, fg_color=COLOR_SURFACE, corner_radius=8)
            row.pack(fill="x", padx=6, pady=4)

            left_box = ctk.CTkFrame(row, fg_color="transparent")
            left_box.pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(left_box, text=f"👤 {user}", font=(FONT_BODY[0], 13, "bold"), text_color=COLOR_TEXT, anchor="w").pack(anchor="w")

            perm_desc = []
            if can_upload:
                perm_desc.append("Upload CSV")
            if can_edit:
                perm_desc.append("Edit Data")
            tag_text = f"Perms: {', '.join(perm_desc)}" if perm_desc else "Perms: View Only"
            tag_color = COLOR_PRIMARY if perm_desc else COLOR_TEXT_MUTED
            ctk.CTkLabel(left_box, text=tag_text, font=(FONT_SMALL[0], 10), text_color=tag_color, anchor="w").pack(anchor="w")

            right_box = ctk.CTkFrame(row, fg_color="transparent")
            right_box.pack(side="right", padx=8, pady=4)

            # Toggles for Upload & Edit
            up_var = ctk.BooleanVar(value=can_upload)
            up_switch = ctk.CTkSwitch(
                right_box, text="Upload", variable=up_var, font=(FONT_SMALL[0], 10),
                command=lambda u=user, uv=up_var, ev_val=can_edit: self._update_perm(u, uv.get(), ev_val)
            )
            up_switch.pack(side="left", padx=6)

            ed_var = ctk.BooleanVar(value=can_edit)
            ed_switch = ctk.CTkSwitch(
                right_box, text="Edit", variable=ed_var, font=(FONT_SMALL[0], 10),
                command=lambda u=user, uv_val=can_upload, ev=ed_var: self._update_perm(u, uv_val, ev.get())
            )
            ed_switch.pack(side="left", padx=6)

            ctk.CTkButton(
                right_box, text="Remove", font=(FONT_SMALL[0], 10),
                fg_color="transparent", hover_color=COLOR_DANGER,
                text_color=COLOR_DANGER, width=54, height=26,
                command=lambda u=user: self._remove_scanner(u)
            ).pack(side="left", padx=(6, 0))

    def _update_perm(self, username: str, can_upload: bool, can_edit: bool):
        update_scanner_permissions(username, can_upload, can_edit)
        self.status_label.configure(text=f"Updated permissions for '{username}'.", text_color=COLOR_SUCCESS)
        self._refresh_list()

    def _add_scanner(self):
        username = self.username_entry.get().strip()
        if not username:
            self.status_label.configure(text="Please enter or select a username.", text_color=COLOR_DANGER)
            return
        if not is_valid_account(username):
            self.status_label.configure(text=f"❌ Account '{username}' not found in created database accounts.", text_color=COLOR_DANGER)
            return

        can_upload = self.chk_upload_var.get()
        can_edit = self.chk_edit_var.get()

        add_authorized_scanner(username, can_upload_csv=can_upload, can_edit_data=can_edit)
        self.username_entry.delete(0, "end")
        self.chk_upload_var.set(False)
        self.chk_edit_var.set(False)
        self.status_label.configure(text=f"✅ Added '{username}' to authorized scanners.", text_color=COLOR_SUCCESS)
        self._refresh_list()

    def _remove_scanner(self, username: str):
        remove_authorized_scanner(username)
        self.status_label.configure(text=f"Removed '{username}'.", text_color=COLOR_TEXT_MUTED)
        self._refresh_list()
