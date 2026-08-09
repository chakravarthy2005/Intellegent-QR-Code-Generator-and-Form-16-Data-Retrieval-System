-- =========================================================================
-- Form 16 QR Scanner - Supabase Schema (Encryption Compatible)
-- Run this in your Supabase SQL Editor to set up clean, encrypted tables.
-- =========================================================================

-- 1. Employer table
CREATE TABLE IF NOT EXISTS employer (
    employer_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_name   TEXT NOT NULL,         -- Encrypted Base64
    pan             TEXT UNIQUE NOT NULL,  -- Encrypted Base64
    tan             TEXT UNIQUE NOT NULL,  -- Encrypted Base64
    address         TEXT
);

-- 2. Employee table
CREATE TABLE IF NOT EXISTS employee (
    employee_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employer_id         INTEGER NOT NULL REFERENCES employer(employer_id) ON DELETE CASCADE,
    employee_name       TEXT NOT NULL,         -- Encrypted Base64
    pan                 TEXT UNIQUE NOT NULL,  -- Encrypted Base64
    reference_number    TEXT,                  -- Encrypted Base64
    address             TEXT,                  -- Encrypted Base64
    city                TEXT,                  -- Encrypted Base64
    pin_code            TEXT,                  -- Encrypted Base64
    email               TEXT,                  -- Encrypted Base64
    mobile_number       TEXT,                  -- Encrypted Base64
    
    -- Security & Portal fields
    email_hash          TEXT UNIQUE,           -- SHA-512 of plain email
    hashed_employee_id  TEXT UNIQUE,           -- PBKDF2-SHA512 of employee ID
    id_salt             TEXT,                  -- Salt used in PBKDF2 hash
    password_hash       TEXT                   -- bcrypt hash of employee login password
);

CREATE INDEX IF NOT EXISTS idx_employee_employer ON employee(employer_id);
CREATE INDEX IF NOT EXISTS idx_employee_hashed_id ON employee(hashed_employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_email_hash ON employee(email_hash);

-- 3. Form16 table
CREATE TABLE IF NOT EXISTS form16 (
    form16_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employee(employee_id) ON DELETE CASCADE,
    financial_year  TEXT,    -- Encrypted Base64
    assessment_year TEXT,    -- Encrypted Base64
    employment_from TEXT,    -- Encrypted Base64
    employment_to   TEXT     -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_form16_employee ON form16(employee_id);

-- 4. Salary Details table
CREATE TABLE IF NOT EXISTS salary_details (
    salary_id                     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    form16_id                     INTEGER UNIQUE REFERENCES form16(form16_id) ON DELETE CASCADE,
    gross_salary                  TEXT,    -- Encrypted Base64
    perquisites                   TEXT,    -- Encrypted Base64
    total_salary                  TEXT,    -- Encrypted Base64
    hra_exemption                 TEXT,    -- Encrypted Base64
    travel_allowance              TEXT,    -- Encrypted Base64
    standard_deduction            TEXT,    -- Encrypted Base64
    professional_tax              TEXT,    -- Encrypted Base64
    total_salary_after_exemptions TEXT     -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_salary_form16 ON salary_details(form16_id);

-- 5. Other Income table
CREATE TABLE IF NOT EXISTS other_income (
    other_income_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    form16_id              INTEGER UNIQUE REFERENCES form16(form16_id) ON DELETE CASCADE,
    house_property_income  TEXT,    -- Encrypted Base64
    other_sources_income   TEXT,    -- Encrypted Base64
    total_other_income     TEXT     -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_other_income_form16 ON other_income(form16_id);

-- 6. Deductions table
CREATE TABLE IF NOT EXISTS deductions (
    deduction_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    form16_id         INTEGER UNIQUE REFERENCES form16(form16_id) ON DELETE CASCADE,
    deduction_80c     TEXT,    -- Encrypted Base64
    deduction_80ccc   TEXT,    -- Encrypted Base64
    deduction_80ccd1  TEXT,    -- Encrypted Base64
    deduction_80ccd1b TEXT,    -- Encrypted Base64
    deduction_80ccd2  TEXT,    -- Encrypted Base64
    deduction_80d     TEXT,    -- Encrypted Base64
    deduction_80e     TEXT,    -- Encrypted Base64
    deduction_80g     TEXT,    -- Encrypted Base64
    deduction_80tta   TEXT,    -- Encrypted Base64
    other_deductions  TEXT,    -- Encrypted Base64
    total_deductions  TEXT     -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_deductions_form16 ON deductions(form16_id);

-- 7. Tax Details table
CREATE TABLE IF NOT EXISTS tax_details (
    tax_id                 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    form16_id              INTEGER UNIQUE REFERENCES form16(form16_id) ON DELETE CASCADE,
    gross_total_income     TEXT,    -- Encrypted Base64
    taxable_income         TEXT,    -- Encrypted Base64
    income_tax             TEXT,    -- Encrypted Base64
    rebate_87a             TEXT,    -- Encrypted Base64
    surcharge              TEXT,    -- Encrypted Base64
    health_education_cess  TEXT,    -- Encrypted Base64
    tax_payable            TEXT,    -- Encrypted Base64
    relief_89              TEXT,    -- Encrypted Base64
    net_tax_payable        TEXT     -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_tax_details_form16 ON tax_details(form16_id);

-- 8. TDS Details table
CREATE TABLE IF NOT EXISTS tds_details (
    tds_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    form16_id       INTEGER NOT NULL REFERENCES form16(form16_id) ON DELETE CASCADE,
    quarter         TEXT,            -- Plaintext quarter (Q1/Q2/Q3/Q4)
    receipt_number  TEXT,            -- Encrypted Base64
    amount_paid     TEXT,            -- Encrypted Base64
    tax_deducted    TEXT,            -- Encrypted Base64
    tax_deposited   TEXT,            -- Encrypted Base64
    challan_number  TEXT,            -- Encrypted Base64
    bsr_code        TEXT,            -- Encrypted Base64
    challan_date    TEXT             -- Encrypted Base64
);

CREATE INDEX IF NOT EXISTS idx_tds_form16 ON tds_details(form16_id);

-- 9. QR Code table
CREATE TABLE IF NOT EXISTS qr_code (
    qr_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id INTEGER UNIQUE NOT NULL REFERENCES employee(employee_id) ON DELETE CASCADE,
    qr_value    TEXT NOT NULL            -- HMAC-signed Base64 payload
);

CREATE INDEX IF NOT EXISTS idx_qr_value ON qr_code(qr_value);

-- 10. Managers table
CREATE TABLE IF NOT EXISTS managers (
    manager_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,       -- bcrypt hash
    display_name    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
