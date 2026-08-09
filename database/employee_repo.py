from database.supabase_client import get_client

def create_employer(data: dict) -> dict:
    return get_client().table("employer").insert(data).execute().data[0]

def get_all_employers() -> list:
    return get_client().table("employer").select("employer_id, employer_name").execute().data

def get_employer_by_id(employer_id: str) -> dict | None:
    result = get_client().table("employer").select("*").eq("employer_id", employer_id).execute()
    return result.data[0] if result.data else None

def create_employee(data: dict) -> dict:
    return get_client().table("employee").insert(data).execute().data[0]

def get_employee_by_email_hash(email_hash: str) -> dict | None:
    result = get_client().table("employee").select("*").eq("email_hash", email_hash).execute()
    return result.data[0] if result.data else None

def get_employee_by_hashed_id(hashed_id: str) -> dict | None:
    result = get_client().table("employee").select("*").eq("hashed_employee_id", hashed_id).execute()
    return result.data[0] if result.data else None

def get_employee_by_id(employee_id: str) -> dict | None:
    result = get_client().table("employee").select("*").eq("employee_id", employee_id).execute()
    return result.data[0] if result.data else None

def email_exists(email_hash: str) -> bool:
    result = get_client().table("employee").select("employee_id").eq("email_hash", email_hash).execute()
    return bool(result.data)
