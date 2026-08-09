import csv
import io
from security.encryption import encrypt_data, decrypt_data
from security.hashing import hash_employee_id, sha512_hash, hash_password
from database.form16_repo import (
    create_form16, get_form16_by_employee, get_salary_details,
    get_other_income, get_deductions, get_tax_details, get_tds_details,
    create_salary_details, create_other_income, create_deductions,
    create_tax_details, create_tds_details
)
from database.employee_repo import (
    create_employee, get_employee_by_id, get_employer_by_id,
    get_all_employers, create_employer
)


# ---------------------------------------------------------------------------
# CSV Bulk Import
# ---------------------------------------------------------------------------

def import_form16_from_csv(file_path: str, system_key: bytes,
                            progress_callback=None,
                            manager_username: str | None = None,
                            authorized_scanners: list[str] | None = None) -> dict:
    """
    Parse a Form 16 CSV file, encrypt all sensitive fields, save to
    Supabase, generate a signed QR code for each employee, and upload
    the QR image PNG to the private 'qr_codes' Supabase storage bucket.

    Returns a summary dict: {"success": int, "skipped": int, "errors": list}
    """
    from database.supabase_client import get_client
    from security.qr_signer import sign_qr_payload
    from security.key_manager import load_app_secret
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    client = get_client()
    app_secret = load_app_secret()
    if authorized_scanners is None:
        from security.authorized_scanners import get_authorized_scanners
        authorized_scanners = get_authorized_scanners()

    enc = lambda v: encrypt_data(str(v), system_key) if v else ""

    summary = {"success": 0, "skipped": 0, "errors": []}

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        emp_name_raw = row.get("employee_name", "").strip()
        emp_email_raw = row.get("employee_email", "").strip().lower()

        if not emp_email_raw:
            summary["skipped"] += 1
            continue

        if progress_callback:
            progress_callback(f"⏳ [{idx}/{total}] Processing {emp_name_raw}…")

        try:
            # ---- Employer ---------------------------------------------------
            employer_id = _get_or_create_employer(row, enc, client)

            # ---- Employee ---------------------------------------------------
            email_hash = sha512_hash(emp_email_raw)
            raw_password = row.get("employee_password", "").strip()
            if not raw_password:
                raw_password = emp_email_raw.split("@")[0] + "123"

            emp_data = {
                "employer_id": employer_id,
                "employee_name": enc(emp_name_raw),
                "pan": enc(row.get("employee_pan", "").strip()),
                "reference_number": enc(row.get("employee_reference_number", "").strip()),
                "address": enc(row.get("employee_address", "").strip()),
                "city": enc(row.get("employee_city", "").strip()),
                "pin_code": enc(row.get("employee_pin_code", "").strip()),
                "email": enc(emp_email_raw),
                "mobile_number": enc(row.get("employee_mobile_number", "").strip()),
                "email_hash": email_hash,
                "password_hash": hash_password(raw_password),
                "hashed_employee_id": "PENDING",
                "id_salt": "PENDING",
            }
            employee = create_employee(emp_data)
            employee_id = employee["employee_id"]

            # Update hashed_employee_id after we know the real ID
            hashed_id, salt_b64 = hash_employee_id(str(employee_id))
            client.table("employee").update({
                "hashed_employee_id": hashed_id,
                "id_salt": salt_b64
            }).eq("employee_id", employee_id).execute()

            # ---- Form 16 header --------------------------------------------
            form16 = create_form16({
                "employee_id": employee_id,
                "financial_year": enc(row.get("financial_year", "").strip()),
                "assessment_year": enc(row.get("assessment_year", "").strip()),
                "employment_from": enc(row.get("employment_from", "").strip()),
                "employment_to": enc(row.get("employment_to", "").strip()),
            })
            form16_id = form16["form16_id"]

            # ---- Salary details --------------------------------------------
            create_salary_details({
                "form16_id": form16_id,
                "gross_salary": enc(row.get("gross_salary", "")),
                "perquisites": enc(row.get("perquisites", "")),
                "total_salary": enc(row.get("total_salary", "")),
                "hra_exemption": enc(row.get("hra_exemption", "")),
                "travel_allowance": enc(row.get("travel_allowance", "")),
                "standard_deduction": enc(row.get("standard_deduction", "")),
                "professional_tax": enc(row.get("professional_tax", "")),
                "total_salary_after_exemptions": enc(row.get("total_salary_after_exemptions", "")),
            })

            # ---- Other income ----------------------------------------------
            create_other_income({
                "form16_id": form16_id,
                "house_property_income": enc(row.get("house_property_income", "")),
                "other_sources_income": enc(row.get("other_sources_income", "")),
                "total_other_income": enc(row.get("total_other_income", "")),
            })

            # ---- Deductions ------------------------------------------------
            create_deductions({
                "form16_id": form16_id,
                "deduction_80c": enc(row.get("deduction_80c", "")),
                "deduction_80ccc": enc(row.get("deduction_80ccc", "")),
                "deduction_80ccd1": enc(row.get("deduction_80ccd1", "")),
                "deduction_80ccd1b": enc(row.get("deduction_80ccd1b", "")),
                "deduction_80ccd2": enc(row.get("deduction_80ccd2", "")),
                "deduction_80d": enc(row.get("deduction_80d", "")),
                "deduction_80e": enc(row.get("deduction_80e", "")),
                "deduction_80g": enc(row.get("deduction_80g", "")),
                "deduction_80tta": enc(row.get("deduction_80tta", "")),
                "other_deductions": enc(row.get("other_deductions", "")),
                "total_deductions": enc(row.get("total_deductions", "")),
            })

            # ---- Tax details -----------------------------------------------
            create_tax_details({
                "form16_id": form16_id,
                "gross_total_income": enc(row.get("gross_total_income", "")),
                "taxable_income": enc(row.get("taxable_income", "")),
                "income_tax": enc(row.get("income_tax", "")),
                "rebate_87a": enc(row.get("rebate_87a", "")),
                "surcharge": enc(row.get("surcharge", "")),
                "health_education_cess": enc(row.get("health_education_cess", "")),
                "tax_payable": enc(row.get("tax_payable", "")),
                "relief_89": enc(row.get("relief_89", "")),
                "net_tax_payable": enc(row.get("net_tax_payable", "")),
            })

            # ---- TDS details per quarter -----------------------------------
            for q in ["q1", "q2", "q3", "q4"]:
                receipt = row.get(f"tds_{q}_receipt_number", "").strip()
                if not receipt:
                    continue
                # VARCHAR(5) limit in tds_details.quarter — keep labels short
                quarter_label = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}[q]
                create_tds_details({
                    "form16_id": form16_id,
                    "quarter": quarter_label,
                    "receipt_number": enc(receipt),
                    "amount_paid": enc(row.get(f"tds_{q}_amount_paid", "")),
                    "tax_deducted": enc(row.get(f"tds_{q}_tax_deducted", "")),
                    "tax_deposited": enc(row.get(f"tds_{q}_tax_deposited", "")),
                    "challan_number": enc(row.get(f"tds_{q}_challan_number", "")),
                    "bsr_code": enc(row.get(f"tds_{q}_bsr_code", "")),
                    "challan_date": enc(row.get(f"tds_{q}_challan_date", "")),
                })

            # ---- Generate & upload QR code to private bucket ---------------
            payload = sign_qr_payload(
                hashed_id,
                app_secret,
                manager_username=manager_username,
                authorized_scanners=authorized_scanners,
            )
            # Save qr_value record in DB
            client.table("qr_code").upsert(
                {"employee_id": employee_id, "qr_value": payload},
                on_conflict="employee_id"
            ).execute()
            # Generate QR image
            qr = qrcode.QRCode(
                version=None, error_correction=ERROR_CORRECT_M,
                box_size=12, border=4
            )
            qr.add_data(payload)
            qr.make(fit=True)
            # Classic black on white for maximum scanner compatibility
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            # Upload to private 'qr_codes' bucket
            file_name = f"qr_{employee_id}.png"
            try:
                client.storage.from_("qr_codes").upload(
                    file_name, png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"}
                )
            except Exception as upload_err:
                # Try remove + re-upload if file already exists
                try:
                    client.storage.from_("qr_codes").remove([file_name])
                    client.storage.from_("qr_codes").upload(
                        file_name, png_bytes,
                        file_options={"content-type": "image/png"}
                    )
                except Exception:
                    raise upload_err

            summary["success"] += 1
            if progress_callback:
                progress_callback(
                    f"✅ [{idx}/{total}] {emp_name_raw} imported successfully.",
                    color="#3FB950"
                )

        except Exception as e:
            summary["errors"].append(f"Row {idx} ({emp_name_raw}): {str(e)}")
            if progress_callback:
                progress_callback(
                    f"❌ [{idx}/{total}] {emp_name_raw}: {str(e)[:80]}",
                    color="#F85149"
                )

    return summary


