"""GSTR-1 JSON export for GST filing"""
import json
from datetime import date
from typing import List
from database.models import Invoice, Company
from utils.formatters import format_date


class GSTR1Exporter:
    """
    Export invoices in GSTR-1 JSON format for GST portal upload

    GSTR-1 Sections:
    - B2B: Business to Business (with GSTIN)
    - B2CL: B2C Large (> 2.5L inter-state without GSTIN)
    - B2CS: B2C Small (all other B2C)
    """

    def __init__(self):
        self.company = Company.get()

    def export_gstr1(
        self,
        start_date: date,
        end_date: date,
        output_path: str = None
    ) -> dict:
        """
        Export GSTR-1 JSON for date range

        Args:
            start_date: Start date
            end_date: End date
            output_path: Optional path to save JSON file

        Returns:
            GSTR-1 data dictionary
        """
        invoices = Invoice.get_by_date_range(start_date, end_date)

        # Separate B2B and B2C invoices
        b2b_invoices = []
        b2cs_data = {}  # Grouped by state + rate

        for inv in invoices:
            if inv.is_cancelled:
                continue

            # Check if B2B (has customer GSTIN)
            # For now, treat all as B2CS since this is retail
            self._add_to_b2cs(b2cs_data, inv)

        # Build GSTR-1 structure
        gstr1 = {
            "gstin": self.company.gstin if self.company else "",
            "fp": self._get_filing_period(start_date),  # MMYYYY
            "version": "GST3.0.4",
            "hash": "hash",
            "b2cs": self._format_b2cs(b2cs_data)
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(gstr1, f, indent=2)

        return gstr1

    def _get_filing_period(self, d: date) -> str:
        """Get filing period in MMYYYY format"""
        return d.strftime("%m%Y")

    def _add_to_b2cs(self, b2cs_data: dict, invoice: Invoice):
        """Add invoice to B2CS summary"""
        # B2CS is summarized by:
        # - Place of Supply (state code)
        # - GST Rate
        # - Supply Type (INTRA/INTER)

        state_code = "32"  # Kerala default
        supply_type = "INTRA"  # Intra-state for now

        for item in invoice.items:
            rate = item.gst_rate

            key = f"{state_code}_{rate}_{supply_type}"

            if key not in b2cs_data:
                b2cs_data[key] = {
                    "sply_ty": supply_type,
                    "pos": state_code,
                    "rt": rate,
                    "txval": 0,
                    "camt": 0,
                    "samt": 0,
                    "iamt": 0,
                    "csamt": 0  # Cess amount
                }

            b2cs_data[key]["txval"] += item.taxable_value
            b2cs_data[key]["camt"] += item.cgst
            b2cs_data[key]["samt"] += item.sgst
            b2cs_data[key]["iamt"] += item.igst

    def _format_b2cs(self, b2cs_data: dict) -> List[dict]:
        """Format B2CS data for JSON export"""
        result = []

        for key, data in b2cs_data.items():
            result.append({
                "sply_ty": data["sply_ty"],
                "pos": data["pos"],
                "rt": data["rt"],
                "txval": round(data["txval"], 2),
                "camt": round(data["camt"], 2),
                "samt": round(data["samt"], 2),
                "iamt": round(data["iamt"], 2),
                "csamt": round(data["csamt"], 2)
            })

        return result

    def get_gstr1_summary(self, start_date: date, end_date: date) -> dict:
        """
        Get GSTR-1 summary for display

        Returns summary with section-wise totals
        """
        invoices = Invoice.get_by_date_range(start_date, end_date)

        total_invoices = 0
        total_taxable = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0
        total_value = 0

        # Rate-wise summary
        rate_summary = {}

        for inv in invoices:
            if inv.is_cancelled:
                continue

            total_invoices += 1
            total_taxable += inv.subtotal
            total_cgst += inv.cgst_total
            total_sgst += inv.sgst_total
            total_igst += inv.igst_total
            total_value += inv.grand_total

            for item in inv.items:
                rate = item.gst_rate
                if rate not in rate_summary:
                    rate_summary[rate] = {
                        "taxable": 0,
                        "cgst": 0,
                        "sgst": 0,
                        "igst": 0,
                        "count": 0
                    }
                rate_summary[rate]["taxable"] += item.taxable_value
                rate_summary[rate]["cgst"] += item.cgst
                rate_summary[rate]["sgst"] += item.sgst
                rate_summary[rate]["igst"] += item.igst
                rate_summary[rate]["count"] += 1

        return {
            "period": {
                "start": format_date(start_date),
                "end": format_date(end_date)
            },
            "summary": {
                "total_invoices": total_invoices,
                "total_taxable": round(total_taxable, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2),
                "total_igst": round(total_igst, 2),
                "total_tax": round(total_cgst + total_sgst + total_igst, 2),
                "total_value": round(total_value, 2)
            },
            "rate_wise": rate_summary
        }
