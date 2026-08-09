"""
Form 16 viewer - displays fully decrypted Form 16 data.
Formatted like an official tax document with optional editing capabilities.
"""
import customtkinter as ctk
from ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_2, COLOR_PRIMARY, COLOR_SECONDARY,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO,
    COLOR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_SUBHEADING, FONT_MONO, CORNER_RADIUS, BUTTON_HEIGHT
)


def _fmt(val) -> str:
    """Format a value for display."""
    if not val:
        return "—"
    try:
        num = float(str(val).replace(",", ""))
        return f"₹ {num:,.2f}"
    except (ValueError, TypeError):
        return str(val)


def _str(val) -> str:
    return str(val) if val else "—"


class Form16ViewerPage(ctk.CTkScrollableFrame):
    """
    Full Form 16 display. Rendered from decrypted data dict.
    Supports in-app database editing for authorized editors.
    """

    def __init__(self, master, form16_data: dict, on_back: callable, can_edit: bool = False, on_save_update: callable = None):
        super().__init__(
            master, fg_color=COLOR_BG,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_PRIMARY
        )
        self.form16_data = form16_data
        self.on_back = on_back
        self.can_edit = can_edit
        self.on_save_update = on_save_update
        self._build()

    def _clear_all(self):
        for child in self.winfo_children():
            child.destroy()

    def _build(self):
        self._clear_all()
        # Top bar
        top = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12,
                           border_width=1, border_color=COLOR_BORDER)
        top.pack(fill="x", padx=24, pady=(16, 0))
        top_inner = ctk.CTkFrame(top, fg_color="transparent")
        top_inner.pack(fill="x", padx=20, pady=12)

        ctk.CTkButton(
            top_inner, text="← Back to Dashboard",
            font=FONT_SMALL, fg_color="transparent",
            hover_color=COLOR_SURFACE_2, text_color=COLOR_TEXT_MUTED,
            width=160, height=32, corner_radius=CORNER_RADIUS,
            command=self.on_back
        ).pack(side="left")

        # Security badge
        badge = ctk.CTkFrame(
            top_inner, fg_color=COLOR_SURFACE_2,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER
        )
        badge.pack(side="right")
        ctk.CTkLabel(
            badge,
            text="✅  Decrypted via Triple AES-256-GCM",
            font=FONT_SMALL, text_color=COLOR_SUCCESS
        ).pack(padx=12, pady=6)

        # Print button
        ctk.CTkButton(
            top_inner, text="🖨 Print",
            font=FONT_SMALL, fg_color=COLOR_SURFACE_2,
            hover_color=COLOR_BORDER, text_color=COLOR_TEXT,
            width=90, height=32, corner_radius=CORNER_RADIUS,
            command=self._print_form16
        ).pack(side="right", padx=(0, 10))

        # Edit button (only if can_edit is True)
        if self.can_edit:
            ctk.CTkButton(
                top_inner, text="✏️ Edit Data",
                font=(FONT_SMALL[0], 12, "bold"),
                fg_color=COLOR_PRIMARY, hover_color="#00B894", text_color="#0D1117",
                width=110, height=32, corner_radius=CORNER_RADIUS,
                command=self._open_edit_dialog
            ).pack(side="right", padx=(0, 10))

        # ---- Document header ------------------------------------------------
        doc_header = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        doc_header.pack(fill="x", padx=24, pady=(16, 0))

        hdr_inner = ctk.CTkFrame(doc_header, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=24, pady=20)

        ctk.CTkLabel(
            hdr_inner, text="FORM 16",
            font=("Segoe UI", 28, "bold"), text_color=COLOR_PRIMARY
        ).pack()
        ctk.CTkLabel(
            hdr_inner,
            text="Certificate under Section 203 of the Income-tax Act, 1961",
            font=FONT_BODY, text_color=COLOR_TEXT_MUTED
        ).pack(pady=(2, 0))

        f16 = self.form16_data.get("form16", {})
        info_row = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        info_row.pack(pady=(12, 0))
        for label, val in [
            ("Financial Year", f16.get("financial_year", "—")),
            ("Assessment Year", f16.get("assessment_year", "—")),
            ("From", f16.get("employment_from", "—")),
            ("To", f16.get("employment_to", "—")),
        ]:
            box = ctk.CTkFrame(
                info_row, fg_color=COLOR_SURFACE_2,
                corner_radius=8, border_width=1, border_color=COLOR_BORDER
            )
            box.pack(side="left", padx=8)
            ctk.CTkLabel(box, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(padx=16, pady=(8, 2))
            ctk.CTkLabel(box, text=val, font=(FONT_BODY[0], 13, "bold"), text_color=COLOR_TEXT).pack(padx=16, pady=(0, 8))

        # ---- Sections -------------------------------------------------------
        emp = self.form16_data.get("employee", {})
        employer = self.form16_data.get("employer", {})
        salary = self.form16_data.get("salary", {})
        other_income = self.form16_data.get("other_income", {})
        deductions = self.form16_data.get("deductions", {})
        tax = self.form16_data.get("tax", {})
        tds_list = self.form16_data.get("tds", [])

        # Part A — Employer Details
        self._section("PART A — EMPLOYER DETAILS", [
            ("Employer Name", _str(employer.get("employer_name"))),
            ("PAN of Employer", _str(employer.get("pan"))),
            ("TAN", _str(employer.get("tan"))),
            ("Address", _str(employer.get("address"))),
        ], COLOR_INFO)

        # Part A — Employee Details
        self._section("PART A — EMPLOYEE DETAILS", [
            ("Employee Name", _str(emp.get("employee_name"))),
            ("PAN of Employee", _str(emp.get("pan"))),
            ("Reference Number", _str(emp.get("reference_number"))),
            ("Address", _str(emp.get("address"))),
            ("City", _str(emp.get("city"))),
            ("PIN Code", _str(emp.get("pin_code"))),
            ("Email", _str(emp.get("email"))),
            ("Mobile", _str(emp.get("mobile_number"))),
        ], COLOR_SECONDARY)

        # Part B — Salary
        self._section("PART B — INCOME FROM SALARY", [
            ("Gross Salary", _fmt(salary.get("gross_salary"))),
            ("Perquisites", _fmt(salary.get("perquisites"))),
            ("Total Salary", _fmt(salary.get("total_salary"))),
            ("HRA Exemption", _fmt(salary.get("hra_exemption"))),
            ("Travel Allowance", _fmt(salary.get("travel_allowance"))),
            ("Standard Deduction", _fmt(salary.get("standard_deduction"))),
            ("Professional Tax", _fmt(salary.get("professional_tax"))),
            ("Net Salary after Exemptions", _fmt(salary.get("total_salary_after_exemptions") or salary.get("total_after_exemptions"))),
        ], COLOR_PRIMARY, highlight_last=True)

        # Other Income
        self._section("OTHER INCOME", [
            ("Income from House Property", _fmt(other_income.get("house_property_income"))),
            ("Income from Other Sources", _fmt(other_income.get("other_sources_income"))),
            ("Total Other Income", _fmt(other_income.get("total_other_income"))),
        ], COLOR_WARNING, highlight_last=True)

        # Deductions
        ded_rows = [
            ("Section 80C", _fmt(deductions.get("deduction_80c") or deductions.get("sec_80c"))),
            ("Section 80CCC", _fmt(deductions.get("deduction_80ccc") or deductions.get("sec_80ccc"))),
            ("Section 80CCD(1)", _fmt(deductions.get("deduction_80ccd1") or deductions.get("sec_80ccd_1"))),
            ("Section 80CCD(1B)", _fmt(deductions.get("deduction_80ccd1b") or deductions.get("sec_80ccd_1b"))),
            ("Section 80CCD(2)", _fmt(deductions.get("deduction_80ccd2") or deductions.get("sec_80ccd_2"))),
            ("Section 80D", _fmt(deductions.get("deduction_80d") or deductions.get("sec_80d"))),
            ("Section 80E", _fmt(deductions.get("deduction_80e") or deductions.get("sec_80e"))),
            ("Section 80G", _fmt(deductions.get("deduction_80g") or deductions.get("sec_80g"))),
            ("Section 80TTA", _fmt(deductions.get("deduction_80tta") or deductions.get("sec_80tta"))),
            ("Other Deductions", _fmt(deductions.get("other_deductions"))),
            ("Total Deductions", _fmt(deductions.get("total_deductions"))),
        ]
        self._section("CHAPTER VI-A DEDUCTIONS", ded_rows, COLOR_SECONDARY, highlight_last=True)

        # Tax Details
        tax_rows = [
            ("Gross Total Income", _fmt(tax.get("gross_total_income"))),
            ("Taxable Income", _fmt(tax.get("taxable_income"))),
            ("Income Tax", _fmt(tax.get("income_tax"))),
            ("Rebate u/s 87A", _fmt(tax.get("rebate_87a"))),
            ("Surcharge", _fmt(tax.get("surcharge"))),
            ("Health & Education Cess", _fmt(tax.get("health_education_cess") or tax.get("health_edu_cess"))),
            ("Tax Payable", _fmt(tax.get("tax_payable"))),
            ("Relief u/s 89", _fmt(tax.get("relief_89"))),
            ("Net Tax Payable", _fmt(tax.get("net_tax_payable"))),
        ]
        self._section("TAX COMPUTATION", tax_rows, COLOR_DANGER, highlight_last=True)

        # TDS Table
        self._tds_section(tds_list)

        # Footer
        footer = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        footer.pack(fill="x", padx=24, pady=(0, 24))
        ctk.CTkLabel(
            footer,
            text="🔒  This document was retrieved and decrypted using triple AES-256-GCM encryption. "
                 "Data is confidential and intended for authorized personnel only.",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
            wraplength=900, justify="center"
        ).pack(padx=24, pady=14)

    def _section(self, title: str, rows: list, accent_color: str, highlight_last: bool = False):
        card = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        card.pack(fill="x", padx=24, pady=(16, 0))

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=0, pady=0)
        ctk.CTkFrame(hdr, width=4, fg_color=accent_color, corner_radius=2).pack(
            side="left", padx=(16, 12), pady=16, fill="y"
        )
        ctk.CTkLabel(
            hdr, text=title,
            font=(FONT_SUBHEADING[0], 12, "bold"),
            text_color=accent_color, anchor="w"
        ).pack(side="left", pady=16)

        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        # Rows
        for i, (label, value) in enumerate(rows):
            is_last = (i == len(rows) - 1) and highlight_last
            row_bg = COLOR_SURFACE_2 if is_last else "transparent"

            row = ctk.CTkFrame(card, fg_color=row_bg)
            row.pack(fill="x")

            ctk.CTkLabel(
                row, text=label,
                font=FONT_SMALL if not is_last else (FONT_SMALL[0], 12, "bold"),
                text_color=COLOR_TEXT_MUTED if not is_last else COLOR_TEXT,
                anchor="w", width=280
            ).pack(side="left", padx=20, pady=10)

            ctk.CTkLabel(
                row, text=value,
                font=FONT_MONO if not is_last else ("Consolas", 13, "bold"),
                text_color=COLOR_TEXT if not is_last else accent_color,
                anchor="e"
            ).pack(side="right", padx=20, pady=10)

            if i < len(rows) - 1:
                ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        ctk.CTkFrame(card, height=1, fg_color="transparent").pack()

    def _tds_section(self, tds_list: list):
        if not tds_list:
            return

        card = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE,
            corner_radius=12, border_width=1, border_color=COLOR_BORDER
        )
        card.pack(fill="x", padx=24, pady=(16, 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkFrame(hdr, width=4, fg_color=COLOR_INFO, corner_radius=2).pack(
            side="left", padx=(16, 12), pady=16, fill="y"
        )
        ctk.CTkLabel(
            hdr, text="TDS DEDUCTED & DEPOSITED",
            font=(FONT_SUBHEADING[0], 12, "bold"),
            text_color=COLOR_INFO, anchor="w"
        ).pack(side="left", pady=16)

        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        # Table header
        cols = ["Quarter", "Receipt No.", "Amount Paid", "Tax Deducted", "Tax Deposited", "BSR Code", "Challan Date"]
        widths = [60, 100, 110, 110, 110, 90, 100]

        thead = ctk.CTkFrame(card, fg_color=COLOR_SURFACE_2)
        thead.pack(fill="x", padx=16, pady=(8, 0))
        for col, w in zip(cols, widths):
            ctk.CTkLabel(
                thead, text=col, width=w,
                font=(FONT_SMALL[0], 11, "bold"),
                text_color=COLOR_TEXT_MUTED, anchor="w"
            ).pack(side="left", padx=8, pady=8)

        for tds in tds_list:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16)

            values = [
                _str(tds.get("quarter")),
                _str(tds.get("receipt_number")),
                _fmt(tds.get("amount_paid")),
                _fmt(tds.get("tax_deducted")),
                _fmt(tds.get("tax_deposited")),
                _str(tds.get("bsr_code")),
                _str(tds.get("challan_date")),
            ]
            for val, w in zip(values, widths):
                ctk.CTkLabel(
                    row, text=val, width=w,
                    font=FONT_MONO, text_color=COLOR_TEXT, anchor="w"
                ).pack(side="left", padx=8, pady=8)

            ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=16)

        ctk.CTkFrame(card, height=8, fg_color="transparent").pack()

    def _open_edit_dialog(self):
        """Opens modal editor window to modify Form 16 figures."""
        win = ctk.CTkToplevel(self)
        win.title("Edit Form 16 Data")
        win.geometry("640x720")
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color=COLOR_BG)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="✏️  Edit Form 16 Database Record", font=FONT_HEADING, text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 10))

        emp = self.form16_data.get("employee", {})
        sal = self.form16_data.get("salary", {})
        ded = self.form16_data.get("deductions", {})
        tax = self.form16_data.get("tax", {})

        entries = {}

        def _make_field(parent, label, key_path, initial_val):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, width=220, anchor="w").pack(side="left")
            ent = ctk.CTkEntry(row, width=320, height=32)
            ent.insert(0, str(initial_val) if initial_val is not None else "")
            ent.pack(side="right")
            entries[key_path] = ent

        # Employee Section
        ctk.CTkLabel(scroll, text="Employee Details", font=(FONT_SMALL[0], 12, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", pady=(10, 4))
        _make_field(scroll, "Employee Name", "employee.employee_name", emp.get("employee_name", ""))
        _make_field(scroll, "PAN Number", "employee.pan", emp.get("pan", ""))
        _make_field(scroll, "Email Address", "employee.email", emp.get("email", ""))
        _make_field(scroll, "Mobile Number", "employee.mobile_number", emp.get("mobile_number", ""))

        # Salary Section
        ctk.CTkLabel(scroll, text="Salary Details", font=(FONT_SMALL[0], 12, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", pady=(16, 4))
        _make_field(scroll, "Gross Salary (₹)", "salary.gross_salary", sal.get("gross_salary", ""))
        _make_field(scroll, "Perquisites (₹)", "salary.perquisites", sal.get("perquisites", ""))
        _make_field(scroll, "Total Salary (₹)", "salary.total_salary", sal.get("total_salary", ""))
        _make_field(scroll, "HRA Exemption (₹)", "salary.hra_exemption", sal.get("hra_exemption", ""))
        _make_field(scroll, "Standard Deduction (₹)", "salary.standard_deduction", sal.get("standard_deduction", ""))
        _make_field(scroll, "Net Salary (₹)", "salary.total_salary_after_exemptions", sal.get("total_salary_after_exemptions", ""))

        # Deductions Section
        ctk.CTkLabel(scroll, text="Deductions", font=(FONT_SMALL[0], 12, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", pady=(16, 4))
        _make_field(scroll, "Section 80C (₹)", "deductions.deduction_80c", ded.get("deduction_80c") or ded.get("sec_80c", ""))
        _make_field(scroll, "Section 80D (₹)", "deductions.deduction_80d", ded.get("deduction_80d") or ded.get("sec_80d", ""))
        _make_field(scroll, "Total Deductions (₹)", "deductions.total_deductions", ded.get("total_deductions", ""))

        # Tax Section
        ctk.CTkLabel(scroll, text="Tax Computation", font=(FONT_SMALL[0], 12, "bold"), text_color=COLOR_PRIMARY).pack(anchor="w", pady=(16, 4))
        _make_field(scroll, "Gross Total Income (₹)", "tax.gross_total_income", tax.get("gross_total_income", ""))
        _make_field(scroll, "Taxable Income (₹)", "tax.taxable_income", tax.get("taxable_income", ""))
        _make_field(scroll, "Income Tax (₹)", "tax.income_tax", tax.get("income_tax", ""))
        _make_field(scroll, "Net Tax Payable (₹)", "tax.net_tax_payable", tax.get("net_tax_payable", ""))

        status_lbl = ctk.CTkLabel(scroll, text="", font=FONT_SMALL, text_color=COLOR_SUCCESS)
        status_lbl.pack(pady=10)

        def _save():
            updated = {
                "employee": {
                    "employee_name": entries["employee.employee_name"].get().strip(),
                    "pan": entries["employee.pan"].get().strip(),
                    "email": entries["employee.email"].get().strip(),
                    "mobile_number": entries["employee.mobile_number"].get().strip(),
                },
                "salary": {
                    "gross_salary": entries["salary.gross_salary"].get().strip(),
                    "perquisites": entries["salary.perquisites"].get().strip(),
                    "total_salary": entries["salary.total_salary"].get().strip(),
                    "hra_exemption": entries["salary.hra_exemption"].get().strip(),
                    "standard_deduction": entries["salary.standard_deduction"].get().strip(),
                    "total_salary_after_exemptions": entries["salary.total_salary_after_exemptions"].get().strip(),
                },
                "deductions": {
                    "deduction_80c": entries["deductions.deduction_80c"].get().strip(),
                    "deduction_80d": entries["deductions.deduction_80d"].get().strip(),
                    "total_deductions": entries["deductions.total_deductions"].get().strip(),
                },
                "tax": {
                    "gross_total_income": entries["tax.gross_total_income"].get().strip(),
                    "taxable_income": entries["tax.taxable_income"].get().strip(),
                    "income_tax": entries["tax.income_tax"].get().strip(),
                    "net_tax_payable": entries["tax.net_tax_payable"].get().strip(),
                }
            }

            # Update local form16_data structure
            for sec, vals in updated.items():
                if sec in self.form16_data:
                    self.form16_data[sec].update(vals)

            if callable(self.on_save_update):
                try:
                    self.on_save_update(updated)
                    status_lbl.configure(text="✅ Database updated successfully!", text_color=COLOR_SUCCESS)
                    win.after(800, lambda: (win.destroy(), self._build()))
                except Exception as ex:
                    status_lbl.configure(text=f"❌ Error updating DB: {ex}", text_color=COLOR_DANGER)
            else:
                win.destroy()
                self._build()

        ctk.CTkButton(
            scroll, text="💾 Save Changes to Database",
            font=(FONT_BODY[0], 13, "bold"),
            fg_color=COLOR_PRIMARY, hover_color="#00B894", text_color="#0D1117",
            height=40, command=_save
        ).pack(fill="x", pady=16)

    def _print_form16(self):
        """Save Form 16 as text report."""
        from tkinter import filedialog, messagebox
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
            initialfile="Form16_Report.txt"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("FORM 16 - INCOME TAX CERTIFICATE\n")
                f.write("=" * 60 + "\n\n")
                self._write_section_text(f, "FORM 16 PERIOD", self.form16_data.get("form16", {}))
                self._write_section_text(f, "EMPLOYEE DETAILS", self.form16_data.get("employee", {}))
                self._write_section_text(f, "EMPLOYER DETAILS", self.form16_data.get("employer", {}))
                self._write_section_text(f, "SALARY DETAILS", self.form16_data.get("salary", {}))
                self._write_section_text(f, "OTHER INCOME", self.form16_data.get("other_income", {}))
                self._write_section_text(f, "DEDUCTIONS", self.form16_data.get("deductions", {}))
                self._write_section_text(f, "TAX COMPUTATION", self.form16_data.get("tax", {}))
                f.write("\nTDS DETAILS\n" + "-" * 40 + "\n")
                for tds in self.form16_data.get("tds", []):
                    for k, v in tds.items():
                        f.write(f"  {k}: {v}\n")
                    f.write("\n")
            messagebox.showinfo("Saved", f"Form 16 report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _write_section_text(self, f, title, data: dict):
        f.write(f"\n{title}\n" + "-" * 40 + "\n")
        for k, v in data.items():
            f.write(f"  {k.replace('_', ' ').title()}: {v}\n")
