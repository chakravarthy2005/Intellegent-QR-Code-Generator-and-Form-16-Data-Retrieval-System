"""
Form 16 QR Scanner - Entry Point
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_env():
    """Ensure .env file exists with credentials."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        example_path = os.path.join(os.path.dirname(__file__), ".env.example")
        if os.path.exists(example_path):
            import shutil
            shutil.copy(example_path, env_path)
            print("[INFO] Created .env from .env.example — please fill in your Supabase credentials.")


def main():
    check_env()

    try:
        from ui.app import Form16ScannerApp
        app = Form16ScannerApp()
        app.mainloop()
    except Exception as e:
        import tkinter as tk
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror(
            "Startup Error",
            f"Failed to start Form16 Scanner:\n\n{str(e)}\n\n"
            "Please ensure:\n"
            "1. All dependencies are installed (pip install -r requirements.txt)\n"
            "2. Your .env file has valid Supabase credentials\n"
            "3. The Supabase database schema has been applied"
        )
        root.destroy()
        raise


if __name__ == "__main__":
    main()