def _get_or_create_employer(row: dict, enc, client) -> int:
    """Return employer_id for matching employer_pan, creating one if absent."""
    emp_pan_plain = row.get("employer_pan", "").strip()
    # Try to find an existing employer by checking all employers
    # (PAN is stored encrypted so we match by creating a consistent enc value)
    employers = client.table("employer").select("employer_id, pan").execute().data
    # Since PAN is encrypted we cannot easily match — create fresh for each import
    # A smarter deduplier can be added later; for now we always insert & rely on UNIQUE
    employer_data = {
        "employer_name": enc(row.get("employer_name", "").strip()),
        "pan": enc(emp_pan_plain),
        "tan": enc(row.get("employer_tan", "").strip()),
        "address": enc(row.get("employer_address", "").strip()),
    }
    try:
        result = client.table("employer").insert(employer_data).execute()
        return result.data[0]["employer_id"]
    except Exception:
        # If UNIQUE constraint fails (pan already exists), fetch last inserted
        existing = client.table("employer").select("employer_id").order(
            "employer_id", desc=True
        ).limit(1).execute()
        if existing.data:
            return existing.data[0]["employer_id"]
        raise


# ---------------------------------------------------------------------------
# Full Form 16 Read (for scanner / manager view)
# ---------------------------------------------------------------------------

