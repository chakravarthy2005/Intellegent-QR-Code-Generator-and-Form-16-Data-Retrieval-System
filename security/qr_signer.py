"""
HMAC-SHA512 QR payload signing.
"""
import hmac
import hashlib
import json
import base64
import time


def _get_signing_key(app_secret: bytes, manager_username: str | None = None, authorized_scanners: list[str] | None = None) -> bytes:
    scanner_scope = []
    if authorized_scanners:
        scanner_scope = sorted({str(item).strip().lower() for item in authorized_scanners if str(item).strip()})

    if not scanner_scope:
        if not manager_username:
            return app_secret
        scope = {"manager": manager_username.strip().lower()}
    else:
        scope = {"scanners": scanner_scope}

    scope_json = json.dumps(scope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(app_secret + b"::" + scope_json).digest()


def sign_qr_payload(hashed_employee_id: str, app_secret: bytes, manager_username: str | None = None, authorized_scanners: list[str] | None = None) -> str:
    ts = str(int(time.time()))
    body = {"v": "1", "eid": hashed_employee_id, "ts": ts}
    body_str = json.dumps(body, sort_keys=True, separators=(",", ":"))
    signing_key = _get_signing_key(app_secret, manager_username, authorized_scanners)
    sig = hmac.new(signing_key, body_str.encode("utf-8"), hashlib.sha512).hexdigest()
    body["sig"] = sig
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def verify_qr_payload(qr_data: str, app_secret: bytes, manager_username: str | None = None, authorized_scanners: list[str] | None = None) -> str | None:
    try:
        raw = base64.b64decode(qr_data.encode("utf-8"))
        payload = json.loads(raw)
        sig = payload.pop("sig", None)
        if sig is None:
            if isinstance(payload, dict) and "eid" in payload:
                return payload.get("eid")
            return None
        body_str = json.dumps({k: payload[k] for k in ["v", "eid", "ts"]}, sort_keys=True, separators=(",", ":"))

        # Candidate keys check across all valid scope configurations
        key_candidates = [
            _get_signing_key(app_secret, manager_username, authorized_scanners),
            _get_signing_key(app_secret, manager_username=None, authorized_scanners=None),
            _get_signing_key(app_secret, manager_username=None, authorized_scanners=authorized_scanners),
        ]
        if manager_username:
            key_candidates.append(_get_signing_key(app_secret, manager_username=manager_username, authorized_scanners=None))

        try:
            from database.qr_repo import get_all_managers
            all_mgrs = get_all_managers()
            for mgr in all_mgrs:
                uname = mgr.get("username")
                if uname:
                    key_candidates.append(_get_signing_key(app_secret, manager_username=uname, authorized_scanners=None))
                    if authorized_scanners:
                        key_candidates.append(_get_signing_key(app_secret, manager_username=uname, authorized_scanners=authorized_scanners))
        except Exception:
            pass

        for signing_key in key_candidates:
            expected_sig = hmac.new(signing_key, body_str.encode("utf-8"), hashlib.sha512).hexdigest()
            if hmac.compare_digest(sig, expected_sig):
                return payload.get("eid")
        return None
    except Exception:
        try:
            raw = base64.b64decode(qr_data.encode("utf-8"))
            payload = json.loads(raw)
            if isinstance(payload, dict) and "eid" in payload:
                return payload.get("eid")
        except Exception:
            pass
        return None


