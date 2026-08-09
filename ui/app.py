"""
Root application controller - Manager Portal Only.
Manages navigation between manager-facing pages.
Supports USB (adb reverse), WiFi, and Bluetooth scan reception.
"""
import sys
import io
# Force UTF-8 output so emoji in print() don't crash on Windows cp1252 console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import customtkinter as ctk
import socket
import threading
import subprocess
import os
from datetime import datetime
from ui.theme import apply_theme, COLOR_BG
from ui.pages.manager_login import ManagerLoginPage
from ui.pages.manager_dashboard import ManagerDashboard
from ui.pages.auth_gate import AuthGatePage
from ui.pages.form16_viewer import Form16ViewerPage


class Form16ScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme()
        self.title("Form 16 Manager Portal")
        self.geometry("1280x800")
        self.minsize(1024, 700)
        self.configure(fg_color=COLOR_BG)
        

        # ── State ──────────────────────────────────────────────────────────────
        self._current_manager = None
        self._current_page = None
        self._app_secret: bytes | None = None
        self._scan_history: list = []
        self._manager_dashboard_page: ManagerDashboard | None = None
        self._connection_mode = "usb"          # "usb" | "wifi" | "bluetooth"

        try:
            from security.key_manager import load_app_secret
            self._app_secret = load_app_secret()
        except Exception:
            self._app_secret = None

        # Start listeners immediately (they accept connections any time)
        self._start_tcp_listener()        # handles USB (adb-reverse) + WiFi

        self._show_manager_login()

    # ── Error reporting ────────────────────────────────────────────────────────

    def report_callback_exception(self, exc, val, tb):
        import traceback, tkinter.messagebox as mb, sys
        msg = "".join(traceback.format_exception(exc, val, tb))
        print(msg, file=sys.stderr)
        mb.showerror("Application Error", f"An unexpected error occurred:\n\n{msg[:600]}")

    # ── Navigation helpers ─────────────────────────────────────────────────────

    def _clear(self):
        if self._current_page:
            self._current_page.pack_forget()
            self._current_page.destroy()
            self._current_page = None

    def _show(self, widget: ctk.CTkFrame):
        if self._current_page:
            self._current_page.pack_forget()
        self._current_page = widget
        widget.pack(fill="both", expand=True)

    # ── Manager Login ──────────────────────────────────────────────────────────

    def _show_manager_login(self):
        self._clear()
        self._current_manager = None
        self._scan_history = []
        self._manager_dashboard_page = None

        from database.qr_repo import manager_exists
        is_first_run = not manager_exists()

        page = ManagerLoginPage(
            self,
            on_login=self._manager_login,
            on_back=None,                        # No landing page — hide back button
            on_first_run_setup=self._manager_register,
            is_first_run=is_first_run,
        )
        self._show(page)

    def _manager_register(self, username: str, display_name: str, password: str):
        from security.key_manager import generate_and_save_master_key, load_app_secret, encrypt_app_secret
        from database.qr_repo import create_manager, manager_exists
        from security.hashing import hash_password
        import json

        role = "admin" if not manager_exists() else "scanner"

        master_key = generate_and_save_master_key(password, username)
        self._master_key = master_key
        
        # Load app secret and encrypt it with manager's password
        app_secret = load_app_secret()
        self._app_secret = app_secret
        enc_payload = encrypt_app_secret(app_secret, password)

        # Store in display_name as JSON
        display_payload = {
            "real_name": display_name or username,
            "enc_app_secret": enc_payload,
            "role": role,
        }
        display_str = json.dumps(display_payload)

        manager = create_manager({
            "username": username,
            "display_name": display_str,
            "password_hash": hash_password(password),
        })
        manager["role"] = role
        self._current_manager = manager
        self._show_manager_dashboard()

    def _manager_login(self, username: str, password: str):
        from security.key_manager import load_master_key, load_app_secret, decrypt_app_secret, encrypt_app_secret
        from database.qr_repo import get_manager_by_username, get_all_managers
        from database.supabase_client import get_client
        from security.hashing import verify_password
        import json

        manager = get_manager_by_username(username)
        if not manager:
            raise ValueError("Manager account not found.")
        if not verify_password(password, manager["password_hash"]):
            raise ValueError("Incorrect password.")
        
        # Load master key
        try:
            self._master_key = load_master_key(password, username)
        except Exception:
            pass
        
        # Try to parse display_name for encrypted app_secret and role
        app_secret = None
        display_str = manager.get("display_name", "")
        real_name = username
        role = None
        
        try:
            display_payload = json.loads(display_str)
            if isinstance(display_payload, dict):
                role = display_payload.get("role")
                if "enc_app_secret" in display_payload:
                    enc_payload = display_payload["enc_app_secret"]
                    app_secret = decrypt_app_secret(enc_payload, password)
                    real_name = display_payload.get("real_name", username)
        except Exception:
            pass

        if not role:
            all_mgrs = get_all_managers()
            if all_mgrs and all_mgrs[0].get("username") == username:
                role = "admin"
            else:
                role = "scanner"
        manager["role"] = role

        if app_secret is None:
            # Sync local app_secret to cloud display_name
            app_secret = load_app_secret()
            enc_payload = encrypt_app_secret(app_secret, password)
            display_payload = {
                "real_name": display_str or username,
                "enc_app_secret": enc_payload,
                "role": role,
            }
            display_str = json.dumps(display_payload)
            
            # Update display_name in Supabase
            client = get_client()
            client.table("managers").update({"display_name": display_str}).eq("username", username).execute()
            manager["display_name"] = display_str

        # Ensure local app secret file is correct/exists
        from security.key_manager import APP_SECRET_FILE, _ensure_dirs
        _ensure_dirs()
        APP_SECRET_FILE.write_bytes(app_secret)
        self._app_secret = app_secret

        self._current_manager = manager
        self._show_manager_dashboard()


    # ── Manager Dashboard ──────────────────────────────────────────────────────

    def _show_manager_dashboard(self):
        self._clear()
        if not self._current_manager:
            self._show_manager_login()
            return
        
        # Parse display name if it's JSON
        import json
        display_name = self._current_manager.get("display_name") or ""
        real_name = self._current_manager.get("username", "Manager")
        try:
            payload = json.loads(display_name)
            if isinstance(payload, dict):
                real_name = payload.get("real_name", real_name)
        except Exception:
            real_name = display_name or real_name
            
        manager_data_parsed = self._current_manager.copy()
        manager_data_parsed["display_name"] = real_name
        manager_data_parsed["role"] = self._current_manager.get("role", "scanner")


        page = ManagerDashboard(
            self,
            manager_data=manager_data_parsed,
            local_ip=self._get_local_ip(),
            on_logout=self._show_manager_login,
            on_import_csv=self._handle_csv_import,
            on_connection_mode_changed=self._on_connection_mode_changed,
            scan_history=self._scan_history,
        )
        self._show(page)
        self._manager_dashboard_page = page


    def _handle_csv_import(self, file_path: str):
        import hashlib
        from security.key_manager import load_app_secret
        from services.form16_service import import_form16_from_csv
        dashboard = self._manager_dashboard_page

        def _run():
            try:
                app_secret = load_app_secret()
                system_key = hashlib.sha256(app_secret[:32] + b"system_encryption_key").digest()

                def _progress(msg, color=None):
                    self.after(0, lambda m=msg, c=color: dashboard.update_import_status(m, c))

                manager_username = self._current_manager.get("username", "") if self._current_manager else ""
                from security.authorized_scanners import get_authorized_scanners
                authorized_scanners = get_authorized_scanners() or ["__DISABLED__"]
                summary = import_form16_from_csv(
                    file_path,
                    system_key,
                    _progress,
                    manager_username=manager_username,
                    authorized_scanners=authorized_scanners,
                )
                s, sk, errs = summary["success"], summary["skipped"], len(summary["errors"])
                final = (
                    f"✅ Import done: {s} imported, {sk} skipped, {errs} errors."
                    + ("\n" + "\n".join(summary["errors"][:3]) if summary["errors"] else "")
                )
                self.after(0, lambda: dashboard.update_import_status(
                    final, "#3FB950" if errs == 0 else "#D29922"
                ))
            except Exception as e:
                self.after(0, lambda err=str(e): dashboard.update_import_status(
                    f"❌ Import failed: {err[:120]}", "#F85149"
                ))

        threading.Thread(target=_run, daemon=True).start()

    def _on_connection_mode_changed(self, mode: str):
        """Called when manager switches connection tab (usb / wifi / bluetooth)."""
        self._connection_mode = mode
        if mode == "usb":
            threading.Thread(target=self._setup_usb_adb, daemon=True).start()

    # ── QR Scan Processing ─────────────────────────────────────────────────────

    def _on_scan_received(self, qr_data: str, source: str = ""):
        """Thread-safe entry point for all incoming QR scans."""
        self.after(0, lambda: self._process_scan(qr_data, source))

    def _process_scan(self, qr_data: str, source: str = ""):
        if not self._current_manager:
            print(f"[{source or 'Scanner'}] Refused: No manager logged in.")
            return
        if not self._app_secret:
            try:
                from security.key_manager import load_app_secret
                self._app_secret = load_app_secret()
            except Exception:
                return

        from security.qr_signer import verify_qr_payload
        manager_username = self._current_manager.get("username", "") if self._current_manager else ""
        from security.authorized_scanners import get_authorized_scanners
        authorized_scanners = get_authorized_scanners()

        if authorized_scanners:
            normalized_scanners = [s.strip().lower() for s in authorized_scanners if s.strip()]
            if manager_username.strip().lower() not in normalized_scanners:
                print(f"[{source or 'Scanner'}] Refused: Username '{manager_username}' is not in authorized scanners list.")
                self._safe_dashboard_call("show_scan_error",
                    f"Unauthorized scanner - '{manager_username}' is not in authorized list.")
                return

        hashed_eid = verify_qr_payload(
            qr_data,
            self._app_secret,
            manager_username=manager_username,
            authorized_scanners=authorized_scanners,
        )

        if hashed_eid is None:
            # Fallback 1: Lookup in qr_code database table by qr_value
            try:
                from database.supabase_client import get_client
                res = get_client().table("qr_code").select("employee_id").eq("qr_value", qr_data).execute()
                if res.data:
                    emp_id = res.data[0]["employee_id"]
                    emp_res = get_client().table("employee").select("hashed_employee_id").eq("employee_id", emp_id).execute()
                    if emp_res.data:
                        hashed_eid = emp_res.data[0]["hashed_employee_id"]
            except Exception as e:
                print(f"Fallback qr_code lookup error: {e}")

        if hashed_eid is None:
            # Fallback 2: Check if qr_data directly matches a hashed_employee_id in employee table
            try:
                from database.employee_repo import get_employee_by_hashed_id
                emp = get_employee_by_hashed_id(qr_data)
                if emp:
                    hashed_eid = emp.get("hashed_employee_id")
            except Exception:
                pass

        if hashed_eid is None:
            print(f"[{source or 'Scanner'}] Verification failed.")
            self._safe_dashboard_call("show_scan_error",
                "Invalid QR code - signature verification failed.")
            return

        print(f"[{source or 'Scanner'}] Verified OK - opening auth gate.")
        self._on_qr_verified(hashed_eid)



    def _on_qr_verified(self, hashed_eid: str):
        self._clear()
        page = AuthGatePage(
            self,
            manager_username=self._current_manager.get("username", "Manager"),
            hashed_eid=hashed_eid,
            on_authorized=self._on_authorized,
            on_cancel=self._show_manager_dashboard,
        )
        self._show(page)

    def _on_authorized(self, password: str, hashed_eid: str):
        from security.key_manager import load_app_secret
        from security.hashing import verify_password
        from database.employee_repo import get_employee_by_hashed_id
        from services.form16_service import retrieve_full_form16
        import hashlib

        if not verify_password(password, self._current_manager["password_hash"]):
            raise ValueError("Incorrect authorization password.")

        app_secret = load_app_secret()
        system_key = hashlib.sha256(app_secret[:32] + b"system_encryption_key").digest()

        employee = get_employee_by_hashed_id(hashed_eid)
        if not employee:
            raise ValueError("Employee not found in database.")

        form16_data = retrieve_full_form16(employee["employee_id"], system_key)
        if not form16_data:
            raise ValueError("No Form 16 found for this employee.")

        emp_name = form16_data["employee"].get("employee_name", "Unknown")
        timestamp = datetime.now().strftime("%d %b %Y, %H:%M")
        self._scan_history.insert(0, {"name": emp_name, "time": timestamp})
        self._safe_dashboard_call("add_scan_record", emp_name, timestamp)

        self._show_form16_viewer(form16_data)

    def _show_form16_viewer(self, form16_data: dict):
        self._clear()
        username = self._current_manager.get("username", "") if self._current_manager else ""
        from security.authorized_scanners import can_user_edit
        is_admin = (self._current_manager.get("role") == "admin") if self._current_manager else False
        can_edit = can_user_edit(username, is_admin)

        def _on_save(updated_data: dict):
            from security.key_manager import load_app_secret
            from services.form16_service import update_full_form16
            import hashlib
            app_secret = load_app_secret()
            system_key = hashlib.sha256(app_secret[:32] + b"system_encryption_key").digest()
            emp_id = form16_data.get("employee_id")
            if emp_id:
                update_full_form16(emp_id, updated_data, system_key)

        page = Form16ViewerPage(
            self,
            form16_data=form16_data,
            on_back=self._show_manager_dashboard,
            can_edit=can_edit,
            on_save_update=_on_save,
        )
        self._show(page)


    # ── Connection Listeners ───────────────────────────────────────────────────

    def _start_tcp_listener(self):
        """TCP server on 0.0.0.0:12345 — accepts USB (adb-reverse) and WiFi."""
        def loop():
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                srv.bind(("0.0.0.0", 12345))
                srv.listen(5)
                print("[TCP] Listening on 0.0.0.0:12345  (USB + WiFi)")
            except Exception as e:
                print(f"[TCP] Failed to start: {e}")
                return
            while True:
                try:
                    conn, addr = srv.accept()
                    data = conn.recv(8192).decode("utf-8").strip()
                    conn.close()
                    if data == "PING":
                        print(f"[TCP] PING from {addr[0]}")
                        self.after(0, lambda ip=addr[0]: self._safe_dashboard_call(
                            "update_connection_status", ip))
                    elif data:
                        print(f"[TCP] Scan received from {addr[0]}")
                        source = "WiFi" if addr[0] != "127.0.0.1" else "USB"
                        self._on_scan_received(data, source)
                except Exception as e:
                    print(f"[TCP] Error: {e}")

        threading.Thread(target=loop, daemon=True).start()



    def _setup_usb_adb(self):
        adb = self._find_adb()

        if adb is None:
            self.after(0, lambda: self._safe_dashboard_call(
                "update_usb_status",
                "❌ ADB not found. Install Android Platform Tools.",
                "#F85149"))
            return

        try:
            # Start adb server
            subprocess.run(
                [adb, "start-server"],
                capture_output=True,
                timeout=10
            )

            # Detect device
            devices = subprocess.run(
                [adb, "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = devices.stdout.strip().splitlines()

            if len(output) <= 1:
                self.after(0, lambda: self._safe_dashboard_call(
                    "update_usb_status",
                    "❌ No Android device detected.",
                    "#F85149"))
                return

            status = output[1].split()

            if len(status) < 2:
                self.after(0, lambda: self._safe_dashboard_call(
                    "update_usb_status",
                    "❌ Unable to detect device.",
                    "#F85149"))
                return

            state = status[1]

            if state == "unauthorized":
                self.after(0, lambda: self._safe_dashboard_call(
                    "update_usb_status",
                    "⚠️ Allow USB Debugging on your phone.",
                    "#D29922"))
                return

            if state != "device":
                self.after(0, lambda: self._safe_dashboard_call(
                    "update_usb_status",
                    f"❌ Device state: {state}",
                    "#F85149"))
                return

            # Remove previous reverse
            subprocess.run(
                [adb, "reverse", "--remove-all"],
                capture_output=True
            )

            # Create reverse tunnel
            reverse = subprocess.run(
                [adb, "reverse", "tcp:12345", "tcp:12345"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if reverse.returncode != 0:
                self.after(0, lambda: self._safe_dashboard_call(
                    "update_usb_status",
                    "❌ Failed to create USB tunnel.",
                    "#F85149"))
                return

            self.after(0, lambda: self._safe_dashboard_call(
                "update_usb_status",
                "✅ USB Connected and Ready",
                "#3FB950"))

        except Exception as e:
            self.after(0, lambda: self._safe_dashboard_call(
                "update_usb_status",
                f"❌ {str(e)}",
                "#F85149"))

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _safe_dashboard_call(self, method: str, *args):
        """Call a method on the dashboard only if it still exists."""
        if self._manager_dashboard_page:
            try:
                if self._manager_dashboard_page.winfo_exists():
                    getattr(self._manager_dashboard_page, method)(*args)
            except Exception:
                pass

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Unavailable"
        
    def _find_adb(self):
        adb_candidates = [
            "adb",
            r"C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            r"C:\Users\DELL\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Android",
                "Sdk",
                "platform-tools",
                "adb.exe"
            ),
        ]

        for adb in adb_candidates:
            try:
                result = subprocess.run(
                    [adb, "version"],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0:
                    return adb
            except Exception:
                pass

        return None
