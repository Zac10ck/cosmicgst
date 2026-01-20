"""Reports screen"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date, timedelta
# Date entry uses simple CTkEntry (no tkcalendar dependency needed)
from services.invoice_service import InvoiceService
from services.stock_service import StockService
from services.gstr1_export import GSTR1Exporter
from utils.formatters import format_currency, format_date


class ReportsFrame(ctk.CTkFrame):
    """Reports and exports"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.invoice_service = InvoiceService()
        self.stock_service = StockService()
        self.gstr1_exporter = GSTR1Exporter()

        self._create_widgets()

    def _create_widgets(self):
        """Create reports screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="Reports",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Reports tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("Sales Report")
        self.tabview.add("GST Report")
        self.tabview.add("Stock Report")
        self.tabview.add("GSTR-1 Export")

        self._create_sales_tab()
        self._create_gst_tab()
        self._create_stock_tab()
        self._create_gstr1_tab()

    def _create_sales_tab(self):
        """Create sales report tab"""
        tab = self.tabview.tab("Sales Report")
        tab.grid_columnconfigure(0, weight=1)

        # Date selection
        date_frame = ctk.CTkFrame(tab, fg_color="transparent")
        date_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(date_frame, text="Date:").pack(side="left", padx=(0, 10))

        self.sales_date_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.sales_date_entry = ctk.CTkEntry(
            date_frame,
            textvariable=self.sales_date_var,
            width=120
        )
        self.sales_date_entry.pack(side="left")

        ctk.CTkButton(
            date_frame,
            text="Today",
            width=60,
            command=lambda: self.sales_date_var.set(date.today().strftime("%Y-%m-%d"))
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            date_frame,
            text="Generate",
            command=self._generate_sales_report
        ).pack(side="left", padx=10)

        # Results
        self.sales_result = ctk.CTkFrame(tab)
        self.sales_result.pack(fill="both", expand=True, pady=10)

    def _create_gst_tab(self):
        """Create GST report tab"""
        tab = self.tabview.tab("GST Report")
        tab.grid_columnconfigure(0, weight=1)

        # Date range
        date_frame = ctk.CTkFrame(tab, fg_color="transparent")
        date_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(date_frame, text="From:").pack(side="left", padx=(0, 5))

        # Default to start of month
        month_start = date.today().replace(day=1)
        self.gst_from_var = ctk.StringVar(value=month_start.strftime("%Y-%m-%d"))
        ctk.CTkEntry(date_frame, textvariable=self.gst_from_var, width=100).pack(side="left")

        ctk.CTkLabel(date_frame, text="To:").pack(side="left", padx=(15, 5))
        self.gst_to_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(date_frame, textvariable=self.gst_to_var, width=100).pack(side="left")

        ctk.CTkButton(
            date_frame,
            text="Generate",
            command=self._generate_gst_report
        ).pack(side="left", padx=15)

        # Results
        self.gst_result = ctk.CTkFrame(tab)
        self.gst_result.pack(fill="both", expand=True, pady=10)

    def _create_stock_tab(self):
        """Create stock report tab"""
        tab = self.tabview.tab("Stock Report")
        tab.grid_columnconfigure(0, weight=1)

        # Actions
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            action_frame,
            text="Refresh",
            command=self._generate_stock_report
        ).pack(side="left")

        ctk.CTkButton(
            action_frame,
            text="Show Low Stock Only",
            fg_color="orange",
            command=self._show_low_stock
        ).pack(side="left", padx=10)

        # Results
        self.stock_result = ctk.CTkScrollableFrame(tab)
        self.stock_result.pack(fill="both", expand=True, pady=10)

    def _create_gstr1_tab(self):
        """Create GSTR-1 export tab"""
        tab = self.tabview.tab("GSTR-1 Export")

        # Info
        ctk.CTkLabel(
            tab,
            text="Export GSTR-1 JSON for GST Portal Upload",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 20))

        # Date range
        date_frame = ctk.CTkFrame(tab, fg_color="transparent")
        date_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(date_frame, text="Period From:").pack(side="left", padx=(0, 5))

        month_start = date.today().replace(day=1)
        self.gstr1_from_var = ctk.StringVar(value=month_start.strftime("%Y-%m-%d"))
        ctk.CTkEntry(date_frame, textvariable=self.gstr1_from_var, width=100).pack(side="left")

        ctk.CTkLabel(date_frame, text="To:").pack(side="left", padx=(15, 5))
        self.gstr1_to_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(date_frame, textvariable=self.gstr1_to_var, width=100).pack(side="left")

        # Summary
        self.gstr1_summary = ctk.CTkFrame(tab)
        self.gstr1_summary.pack(fill="both", expand=True, pady=10)

        # Export button
        ctk.CTkButton(
            tab,
            text="Preview Summary",
            command=self._preview_gstr1
        ).pack(pady=5)

        ctk.CTkButton(
            tab,
            text="Export JSON File",
            fg_color="green",
            command=self._export_gstr1
        ).pack(pady=10)

    def _generate_sales_report(self):
        """Generate sales report"""
        try:
            sales_date = date.fromisoformat(self.sales_date_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        report = self.invoice_service.get_daily_sales(sales_date)

        # Clear and display
        for widget in self.sales_result.winfo_children():
            widget.destroy()

        # Summary
        ctk.CTkLabel(
            self.sales_result,
            text=f"Sales Report for {format_date(sales_date)}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 20))

        info_frame = ctk.CTkFrame(self.sales_result, fg_color="transparent")
        info_frame.pack(fill="x", padx=20)

        data = [
            ("Total Sales:", format_currency(report['total_sales'], "")),
            ("Total Tax:", format_currency(report['total_tax'], "")),
            ("Invoice Count:", str(report['invoice_count'])),
        ]

        for label, value in data:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=label, width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Payment breakdown
        if report['payment_breakdown']:
            ctk.CTkLabel(
                self.sales_result,
                text="Payment Breakdown",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(20, 10))

            for mode, amount in report['payment_breakdown'].items():
                row = ctk.CTkFrame(self.sales_result, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=mode, width=150, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=format_currency(amount, "")).pack(side="left")

    def _generate_gst_report(self):
        """Generate GST report"""
        try:
            from_date = date.fromisoformat(self.gst_from_var.get())
            to_date = date.fromisoformat(self.gst_to_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        report = self.invoice_service.get_gst_summary(from_date, to_date)

        # Clear and display
        for widget in self.gst_result.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.gst_result,
            text=f"GST Summary: {format_date(from_date)} to {format_date(to_date)}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 20))

        # Summary
        data = [
            ("Total Taxable Value:", format_currency(report['total_taxable'], "")),
            ("Total CGST:", format_currency(report['total_cgst'], "")),
            ("Total SGST:", format_currency(report['total_sgst'], "")),
            ("Total IGST:", format_currency(report['total_igst'], "")),
            ("Total Tax:", format_currency(report['total_tax'], "")),
        ]

        for label, value in data:
            row = ctk.CTkFrame(self.gst_result, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=label, width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(weight="bold")).pack(side="left")

    def _generate_stock_report(self):
        """Generate stock report"""
        self._show_stock_list(self.stock_service.get_stock_report())

    def _show_low_stock(self):
        """Show only low stock items"""
        report = self.stock_service.get_stock_report()
        low_stock = [item for item in report if item['is_low']]
        self._show_stock_list(low_stock)

    def _show_stock_list(self, items):
        """Display stock list"""
        for widget in self.stock_result.winfo_children():
            widget.destroy()

        # Summary
        total_value = sum(item['value'] for item in items)
        ctk.CTkLabel(
            self.stock_result,
            text=f"Total Stock Value: {format_currency(total_value, '')}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        # Headers
        header_frame = ctk.CTkFrame(self.stock_result, fg_color=("gray80", "gray30"))
        header_frame.pack(fill="x", padx=5, pady=(10, 5))

        for col, text in enumerate(['Product', 'Stock', 'Value', 'Status']):
            ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(weight="bold"),
                width=120
            ).grid(row=0, column=col, padx=10, pady=8)

        # Items
        for item in items:
            row = ctk.CTkFrame(self.stock_result, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)

            ctk.CTkLabel(row, text=item['name'][:25], width=120, anchor="w").grid(row=0, column=0, padx=10)
            ctk.CTkLabel(row, text=f"{item['stock_qty']} {item['unit']}", width=120).grid(row=0, column=1, padx=10)
            ctk.CTkLabel(row, text=format_currency(item['value'], ""), width=120).grid(row=0, column=2, padx=10)

            status_color = "red" if item['is_low'] else "green"
            status_text = "LOW" if item['is_low'] else "OK"
            ctk.CTkLabel(row, text=status_text, width=120, text_color=status_color).grid(row=0, column=3, padx=10)

    def _preview_gstr1(self):
        """Preview GSTR-1 summary"""
        try:
            from_date = date.fromisoformat(self.gstr1_from_var.get())
            to_date = date.fromisoformat(self.gstr1_to_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format")
            return

        summary = self.gstr1_exporter.get_gstr1_summary(from_date, to_date)

        for widget in self.gstr1_summary.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.gstr1_summary,
            text="GSTR-1 Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        data = summary['summary']
        info = [
            f"Total Invoices: {data['total_invoices']}",
            f"Total Taxable: {format_currency(data['total_taxable'], '')}",
            f"Total CGST: {format_currency(data['total_cgst'], '')}",
            f"Total SGST: {format_currency(data['total_sgst'], '')}",
            f"Total Value: {format_currency(data['total_value'], '')}",
        ]

        for text in info:
            ctk.CTkLabel(self.gstr1_summary, text=text).pack(pady=2)

    def _export_gstr1(self):
        """Export GSTR-1 JSON"""
        try:
            from_date = date.fromisoformat(self.gstr1_from_var.get())
            to_date = date.fromisoformat(self.gstr1_to_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format")
            return

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfilename=f"GSTR1_{from_date.strftime('%Y%m')}.json"
        )

        if filename:
            self.gstr1_exporter.export_gstr1(from_date, to_date, filename)
            messagebox.showinfo("Success", f"GSTR-1 exported to:\n{filename}")

    def refresh(self):
        """Refresh reports"""
        pass
