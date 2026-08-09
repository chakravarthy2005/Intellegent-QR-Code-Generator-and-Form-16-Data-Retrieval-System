"""
Multi-step Form 16 wizard - 8 steps covering all Form 16 data.
"""
import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_DANGER, COLOR_SUCCESS,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_SUBHEADING, CORNER_RADIUS, BUTTON_HEIGHT
)
from ui.components.form_fields import LabeledEntry, LabeledDropdown, SectionHeader, FormCard


STEPS = [
    ("Personal Info", "Your basic details"),
    ("Employer", "Company information"),
    ("Form 16 Dates", "Employment period"),
    ("Salary", "Salary breakdown"),
    ("Other Income", "Additional income"),
    ("Deductions", "Section 80 deductions"),
    ("Tax Details", "Tax computation"),
    ("TDS Details", "Tax deducted at source"),
]

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]   # VARCHAR(5) limit in tds_details.quarter
FY_OPTIONS = [f"FY {y}-{y+1}" for y in range(2020, 2026)]
AY_OPTIONS = [f"AY {y+1}-{y+2}" for y in range(2020, 2026)]


class Form16Wizard(ctk.CTkFrame):
    """Multi-step wizard to enter all Form 16 data."""

    def __init__(self, master, employer_list: list, on_submit: callable, on_back: callable):
        super().__init__(master, fg_color=COLOR_BG)
        self.employer_list = employer_list  # [{"employer_id": ..., "employer_name": ...}]
        self.on_submit = on_submit
        self.on_back = on_back
        self._current_step = 0
        self._pages: list[ctk.CTkFrame] = []
        self._step_indicators: list[ctk.CTkLabel] = []
        self._form_data = {}
        self._build_layout()
        self._build_all_steps()
        self._show_step(0)

    # ---- Layout -------------------------------------------------------------

    def _build_layout(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=60, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", font=FONT_SMALL, fg_color="transparent",
            hover_color=COLOR_SURFACE_2, text_color=COLOR_TEXT_MUTED,
            width=80, height=32, command=self.on_back
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkLabel(
            top, text="Form 16 Registration Wizard",
            font=FONT_SUBHEADING, text_color=COLOR_TEXT
        ).pack(side="left", padx=8, pady=14)

        # Step progress bar
        self._progress_bar = ctk.CTkProgressBar(
            top, width=200, height=6,
            progress_color=COLOR_PRIMARY, fg_color=COLOR_BORDER
        )
        self._progress_bar.pack(side="right", padx=24, pady=22)
        self._progress_bar.set(0)

        self._step_label = ctk.CTkLabel(
            top, text="Step 1 of 8", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self._step_label.pack(side="right", padx=(0, 8), pady=22)

        # Main area: sidebar steps + content
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # Left sidebar
        self._sidebar = ctk.CTkFrame(main, fg_color=COLOR_SURFACE, width=200, corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self._sidebar, text="STEPS", font=(FONT_SMALL[0], 10, "bold"),
            text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(20, 8))

        self._step_buttons: list[ctk.CTkFrame] = []
        for i, (step_name, step_desc) in enumerate(STEPS):
            btn_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent", cursor="arrow")
            btn_frame.pack(fill="x", padx=12, pady=2)

            num_label = ctk.CTkLabel(
                btn_frame, text=str(i + 1),
                font=(FONT_SMALL[0], 11, "bold"),
                width=26, height=26,
                fg_color=COLOR_BORDER,
                corner_radius=13,
                text_color=COLOR_TEXT_MUTED
            )
            num_label.pack(side="left", padx=(8, 10), pady=8)

            text_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="y", pady=8)

            ctk.CTkLabel(
                text_frame, text=step_name,
                font=(FONT_SMALL[0], 12, "normal"),
                text_color=COLOR_TEXT_MUTED, anchor="w"
            ).pack(anchor="w")

            self._step_buttons.append((btn_frame, num_label))

        # Content area
        self._content_area = ctk.CTkFrame(main, fg_color=COLOR_BG)
        self._content_area.pack(side="right", fill="both", expand=True)

        # Bottom nav bar
        self._nav_bar = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=72, corner_radius=0)
        self._nav_bar.pack(fill="x", side="bottom")
        self._nav_bar.pack_propagate(False)

        self._back_btn = ctk.CTkButton(
            self._nav_bar, text="← Previous", font=FONT_BODY,
            fg_color="transparent", hover_color=COLOR_SURFACE_2,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT, height=40, width=140,
            command=self._prev_step
        )
        self._back_btn.pack(side="left", padx=24, pady=16)

        self._next_btn = ctk.CTkButton(
            self._nav_bar, text="Next →", font=(FONT_BODY[0], 14, "bold"),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER if hasattr(__builtins__, 'COLOR_PRIMARY_HOVER') else "#00B894",
            text_color="#0D1117", height=40, width=160,
            command=self._next_step
        )
        self._next_btn.pack(side="right", padx=24, pady=16)

    # ---- Step Building ------------------------------------------------------

    def _build_all_steps(self):
        for i in range(len(STEPS)):
            page = ctk.CTkScrollableFrame(
                self._content_area, fg_color=COLOR_BG,
                scrollbar_button_color=COLOR_BORDER,
                scrollbar_button_hover_color=COLOR_PRIMARY
            )
            self._pages.append(page)
            builder = getattr(self, f"_build_step_{i+1}")
            builder(page)

    def _build_step_1(self, page):
        """Personal Information"""
        self._pad_page(page, "Personal Information", "Fill in your personal details below")
        card = FormCard(page, "Basic Details")
        card.pack(fill="x", padx=32, pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        self._name = LabeledEntry(inner, "Full Name *", "John Doe", width=500)
        self._name.pack(fill="x", pady=(0, 12))
        self._pan = LabeledEntry(inner, "PAN Number *", "ABCDE1234F", width=500)
        self._pan.pack(fill="x", pady=(0, 12))
        self._ref_num = LabeledEntry(inner, "Reference Number", "REF-12345", width=500)
        self._ref_num.pack(fill="x", pady=(0, 12))

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        self._email = LabeledEntry(row1, "Email Address *", "you@company.com", width=240)
        self._email.pack(side="left", padx=(0, 16))
        self._mobile = LabeledEntry(row1, "Mobile Number", "9876543210", width=240)
        self._mobile.pack(side="left")

        self._address = LabeledEntry(inner, "Address", "123 Main Street", width=500)
        self._address.pack(fill="x", pady=(0, 12))

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        self._city = LabeledEntry(row2, "City", "Mumbai", width=240)
        self._city.pack(side="left", padx=(0, 16))
        self._pincode = LabeledEntry(row2, "PIN Code", "400001", width=240)
        self._pincode.pack(side="left")

        card2 = FormCard(page, "Account Security")
        card2.pack(fill="x", padx=32, pady=(0, 32))
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(padx=20, pady=(0, 20), fill="x")
        self._password = LabeledEntry(inner2, "Create Password *", "Min 8 characters", show="*", width=500)
        self._password.pack(fill="x", pady=(0, 12))
        self._confirm_pwd = LabeledEntry(inner2, "Confirm Password *", "Re-enter password", show="*", width=500)
        self._confirm_pwd.pack(fill="x")

    def _build_step_2(self, page):
        """Employer Details"""
        self._pad_page(page, "Employer Information", "Select or enter your employer details")
        card = FormCard(page, "Company Details")
        card.pack(fill="x", padx=32, pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        employer_names = [e.get("employer_name_display", e.get("employer_id", "Unknown")) for e in self.employer_list]
        if not employer_names:
            employer_names = ["No employers found - add one below"]

        self._employer_choice = LabeledDropdown(inner, "Select Employer *", employer_names, width=500)
        self._employer_choice.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(inner, text="— OR ADD NEW EMPLOYER —", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=8)

        self._new_employer_name = LabeledEntry(inner, "Employer Name", "ABC Pvt Ltd", width=500)
        self._new_employer_name.pack(fill="x", pady=(0, 12))
        self._new_employer_pan = LabeledEntry(inner, "Employer PAN", "AAAPL1234C", width=500)
        self._new_employer_pan.pack(fill="x", pady=(0, 12))
        self._new_employer_tan = LabeledEntry(inner, "TAN Number", "MUMA12345B", width=500)
        self._new_employer_tan.pack(fill="x", pady=(0, 12))
        self._new_employer_addr = LabeledEntry(inner, "Employer Address", "Corporate Office, Mumbai", width=500)
        self._new_employer_addr.pack(fill="x", pady=(0, 12))

    def _build_step_3(self, page):
        """Form 16 Dates"""
        self._pad_page(page, "Form 16 Period", "Specify the financial year and employment period")
        card = FormCard(page, "Financial Year")
        card.pack(fill="x", padx=32, pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))
        self._financial_year = LabeledDropdown(row, "Financial Year *", FY_OPTIONS, width=240)
        self._financial_year.pack(side="left", padx=(0, 16))
        self._assessment_year = LabeledDropdown(row, "Assessment Year *", AY_OPTIONS, width=240)
        self._assessment_year.pack(side="left")

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        self._emp_from = LabeledEntry(row2, "Employment From", "01-04-2024", width=240)
        self._emp_from.pack(side="left", padx=(0, 16))
        self._emp_to = LabeledEntry(row2, "Employment To", "31-03-2025", width=240)
        self._emp_to.pack(side="left")

    def _build_step_4(self, page):
        """Salary Details"""
        self._pad_page(page, "Salary Details", "Enter your salary breakdown for the year")
        card = FormCard(page, "Income from Salary")
        card.pack(fill="x", padx=32, pady=(0, 32))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        fields = [
            ("_gross_salary", "Gross Salary (₹)", "1200000"),
            ("_perquisites", "Perquisites (₹)", "0"),
            ("_total_salary", "Total Salary (₹)", "1200000"),
            ("_hra_exemption", "HRA Exemption (₹)", "120000"),
            ("_travel_allowance", "Travel Allowance (₹)", "19200"),
            ("_standard_deduction", "Standard Deduction (₹)", "50000"),
            ("_professional_tax", "Professional Tax (₹)", "2400"),
            ("_total_after_exemptions", "Total Salary after Exemptions (₹)", "1008400"),
        ]
        for attr, label, placeholder in fields:
            entry = LabeledEntry(inner, label, placeholder, width=500)
            entry.pack(fill="x", pady=(0, 10))
            setattr(self, attr, entry)

    def _build_step_5(self, page):
        """Other Income"""
        self._pad_page(page, "Other Income", "Income from house property and other sources")
        card = FormCard(page, "Income Details")
        card.pack(fill="x", padx=32, pady=(0, 32))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        self._house_property = LabeledEntry(inner, "Income from House Property (₹)", "0", width=500)
        self._house_property.pack(fill="x", pady=(0, 12))
        self._other_sources = LabeledEntry(inner, "Income from Other Sources (₹)", "0", width=500)
        self._other_sources.pack(fill="x", pady=(0, 12))
        self._total_other = LabeledEntry(inner, "Total Other Income (₹)", "0", width=500)
        self._total_other.pack(fill="x")

    def _build_step_6(self, page):
        """Deductions"""
        self._pad_page(page, "Deductions Under Chapter VI-A", "Section 80 deductions")
        card = FormCard(page, "Tax Deductions")
        card.pack(fill="x", padx=32, pady=(0, 32))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        ded_fields = [
            ("_d80c", "Section 80C (PF, LIC, ELSS etc.) (₹)", "150000"),
            ("_d80ccc", "Section 80CCC (Pension fund) (₹)", "0"),
            ("_d80ccd1", "Section 80CCD(1) (NPS Employee) (₹)", "0"),
            ("_d80ccd1b", "Section 80CCD(1B) (NPS Additional) (₹)", "50000"),
            ("_d80ccd2", "Section 80CCD(2) (NPS Employer) (₹)", "0"),
            ("_d80d", "Section 80D (Health Insurance) (₹)", "25000"),
            ("_d80e", "Section 80E (Education Loan) (₹)", "0"),
            ("_d80g", "Section 80G (Donations) (₹)", "0"),
            ("_d80tta", "Section 80TTA (Savings Interest) (₹)", "10000"),
            ("_d_other", "Other Deductions (₹)", "0"),
            ("_d_total", "Total Deductions (₹)", "235000"),
        ]
        for attr, label, placeholder in ded_fields:
            entry = LabeledEntry(inner, label, placeholder, width=500)
            entry.pack(fill="x", pady=(0, 8))
            setattr(self, attr, entry)

    def _build_step_7(self, page):
        """Tax Details"""
        self._pad_page(page, "Tax Computation", "Income tax calculation summary")
        card = FormCard(page, "Tax Details")
        card.pack(fill="x", padx=32, pady=(0, 32))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=(0, 20), fill="x")

        tax_fields = [
            ("_gross_total_income", "Gross Total Income (₹)", "1008400"),
            ("_taxable_income", "Taxable Income (₹)", "773400"),
            ("_income_tax", "Income Tax (₹)", "55020"),
            ("_rebate_87a", "Rebate u/s 87A (₹)", "0"),
            ("_surcharge", "Surcharge (₹)", "0"),
            ("_health_edu_cess", "Health & Education Cess (₹)", "2201"),
            ("_tax_payable", "Tax Payable (₹)", "57221"),
            ("_relief_89", "Relief u/s 89 (₹)", "0"),
            ("_net_tax_payable", "Net Tax Payable (₹)", "57221"),
        ]
        for attr, label, placeholder in tax_fields:
            entry = LabeledEntry(inner, label, placeholder, width=500)
            entry.pack(fill="x", pady=(0, 8))
            setattr(self, attr, entry)

    def _build_step_8(self, page):
        """TDS Details (4 quarters)"""
        self._pad_page(page, "TDS Details", "Tax deducted at source - quarterly breakdown")
        self._tds_entries = []
        for qi, quarter in enumerate(QUARTERS):
            card = FormCard(page, quarter)
            card.pack(fill="x", padx=32, pady=(0, 16))
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=20, pady=(0, 20), fill="x")

            row1 = ctk.CTkFrame(inner, fg_color="transparent")
            row1.pack(fill="x", pady=(0, 8))
            receipt = LabeledEntry(row1, "Receipt Number", "RCPT-001", width=240)
            receipt.pack(side="left", padx=(0, 16))
            challan_no = LabeledEntry(row1, "Challan Number", "CH-001", width=240)
            challan_no.pack(side="left")

            row2 = ctk.CTkFrame(inner, fg_color="transparent")
            row2.pack(fill="x", pady=(0, 8))
            amount_paid = LabeledEntry(row2, "Amount Paid (₹)", "300000", width=156)
            amount_paid.pack(side="left", padx=(0, 8))
            tax_deducted = LabeledEntry(row2, "Tax Deducted (₹)", "14305", width=156)
            tax_deducted.pack(side="left", padx=(0, 8))
            tax_deposited = LabeledEntry(row2, "Tax Deposited (₹)", "14305", width=156)
            tax_deposited.pack(side="left")

            row3 = ctk.CTkFrame(inner, fg_color="transparent")
            row3.pack(fill="x")
            bsr_code = LabeledEntry(row3, "BSR Code", "0010001", width=240)
            bsr_code.pack(side="left", padx=(0, 16))
            challan_date = LabeledEntry(row3, "Challan Date", "15-06-2024", width=240)
            challan_date.pack(side="left")

            quarter_key = ["Q1", "Q2", "Q3", "Q4"][qi]
            self._tds_entries.append({
                "quarter": quarter_key,
                "receipt_number": receipt,
                "challan_number": challan_no,
                "amount_paid": amount_paid,
                "tax_deducted": tax_deducted,
                "tax_deposited": tax_deposited,
                "bsr_code": bsr_code,
                "challan_date": challan_date,
            })

    # ---- Step Navigation ----------------------------------------------------

    def _show_step(self, index: int):
        for page in self._pages:
            page.pack_forget()
        self._pages[index].pack(fill="both", expand=True)

        # Update sidebar indicators
        for i, (btn_frame, num_label) in enumerate(self._step_buttons):
            if i < index:
                num_label.configure(fg_color=COLOR_SUCCESS, text_color="#0D1117", text="✓")
                btn_frame.configure(fg_color=COLOR_SURFACE_2)
            elif i == index:
                num_label.configure(fg_color=COLOR_PRIMARY, text_color="#0D1117", text=str(i + 1))
                btn_frame.configure(fg_color=COLOR_SURFACE_2)
            else:
                num_label.configure(fg_color=COLOR_BORDER, text_color=COLOR_TEXT_MUTED, text=str(i + 1))
                btn_frame.configure(fg_color="transparent")

        # Update progress
        self._progress_bar.set((index + 1) / len(STEPS))
        self._step_label.configure(text=f"Step {index + 1} of {len(STEPS)}")

        # Buttons
        self._back_btn.configure(state="normal" if index > 0 else "disabled")
        if index == len(STEPS) - 1:
            self._next_btn.configure(text="✓ Submit & Generate QR", fg_color=COLOR_SECONDARY,
                                     hover_color="#6D28D9", text_color="#FFFFFF")
        else:
            self._next_btn.configure(text="Next →", fg_color=COLOR_PRIMARY,
                                     hover_color="#00B894", text_color="#0D1117")

    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._show_step(self._current_step)

    def _next_step(self):
        if self._current_step < len(STEPS) - 1:
            self._current_step += 1
            self._show_step(self._current_step)
        else:
            self._collect_and_submit()

    def _collect_and_submit(self):
        """Collect all form data and call on_submit."""
        # Determine employer
        employer_id = None
        new_employer_data = None
        if self._new_employer_name.get():
            new_employer_data = {
                "name": self._new_employer_name.get(),
                "pan": self._new_employer_pan.get(),
                "tan": self._new_employer_tan.get(),
                "address": self._new_employer_addr.get(),
            }
        else:
            sel = self._employer_choice.get()
            for emp in self.employer_list:
                if emp.get("employer_name_display", "") == sel or emp.get("employer_id") == sel:
                    employer_id = emp["employer_id"]
                    break

        form_data = {
            "personal": {
                "name": self._name.get(),
                "pan": self._pan.get(),
                "reference_number": self._ref_num.get(),
                "email": self._email.get(),
                "mobile_number": self._mobile.get(),
                "address": self._address.get(),
                "city": self._city.get(),
                "pin_code": self._pincode.get(),
                "password": self._password.get(),
                "employer_id": employer_id,
            },
            "new_employer": new_employer_data,
            "form16": {
                "financial_year": self._financial_year.get(),
                "assessment_year": self._assessment_year.get(),
                "employment_from": self._emp_from.get(),
                "employment_to": self._emp_to.get(),
            },
            "salary": {
                "gross_salary": self._gross_salary.get(),
                "perquisites": self._perquisites.get(),
                "total_salary": self._total_salary.get(),
                "hra_exemption": self._hra_exemption.get(),
                "travel_allowance": self._travel_allowance.get(),
                "standard_deduction": self._standard_deduction.get(),
                "professional_tax": self._professional_tax.get(),
                "total_salary_after_exemptions": self._total_after_exemptions.get(),
            },
            "other_income": {
                "house_property_income": self._house_property.get(),
                "other_sources_income": self._other_sources.get(),
                "total_other_income": self._total_other.get(),
            },
            "deductions": {
                "deduction_80c": self._d80c.get(),
                "deduction_80ccc": self._d80ccc.get(),
                "deduction_80ccd1": self._d80ccd1.get(),
                "deduction_80ccd1b": self._d80ccd1b.get(),
                "deduction_80ccd2": self._d80ccd2.get(),
                "deduction_80d": self._d80d.get(),
                "deduction_80e": self._d80e.get(),
                "deduction_80g": self._d80g.get(),
                "deduction_80tta": self._d80tta.get(),
                "other_deductions": self._d_other.get(),
                "total_deductions": self._d_total.get(),
            },
            "tax": {
                "gross_total_income": self._gross_total_income.get(),
                "taxable_income": self._taxable_income.get(),
                "income_tax": self._income_tax.get(),
                "rebate_87a": self._rebate_87a.get(),
                "surcharge": self._surcharge.get(),
                "health_education_cess": self._health_edu_cess.get(),
                "tax_payable": self._tax_payable.get(),
                "relief_89": self._relief_89.get(),
                "net_tax_payable": self._net_tax_payable.get(),
            },
            "tds": [
                {
                    "quarter": e["quarter"],
                    "receipt_number": e["receipt_number"].get(),
                    "challan_number": e["challan_number"].get(),
                    "amount_paid": e["amount_paid"].get(),
                    "tax_deducted": e["tax_deducted"].get(),
                    "tax_deposited": e["tax_deposited"].get(),
                    "bsr_code": e["bsr_code"].get(),
                    "challan_date": e["challan_date"].get(),
                }
                for e in self._tds_entries
            ],
        }
        self._next_btn.configure(state="disabled", text="Submitting...")
        self.after(50, lambda: self.on_submit(form_data))

    # ---- Helpers ------------------------------------------------------------

    def _pad_page(self, page, title: str, subtitle: str):
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 20))
        ctk.CTkLabel(header, text=title, font=FONT_HEADING, text_color=COLOR_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(header, text=subtitle, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))