def create_full_form16(employee_id: str, form_data: dict, master_key: bytes) -> dict:
    enc = lambda v: encrypt_data(str(v), master_key) if v else ""
    f16_data = form_data["form16"]
    form16 = create_form16({
        "employee_id": employee_id,
        "financial_year": enc(f16_data.get("financial_year", "")),
        "assessment_year": enc(f16_data.get("assessment_year", "")),
        "employment_from": enc(f16_data.get("employment_from", "")),
        "employment_to": enc(f16_data.get("employment_to", "")),
    })
    form16_id = form16["form16_id"]
    sal = form_data.get("salary", {})
    create_salary_details({
        "form16_id": form16_id,
        "gross_salary": enc(sal.get("gross_salary")),
        "perquisites": enc(sal.get("perquisites")),
        "total_salary": enc(sal.get("total_salary")),
        "hra_exemption": enc(sal.get("hra_exemption")),
        "travel_allowance": enc(sal.get("travel_allowance")),
        "standard_deduction": enc(sal.get("standard_deduction")),
        "professional_tax": enc(sal.get("professional_tax")),
        "total_salary_after_exemptions": enc(sal.get("total_salary_after_exemptions") or sal.get("total_after_exemptions"))
    })
    oi = form_data.get("other_income", {})
    create_other_income({
        "form16_id": form16_id,
        "house_property_income": enc(oi.get("house_property_income")),
        "other_sources_income": enc(oi.get("other_sources_income")),
        "total_other_income": enc(oi.get("total_other_income"))
    })
    ded = form_data.get("deductions", {})
    create_deductions({
        "form16_id": form16_id,
        "deduction_80c": enc(ded.get("deduction_80c") or ded.get("sec_80c")),
        "deduction_80ccc": enc(ded.get("deduction_80ccc") or ded.get("sec_80ccc")),
        "deduction_80ccd1": enc(ded.get("deduction_80ccd1") or ded.get("sec_80ccd_1")),
        "deduction_80ccd1b": enc(ded.get("deduction_80ccd1b") or ded.get("sec_80ccd_1b")),
        "deduction_80ccd2": enc(ded.get("deduction_80ccd2") or ded.get("sec_80ccd_2")),
        "deduction_80d": enc(ded.get("deduction_80d") or ded.get("sec_80d")),
        "deduction_80e": enc(ded.get("deduction_80e") or ded.get("sec_80e")),
        "deduction_80g": enc(ded.get("deduction_80g") or ded.get("sec_80g")),
        "deduction_80tta": enc(ded.get("deduction_80tta") or ded.get("sec_80tta")),
        "other_deductions": enc(ded.get("other_deductions")),
        "total_deductions": enc(ded.get("total_deductions"))
    })
    tax = form_data.get("tax", {})
    create_tax_details({
        "form16_id": form16_id,
        "gross_total_income": enc(tax.get("gross_total_income")),
        "taxable_income": enc(tax.get("taxable_income")),
        "income_tax": enc(tax.get("income_tax")),
        "rebate_87a": enc(tax.get("rebate_87a")),
        "surcharge": enc(tax.get("surcharge")),
        "health_education_cess": enc(tax.get("health_education_cess") or tax.get("health_edu_cess")),
        "tax_payable": enc(tax.get("tax_payable")),
        "relief_89": enc(tax.get("relief_89")),
        "net_tax_payable": enc(tax.get("net_tax_payable"))
    })
    for tds_entry in form_data.get("tds", []):
        create_tds_details({
            "form16_id": form16_id,
            "quarter": tds_entry.get("quarter", ""),
            "receipt_number": enc(tds_entry.get("receipt_number")),
            "amount_paid": enc(tds_entry.get("amount_paid")),
            "tax_deducted": enc(tds_entry.get("tax_deducted")),
            "tax_deposited": enc(tds_entry.get("tax_deposited")),
            "challan_number": enc(tds_entry.get("challan_number")),
            "bsr_code": enc(tds_entry.get("bsr_code")),
            "challan_date": enc(tds_entry.get("challan_date"))
        })
    return form16


