"""Storage and permission manager for authorized scanner accounts."""
import json
from pathlib import Path
from security.key_manager import APP_DATA_DIR

AUTHORIZED_SCANNERS_FILE = APP_DATA_DIR / "authorized_scanners.json"


def _ensure_file() -> Path:
    AUTHORIZED_SCANNERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not AUTHORIZED_SCANNERS_FILE.exists():
        AUTHORIZED_SCANNERS_FILE.write_text("[]", encoding="utf-8")
    return AUTHORIZED_SCANNERS_FILE


def _load_raw() -> list:
    try:
        data = json.loads(_ensure_file().read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_raw(data: list):
    _ensure_file().write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_authorized_scanners() -> list[str]:
    """Returns list of plain username strings for backward compatibility."""
    raw = _load_raw()
    usernames = []
    for item in raw:
        if isinstance(item, dict):
            u = item.get("username", "").strip()
            if u:
                usernames.append(u)
        elif isinstance(item, str) and item.strip():
            usernames.append(item.strip())
    return usernames


def get_authorized_scanners_detail() -> dict[str, dict]:
    """Returns dictionary mapping normalized username to detailed permission dict."""
    raw = _load_raw()
    details = {}
    for item in raw:
        if isinstance(item, dict):
            u = str(item.get("username", "")).strip()
            if u:
                details[u.lower()] = {
                    "username": u,
                    "can_upload_csv": bool(item.get("can_upload_csv", False)),
                    "can_edit_data": bool(item.get("can_edit_data", False)),
                }
        elif isinstance(item, str) and item.strip():
            u = item.strip()
            details[u.lower()] = {
                "username": u,
                "can_upload_csv": False,
                "can_edit_data": False,
            }
    return details


def add_authorized_scanner(username: str, can_upload_csv: bool = False, can_edit_data: bool = False) -> list[str]:
    cleaned = (username or "").strip()
    if not cleaned:
        return get_authorized_scanners()

    raw = _load_raw()
    found = False
    for item in raw:
        if isinstance(item, dict) and item.get("username", "").strip().lower() == cleaned.lower():
            item["can_upload_csv"] = can_upload_csv
            item["can_edit_data"] = can_edit_data
            found = True
            break
        elif isinstance(item, str) and item.strip().lower() == cleaned.lower():
            raw.remove(item)
            break

    if not found:
        raw.append({
            "username": cleaned,
            "can_upload_csv": can_upload_csv,
            "can_edit_data": can_edit_data,
        })

    _save_raw(raw)
    return get_authorized_scanners()


def update_scanner_permissions(username: str, can_upload_csv: bool, can_edit_data: bool):
    cleaned = (username or "").strip().lower()
    raw = _load_raw()
    for item in raw:
        if isinstance(item, dict) and item.get("username", "").strip().lower() == cleaned:
            item["can_upload_csv"] = can_upload_csv
            item["can_edit_data"] = can_edit_data
            break
        elif isinstance(item, str) and item.strip().lower() == cleaned:
            raw.remove(item)
            raw.append({
                "username": username.strip(),
                "can_upload_csv": can_upload_csv,
                "can_edit_data": can_edit_data,
            })
            break
    _save_raw(raw)


def remove_authorized_scanner(username: str) -> list[str]:
    cleaned = (username or "").strip().lower()
    raw = _load_raw()
    filtered = []
    for item in raw:
        if isinstance(item, dict):
            if item.get("username", "").strip().lower() != cleaned:
                filtered.append(item)
        elif isinstance(item, str):
            if item.strip().lower() != cleaned:
                filtered.append(item)
    _save_raw(filtered)
    return get_authorized_scanners()


def can_user_upload(username: str, is_admin: bool = False) -> bool:
    if is_admin:
        return True
    details = get_authorized_scanners_detail()
    cfg = details.get((username or "").strip().lower(), {})
    return bool(cfg.get("can_upload_csv", False))


def can_user_edit(username: str, is_admin: bool = False) -> bool:
    if is_admin:
        return True
    details = get_authorized_scanners_detail()
    cfg = details.get((username or "").strip().lower(), {})
    return bool(cfg.get("can_edit_data", False))


def is_valid_account(username: str) -> bool:
    cleaned = (username or "").strip()
    if not cleaned:
        return False
    from database.qr_repo import get_manager_by_username
    try:
        mgr = get_manager_by_username(cleaned)
        return mgr is not None
    except Exception:
        return True
