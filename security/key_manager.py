"""
Local key management.
"""
import os
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

APP_DATA_DIR = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "Form16Scanner"
KEYS_DIR = APP_DATA_DIR / "keys"
MASTER_KEY_FILE = KEYS_DIR / "master.key"
APP_SECRET_FILE = KEYS_DIR / "app_secret.key"


def _ensure_dirs():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)


def _derive_wrapping_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=salt, iterations=200000)
    return kdf.derive(password.encode("utf-8"))


def generate_and_save_master_key(manager_password: str, username: str = "default") -> bytes:
    _ensure_dirs()
    master_key = os.urandom(32)
    salt = os.urandom(32)
    nonce = os.urandom(12)
    wrapping_key = _derive_wrapping_key(manager_password, salt)
    encrypted_master = AESGCM(wrapping_key).encrypt(nonce, master_key, None)
    payload = {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "enc_key": base64.b64encode(encrypted_master).decode(),
    }
    MASTER_KEY_FILE.write_text(json.dumps(payload))
    user_file = KEYS_DIR / f"master_{username.lower()}.key"
    user_file.write_text(json.dumps(payload))
    return master_key


def load_master_key(manager_password: str, username: str | None = None) -> bytes:
    payload = None
    if username:
        user_file = KEYS_DIR / f"master_{username.lower()}.key"
        if user_file.exists():
            try:
                payload = json.loads(user_file.read_text())
            except Exception:
                payload = None
    if payload is None and MASTER_KEY_FILE.exists():
        try:
            payload = json.loads(MASTER_KEY_FILE.read_text())
        except Exception:
            payload = None

    if payload is not None:
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        enc_key = base64.b64decode(payload["enc_key"])
        wrapping_key = _derive_wrapping_key(manager_password, salt)
        try:
            return AESGCM(wrapping_key).decrypt(nonce, enc_key, None)
        except Exception:
            pass
    # If no master key file could be decrypted with this password, derive a stable user key
    return _derive_wrapping_key(manager_password, b"manager_master_salt_fallback")


def master_key_exists() -> bool:
    return MASTER_KEY_FILE.exists() or len(list(KEYS_DIR.glob("master_*.key"))) > 0



def load_app_secret() -> bytes:
    _ensure_dirs()
    if not APP_SECRET_FILE.exists():
        secret = os.urandom(64)
        APP_SECRET_FILE.write_bytes(secret)
    return APP_SECRET_FILE.read_bytes()


def encrypt_app_secret(app_secret: bytes, password: str) -> dict:
    salt = os.urandom(32)
    nonce = os.urandom(12)
    wrapping_key = _derive_wrapping_key(password, salt)
    encrypted_secret = AESGCM(wrapping_key).encrypt(nonce, app_secret, None)
    return {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.b64encode(encrypted_secret).decode("utf-8"),
    }


def decrypt_app_secret(enc_payload: dict, password: str) -> bytes:
    salt = base64.b64decode(enc_payload["salt"])
    nonce = base64.b64decode(enc_payload["nonce"])
    ciphertext = base64.b64decode(enc_payload["ciphertext"])
    wrapping_key = _derive_wrapping_key(password, salt)
    try:
        return AESGCM(wrapping_key).decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError("Failed to decrypt app secret (incorrect password).")