def retrieve_full_form16(employee_id: str, master_key: bytes) -> dict | None:
    records = get_form16_by_employee(employee_id)
    if not records:
        return None
    form16 = records[0]
    form16_id = form16["form16_id"]
    dec = lambda v: decrypt_data(v, master_key) if v else ""
    form16_dec = {
        "form16_id": form16_id,
        "financial_year": dec(form16.get("financial_year")),
        "assessment_year": dec(form16.get("assessment_year")),
        "employment_from": dec(form16.get("employment_from")),
        "employment_to": dec(form16.get("employment_to"))
    }
    emp = get_employee_by_id(employee_id)
    emp_dec = {
        "employee_name": dec(emp.get("employee_name")),
        "pan": dec(emp.get("pan")),
        "reference_number": dec(emp.get("reference_number")),
        "address": dec(emp.get("address")),
        "city": dec(emp.get("city")),
        "pin_code": dec(emp.get("pin_code")),
        "email": dec(emp.get("email")),
        "mobile_number": dec(emp.get("mobile_number"))
    }
    employer_dec = {}
    if emp and emp.get("employer_id"):
        employer = get_employer_by_id(emp["employer_id"])
        if employer:
            employer_dec = {
                "employer_name": dec(employer.get("employer_name")),
                "pan": dec(employer.get("pan")),
                "tan": dec(employer.get("tan")),
                "address": dec(employer.get("address"))
            }
    sal_raw = get_salary_details(form16_id) or {}
    salary_dec = {k: dec(v) for k, v in sal_raw.items() if k not in ("salary_id", "form16_id")}
    oi_raw = get_other_income(form16_id) or {}
    oi_dec = {k: dec(v) for k, v in oi_raw.items() if k not in ("other_income_id", "form16_id")}
    ded_raw = get_deductions(form16_id) or {}
    ded_dec = {k: dec(v) for k, v in ded_raw.items() if k not in ("deduction_id", "form16_id")}
    tax_raw = get_tax_details(form16_id) or {}
    tax_dec = {k: dec(v) for k, v in tax_raw.items() if k not in ("tax_id", "form16_id")}
    tds_list = get_tds_details(form16_id)
    tds_dec = []
    for tds_raw in tds_list:
        entry = {"quarter": tds_raw.get("quarter", "")}
        for k, v in tds_raw.items():
            if k not in ("tds_id", "form16_id", "quarter"):
                entry[k] = dec(v)
        tds_dec.append(entry)
    return {
        "employee_id": employee_id,
        "form16": form16_dec,
        "employee": emp_dec,
        "employer": employer_dec,
        "salary": salary_dec,
        "other_income": oi_dec,
        "deductions": ded_dec,
        "tax": tax_dec,
        "tds": tds_dec
    }



