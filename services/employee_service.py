from security.encryption import encrypt_data
from security.hashing import hash_employee_id, sha512_hash, hash_password, verify_password
from database.employee_repo import create_employee, get_employee_by_email_hash, email_exists, get_all_employers


def register_employee(personal_data: dict, master_key: bytes) -> dict:
    email = personal_data["email"].strip().lower()
    email_hash = sha512_hash(email)
    if email_exists(email_hash):
        raise ValueError("An account with this email already exists.")
    enc = lambda val: encrypt_data(str(val), master_key) if val else ""
    db_data = {
        "employer_id": personal_data["employer_id"],
        "employee_name": enc(personal_data["name"]),
        "pan": enc(personal_data["pan"]),
        "reference_number": enc(personal_data.get("reference_number", "")),
        "address": enc(personal_data.get("address", "")),
        "city": enc(personal_data.get("city", "")),
        "pin_code": enc(personal_data.get("pin_code", "")),
        "email": enc(email),
        "mobile_number": enc(personal_data.get("mobile_number", "")),
        "email_hash": email_hash,
        "password_hash": hash_password(personal_data["password"]),
        "hashed_employee_id": "PENDING",
        "id_salt": "PENDING",
    }
    employee = create_employee(db_data)
    employee_id = employee["employee_id"]
    from database.supabase_client import get_client
    hashed_id, salt_b64 = hash_employee_id(str(employee_id))
    get_client().table("employee").update(
        {"hashed_employee_id": hashed_id, "id_salt": salt_b64}
    ).eq("employee_id", employee_id).execute()
    employee["hashed_employee_id"] = hashed_id
    employee["id_salt"] = salt_b64
    return employee


def login_employee(email: str, password: str) -> dict | None:
    """
    Authenticate an employee using email (SHA-512 hash lookup) and bcrypt
    password verification. Returns the employee DB row or None on failure.
    """
    email = email.strip().lower()
    email_hash = sha512_hash(email)
    employee = get_employee_by_email_hash(email_hash)
    if employee is None:
        return None
    pwd_hash = employee.get("password_hash", "")
    if not pwd_hash:
        return None
    if not verify_password(password, pwd_hash):
        return None
    return employee


def get_employer_list() -> list:
    return get_all_employers()
