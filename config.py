import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
APP_NAME = os.getenv("APP_NAME", "Form16 Scanner")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
PBKDF2_ITERATIONS = 100000
KEY_LENGTH = 32