def update_full_form16(employee_id: int | str, updated_data: dict, master_key: bytes) -> bool:
    from database.supabase_client import get_client
    client = get_client()
    enc = lambda v: encrypt_data(str(v), master_key) if v is not None and str(v) != "" else ""

    # Update employee table
    emp = updated_data.get("employee", {})
    if emp:
        client.table("employee").update({
            "employee_name": enc(emp.get("employee_name", "")),
            "pan": enc(emp.get("pan", "")),
            "address": enc(emp.get("address", "")),
            "city": enc(emp.get("city", "")),
            "pin_code": enc(emp.get("pin_code", "")),
            "email": enc(emp.get("email", "")),
            "mobile_number": enc(emp.get("mobile_number", "")),
        }).eq("employee_id", employee_id).execute()

    records = get_form16_by_employee(str(employee_id))
    if not records:
        return False
    form16_id = records[0]["form16_id"]

    # Update salary_details table
    sal = updated_data.get("salary", {})
    if sal:
        client.table("salary_details").update({
            "gross_salary": enc(sal.get("gross_salary", "")),
            "perquisites": enc(sal.get("perquisites", "")),
            "total_salary": enc(sal.get("total_salary", "")),
            "hra_exemption": enc(sal.get("hra_exemption", "")),
            "travel_allowance": enc(sal.get("travel_allowance", "")),
            "standard_deduction": enc(sal.get("standard_deduction", "")),
            "professional_tax": enc(sal.get("professional_tax", "")),
            "total_salary_after_exemptions": enc(sal.get("total_salary_after_exemptions", "")),
        }).eq("form16_id", form16_id).execute()

    # Update deductions table
    ded = updated_data.get("deductions", {})
    if ded:
        client.table("deductions").update({
            "deduction_80c": enc(ded.get("deduction_80c") or ded.get("sec_80c", "")),
            "deduction_80d": enc(ded.get("deduction_80d") or ded.get("sec_80d", "")),
            "deduction_80e": enc(ded.get("deduction_80e") or ded.get("sec_80e", "")),
            "deduction_80g": enc(ded.get("deduction_80g") or ded.get("sec_80g", "")),
            "other_deductions": enc(ded.get("other_deductions", "")),
            "total_deductions": enc(ded.get("total_deductions", "")),
        }).eq("form16_id", form16_id).execute()

    # Update tax_details table
    tax = updated_data.get("tax", {})
    if tax:
        client.table("tax_details").update({
            "gross_total_income": enc(tax.get("gross_total_income", "")),
            "taxable_income": enc(tax.get("taxable_income", "")),
            "income_tax": enc(tax.get("income_tax", "")),
            "tax_payable": enc(tax.get("tax_payable", "")),
            "net_tax_payable": enc(tax.get("net_tax_payable", "")),
        }).eq("form16_id", form16_id).execute()

    return True

