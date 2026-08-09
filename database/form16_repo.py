from database.supabase_client import get_client

def create_form16(data: dict) -> dict:
    return get_client().table("form16").insert(data).execute().data[0]

def get_form16_by_employee(employee_id: str) -> list:
    return get_client().table("form16").select("*").eq("employee_id", employee_id).order("form16_id", desc=True).execute().data

def get_form16_by_id(form16_id: str) -> dict | None:
    result = get_client().table("form16").select("*").eq("form16_id", form16_id).execute()
    return result.data[0] if result.data else None

def create_salary_details(data: dict) -> dict:
    return get_client().table("salary_details").insert(data).execute().data[0]

def get_salary_details(form16_id: str) -> dict | None:
    result = get_client().table("salary_details").select("*").eq("form16_id", form16_id).execute()
    return result.data[0] if result.data else None

def create_other_income(data: dict) -> dict:
    return get_client().table("other_income").insert(data).execute().data[0]

def get_other_income(form16_id: str) -> dict | None:
    result = get_client().table("other_income").select("*").eq("form16_id", form16_id).execute()
    return result.data[0] if result.data else None

def create_deductions(data: dict) -> dict:
    return get_client().table("deductions").insert(data).execute().data[0]

def get_deductions(form16_id: str) -> dict | None:
    result = get_client().table("deductions").select("*").eq("form16_id", form16_id).execute()
    return result.data[0] if result.data else None

def create_tax_details(data: dict) -> dict:
    return get_client().table("tax_details").insert(data).execute().data[0]

def get_tax_details(form16_id: str) -> dict | None:
    result = get_client().table("tax_details").select("*").eq("form16_id", form16_id).execute()
    return result.data[0] if result.data else None

def create_tds_details(data: dict) -> dict:
    return get_client().table("tds_details").insert(data).execute().data[0]

def get_tds_details(form16_id: str) -> list:
    return get_client().table("tds_details").select("*").eq("form16_id", form16_id).order("quarter").execute().data
