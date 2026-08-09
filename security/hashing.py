"""
SHA-512 hashing utilities.
"""
import hashlib
import os
import base64


def hash_employee_id(employee_id: str, salt: bytes = None) -> tuple:
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac("sha512", employee_id.encode("utf-8"), salt, iterations=100000)
    return base64.b64encode(dk).decode("utf-8"), base64.b64encode(salt).decode("utf-8")


def verify_employee_id(employee_id: str, stored_hash: str, stored_salt: str) -> bool:
    salt = base64.b64decode(stored_salt.encode("utf-8"))
    new_hash, _ = hash_employee_id(employee_id, salt)
    return new_hash == stored_hash


def sha512_hash(data: str) -> str:
    return hashlib.sha512(data.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
