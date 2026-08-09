-- ============================================================
-- Form 16 QR Scanner - SQL Schema Alteration Script
-- Run this in your Supabase SQL Editor to adapt your tables
-- to support encryption and user portals!
-- ============================================================

-- 1. Alter EMPLOYER columns to support encrypted Base64 strings
ALTER TABLE employer ALTER COLUMN employer_name TYPE TEXT;
ALTER TABLE employer ALTER COLUMN pan TYPE TEXT;
ALTER TABLE employer ALTER COLUMN tan TYPE TEXT;
ALTER TABLE employer ALTER COLUMN address TYPE TEXT;

-- 2. Alter EMPLOYEE columns to support encrypted Base64 strings
ALTER TABLE employee ALTER COLUMN employee_name TYPE TEXT;
ALTER TABLE employee ALTER COLUMN pan TYPE TEXT;
ALTER TABLE employee ALTER COLUMN reference_number TYPE TEXT;
ALTER TABLE employee ALTER COLUMN address TYPE TEXT;
ALTER TABLE employee ALTER COLUMN city TYPE TEXT;
ALTER TABLE employee ALTER COLUMN pin_code TYPE TEXT;
ALTER TABLE employee ALTER COLUMN email TYPE TEXT;
ALTER TABLE employee ALTER COLUMN mobile_number TYPE TEXT;

-- Add security and portal columns to EMPLOYEE table
ALTER TABLE employee ADD COLUMN IF NOT EXISTS email_hash TEXT UNIQUE;
ALTER TABLE employee ADD COLUMN IF NOT EXISTS hashed_employee_id TEXT UNIQUE;
ALTER TABLE employee ADD COLUMN IF NOT EXISTS id_salt TEXT;
ALTER TABLE employee ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_employee_email_hash ON employee(email_hash);
CREATE INDEX IF NOT EXISTS idx_employee_hashed_id ON employee(hashed_employee_id);

-- 3. Alter FORM16 columns to support encrypted Base64 strings
ALTER TABLE form16 ALTER COLUMN financial_year TYPE TEXT;
ALTER TABLE form16 ALTER COLUMN assessment_year TYPE TEXT;
ALTER TABLE form16 ALTER COLUMN employment_from TYPE TEXT;
ALTER TABLE form16 ALTER COLUMN employment_to TYPE TEXT;

-- 4. Alter SALARY_DETAILS columns to support encrypted Base64 strings
ALTER TABLE salary_details ALTER COLUMN gross_salary TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN perquisites TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN total_salary TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN hra_exemption TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN travel_allowance TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN standard_deduction TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN professional_tax TYPE TEXT;
ALTER TABLE salary_details ALTER COLUMN total_salary_after_exemptions TYPE TEXT;

-- 5. Alter OTHER_INCOME columns to support encrypted Base64 strings
ALTER TABLE other_income ALTER COLUMN house_property_income TYPE TEXT;
ALTER TABLE other_income ALTER COLUMN other_sources_income TYPE TEXT;
ALTER TABLE employer ALTER COLUMN address TYPE TEXT;
ALTER TABLE other_income ALTER COLUMN total_other_income TYPE TEXT;

-- 6. Alter DEDUCTIONS columns to support encrypted Base64 strings
ALTER TABLE deductions ALTER COLUMN deduction_80c TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80ccc TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80ccd1 TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80ccd1b TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80ccd2 TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80d TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80e TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80g TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN deduction_80tta TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN other_deductions TYPE TEXT;
ALTER TABLE deductions ALTER COLUMN total_deductions TYPE TEXT;

-- 7. Alter TAX_DETAILS columns to support encrypted Base64 strings
ALTER TABLE tax_details ALTER COLUMN gross_total_income TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN taxable_income TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN income_tax TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN rebate_87a TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN surcharge TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN health_education_cess TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN tax_payable TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN relief_89 TYPE TEXT;
ALTER TABLE tax_details ALTER COLUMN net_tax_payable TYPE TEXT;

-- 8. Alter TDS_DETAILS columns to support encrypted Base64 strings
ALTER TABLE tds_details ALTER COLUMN receipt_number TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN amount_paid TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN tax_deducted TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN tax_deposited TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN challan_number TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN bsr_code TYPE TEXT;
ALTER TABLE tds_details ALTER COLUMN challan_date TYPE TEXT;

-- 9. Create QR_CODES table (using identity integer ID)
CREATE TABLE IF NOT EXISTS qr_codes (
    qr_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id INTEGER UNIQUE NOT NULL REFERENCES employee(employee_id) ON DELETE CASCADE,
    qr_value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Create MANAGERS table (using identity integer ID)
CREATE TABLE IF NOT EXISTS managers (
    manager_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
