from database.supabase_client import get_client

def upsert_qr_code(employee_id: str, qr_value: str) -> dict:
    data = {"employee_id": employee_id, "qr_value": qr_value}
    return get_client().table("qr_code").upsert(data, on_conflict="employee_id").execute().data[0]

def get_qr_by_employee(employee_id: str) -> dict | None:
    result = get_client().table("qr_code").select("*").eq("employee_id", employee_id).execute()
    return result.data[0] if result.data else None

def get_manager_by_username(username: str) -> dict | None:
    result = get_client().table("managers").select("*").eq("username", username).execute()
    return result.data[0] if result.data else None

def create_manager(data: dict) -> dict:
    return get_client().table("managers").insert(data).execute().data[0]

def manager_exists() -> bool:
    result = get_client().table("managers").select("manager_id").limit(1).execute()
    return bool(result.data)

def get_all_managers() -> list:
    result = get_client().table("managers").select("username, display_name").execute()
    return result.data if result.data else []

