# 🔐 Form 16 QR Scanner & Manager Portal

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Cloud%20DB-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-GUI-1F538D?style=for-the-badge)
![Encryption](https://img.shields.io/badge/Encryption-AES--256--GCM-FF6B6B?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)

**An enterprise-grade desktop application for secure Form 16 tax document management, cryptographic QR code generation, and remote mobile scanning via USB or WiFi.**

</div>

---

## 📸 Overview

The system consists of three components:

- **Desktop Application**: Used by the Company Admin to upload Form 16 data, manage authorized scanner accounts, set permissions, and view encrypted data.
- **Manager Mobile App** (Scanner): Allows authorized managers to scan employee QR codes via USB or Wi‑Fi and retrieve the decrypted Form 16 information.
- **Employee Mobile App**: Enables employees to view their QR code, which can be scanned by the manager app.

**Workflow:** An admin creates an account on the desktop app, then signs in with the same credentials on the manager mobile app. The manager scans the QR code shown in the employee app to access the employee’s Form 16 data.
---

## ✨ Features

| Feature | Description |
|---|---|
| 🔑 **Multi-Account Auth** | All accounts verified against Supabase database with bcrypt-hashed passwords |
| 👑 **Role-Based Access (RBAC)** | First account becomes **Admin**; all subsequent accounts are **Scanner** role |
| 🔒 **Granular Permissions** | Admin grants scanners: `Allow Upload CSV` and/or `Allow Edit Data` |
| 🛡️ **Triple AES-256-GCM** | All tax data encrypted 3× with HKDF-derived keys before cloud storage |
| 📲 **HMAC-Signed QR Codes** | QR payloads signed with HMAC-SHA512 — invalid on generic scanner apps |
| 📡 **USB + WiFi Scanning** | Receive QR scans from Android device via ADB or local network |
| 📂 **Bulk CSV Import** | Upload Form 16 CSV → auto-encrypt fields → generate QR codes in bulk |
| ✏️ **Live Database Editing** | Edit employee/salary/tax records after scan and save directly to Supabase |
| 🖨️ **Print / Export** | Export decrypted Form 16 as a formatted text report |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10** or higher
- A [Supabase](https://supabase.com) project (free tier works)
- Android device with the companion scanner app (for mobile scanning)

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/qr-form16-scanner.git
cd qr-form16-scanner
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Windows only — `pyzbar` extra step:**
> ZBar native DLL is required. Install with:
> ```bash
> pip install pyzbar[scripts]
> ```
> Or download manually from: https://github.com/NaturalHistoryMuseum/pyzbar#installation

---

### 3. Set Up Supabase Database

1. Open your [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to **SQL Editor** → **New Query**
3. Paste the full contents of `schema.sql` → click **Run**
4. Go to **Project Settings → API** → copy:
   - `Project URL`
   - `service_role` secret key *(not the anon key)*

---

### 4. Configure Environment

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-secret-key
```

---

### 5. Launch the Application

```bash
python main.py
```

---

## 🖥️ User Roles & Workflow

```
┌─────────────────────────────────────────────────────┐
│              Form 16 Manager Portal                 │
└──────────────────────────┬──────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
   👑 Company Admin                  🔍 Scanner Account
   (First Registered Account)        (All Subsequent Accounts)
          │                                 │
          ├── Import Bulk CSV               ├── Login via Supabase DB Auth
          ├── Manage Authorized Scanners    ├── Receive USB / WiFi Phone Scans
          ├── Grant/Revoke Permissions      ├── Authorization Gate (Password)
          ├── Receive Phone Scans           └── Decrypt & View Form 16
          └── Decrypt, View & Edit Form 16      │
                                                ├── [If Upload CSV granted]
                                                │   └── Access CSV Import
                                                └── [If Edit Data granted]
                                                    └── Access ✏️ Data Editor
```

---

## 🔐 Security Architecture

### Triple AES-256-GCM Encryption

Every sensitive field is encrypted **three times** before storing in Supabase:

```
Plaintext
  └─► Layer 1: AES-256-GCM  (Key₁ = HKDF(secret, "aes256_layer_1_key"))
        └─► Layer 2: AES-256-GCM  (Key₂ = HKDF(secret, "aes256_layer_2_key"))
              └─► Layer 3: AES-256-GCM  (Key₃ = HKDF(secret, "aes256_layer_3_key"))
                    └─► Base64 ciphertext → stored in Supabase
```

Each layer uses a **fresh random 12-byte nonce** with a full AEAD authentication tag.

---

### HMAC-Signed QR Code Payload

```json
{
  "v":   "1",
  "eid": "<PBKDF2-HMAC-SHA512 hashed employee ID>",
  "ts":  "<unix timestamp>",
  "sig": "<HMAC-SHA512 of {v, eid, ts} with app_secret>"
}
```

> The entire payload is Base64-encoded. A generic scanner app will only see random characters. The signature is verified against the **Authorized Scanners** scope on the desktop before any data is revealed.

---

### Local Key Storage

```
%APPDATA%\Form16Scanner\
  ├── master_<username>.key   ← AES-256-GCM encrypted with user's password
  ├── app_secret.key          ← 64-byte HMAC secret (auto-generated on first run)
  └── authorized_scanners.json← Scanner accounts with permission flags
```

---

## 📱 Mobile Scanner Setup

### 🔌 USB Mode (Recommended)

1. Connect Android phone via USB cable
2. Enable **Developer Options → USB Debugging** on the phone
3. In the desktop app, select **USB** connection mode
4. Desktop automatically runs: `adb reverse tcp:12345 tcp:12345`
5. Open the Android scanner app → connect via USB → scan an employee QR code

### 📶 WiFi Mode

1. Connect both phone and PC to the **same WiFi network**
2. In the desktop app, select **WiFi** mode — your local IP is shown
3. Enter that IP and port `12345` in the Android scanner app
4. Scan a QR code — data is sent to the desktop over the local network

---

## 📁 Project Structure

```
QR_CODE_SCANNER_PROJECT/
│
├── main.py                          # App entry point
├── config.py                        # .env loader
├── requirements.txt                 # Dependencies
├── schema.sql                       # Supabase table definitions
├── .env.example                     # Environment template
│
├── security/
│   ├── encryption.py                # Triple AES-256-GCM
│   ├── hashing.py                   # bcrypt + PBKDF2-SHA512
│   ├── key_manager.py               # Key file read/write per user
│   ├── authorized_scanners.py       # Scanner list + permissions store
│   └── qr_signer.py                 # HMAC sign & verify QR payloads
│
├── database/
│   ├── supabase_client.py           # Supabase singleton client
│   ├── employee_repo.py             # Employee table queries
│   ├── form16_repo.py               # All Form 16 section queries
│   └── qr_repo.py                   # QR codes & manager accounts
│
├── services/
│   ├── form16_service.py            # CSV import + DB update logic
│   ├── employee_service.py          # Employee registration
│   ├── qr_service.py                # QR generation & storage
│   └── scanner_service.py           # OpenCV + pyzbar scanner
│
└── ui/
    ├── theme.py                     # Color palette & font constants
    ├── app.py                       # Navigation + TCP listener
    ├── components/                  # Shared widgets
    └── pages/
        ├── landing_page.py          # Home / role selector
        ├── manager_login.py         # Login & account creation
        ├── manager_dashboard.py     # Main dashboard panel
        ├── authorized_scanners_page.py  # Scanner permission manager
        ├── auth_gate.py             # Decryption password gate
        └── form16_viewer.py         # Form 16 viewer + data editor
```

---

## 💡 Troubleshooting

| Problem | Solution |
|---|---|
| **Login fails for old account** | Credentials are checked against Supabase DB. Ensure username/password match exactly what was used at registration |
| **"Invalid QR signature"** | The scanning account is not in the **Authorized Scanners** list. Admin must add them |
| **ADB device not found** | Install [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools) and add to `%PATH%` |
| **pyzbar import error** | Install ZBar DLL via `pip install pyzbar[scripts]` or download manually |
| **Supabase connection error** | Check `.env` has the correct URL and `service_role` key (not `anon` key) |
| **Data not saving after edit** | Confirm user has `Allow Edit Data` permission granted by Admin |

---

## ⚠️ Important Notes

- Always use the **`service_role`** key in `.env` — the `anon` key does not have write access
- The `master_<username>.key` file is **device-specific** — encrypted key files cannot be transferred between machines
- **First account registered** is permanently the Company Admin — choose this account carefully
- All Form 16 data in Supabase is **always encrypted** — raw values in the DB are unreadable without the correct key

---

<div align="center">

Built with ❤️ using **Python · CustomTkinter · Supabase · OpenCV · cryptography**

</div>
