import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image
from security.qr_signer import sign_qr_payload
from security.key_manager import load_app_secret
from database.qr_repo import upsert_qr_code, get_qr_by_employee


def generate_qr_for_employee(employee_id: str, hashed_employee_id: str, manager_username: str | None = None, authorized_scanners: list[str] | None = None) -> Image.Image:
    """Generate, sign, store to DB and upload PNG to the private bucket."""
    app_secret = load_app_secret()
    payload = sign_qr_payload(
        hashed_employee_id,
        app_secret,
        manager_username=manager_username,
        authorized_scanners=authorized_scanners,
    )
    upsert_qr_code(employee_id, payload)

    img = _build_qr_image(payload)

    # Upload to private 'qr_codes' storage bucket
    _upload_qr_to_bucket(employee_id, img)

    return img


def get_employee_qr_image(employee_id: str) -> Image.Image | None:
    """
    Primary: download QR PNG from the private Supabase storage bucket.
    Fallback: rebuild from the signed payload stored in the qr_code table.
    """
    # 1. Try private bucket first
    img = get_employee_qr_from_bucket(employee_id)
    if img:
        return img

    # 2. Fallback: rebuild from DB payload
    record = get_qr_by_employee(employee_id)
    if not record:
        return None
    return _build_qr_image(record["qr_value"])


def get_employee_qr_from_bucket(employee_id: str) -> Image.Image | None:
    """
    Download qr_{employee_id}.png from the private 'qr_codes' Supabase bucket.
    Returns a PIL Image or None if the file is not found / download fails.
    """
    try:
        from database.supabase_client import get_client
        client = get_client()
        file_name = f"qr_{employee_id}.png"
        raw = client.storage.from_("qr_codes").download(file_name)
        if not raw:
            return None
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _upload_qr_to_bucket(employee_id: str, img: Image.Image):
    """Encode PIL image to PNG bytes and upload to the private bucket."""
    try:
        from database.supabase_client import get_client
        client = get_client()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        file_name = f"qr_{employee_id}.png"
        try:
            client.storage.from_("qr_codes").upload(
                file_name, png_bytes,
                file_options={"content-type": "image/png", "upsert": "true"}
            )
        except Exception:
            # Remove stale file then re-upload
            try:
                client.storage.from_("qr_codes").remove([file_name])
            except Exception:
                pass
            client.storage.from_("qr_codes").upload(
                file_name, png_bytes,
                file_options={"content-type": "image/png"}
            )
    except Exception as e:
        # Non-fatal: QR record already saved in DB; bucket upload failure is logged only
        import sys
        print(f"[WARNING] QR bucket upload failed for employee {employee_id}: {e}",
              file=sys.stderr)


def _build_qr_image(payload: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,  # M = ~15% recovery, less dense than H
        box_size=12,                        # larger boxes = sharper pixels
        border=4,                           # standard quiet zone
    )
    qr.add_data(payload)
    qr.make(fit=True)
    # Classic black on white — maximum contrast for any scanner
    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")
