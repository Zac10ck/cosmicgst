"""Reports screen"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date, timedelta
import json
# Date entry uses simple CTkEntry (no tkcalendar dependency needed)
from services.invoice_service import InvoiceService
from services.stock_service import StockService
from services.gstr1_export import GSTR1Exporter
from services.eway_bill_service import EWayBillService, TRANSPORT_MODES, EWAY_BILL_THRESHOLD
from services.excel_exporter import ExcelExporter
from database.models import Invoice, Company
from utils.formatters import format_currency, format_date


class ReportsFrame(ctk.CTkFrame):
    """Reports and exports"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.invoice_service = InvoiceService()
        self.stock_service = StockService()
        self.gstr1_exporter = GSTR1Exporter()
        self.eway_service = EWayBillService()
        self.excel_exporter = ExcelExporter()

        # Store current report data for export
        self.current_sales_report = None
        self.current_gst_report = None
        self.current_stock_report = None

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
        self.tabview.add("e-Way Bill")

        self._create_sales_tab()
        self._create_gst_tab()
        self._create_stock_tab()
        self._create_gstr1_tab()
        self._create_eway_bill_tab()

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

        ctk.CTkButton(
            date_frame,
            text="Export to Excel",
            fg_color="green",
            hover_color="darkgreen",
            command=self._export_sales_excel
        ).pack(side="left", padx=5)

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

        ctk.CTkButton(
            date_frame,
            text="Export to Excel",
            fg_color="green",
            hover_color="darkgreen",
            command=self._export_gst_excel
        ).pack(side="left", padx=5)

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

        ctk.CTkButton(
            action_frame,
            text="Export to Excel",
            fg_color="green",
            hover_color="darkgreen",
            command=self._export_stock_excel
        ).pack(side="left", padx=5)

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
        self.current_sales_report = report
        self.current_sales_invoices = Invoice.get_by_date_range(sales_date, sales_date)

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
        self.current_gst_report = report

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
        self.current_stock_report = self.stock_service.get_stock_report()
        self._show_stock_list(self.current_stock_report)

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

    def _create_eway_bill_tab(self):
        """Create e-Way Bill helper tab"""
        tab = self.tabview.tab("e-Way Bill")

        # Info header
        info_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"))
        info_frame.pack(fill="x", pady=(10, 15), padx=10)

        ctk.CTkLabel(
            info_frame,
            text="e-Way Bill Helper",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            info_frame,
            text=f"Generate e-Way Bill data for manual entry into GST portal.\ne-Way Bill is required for invoices > ₹{EWAY_BILL_THRESHOLD:,}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 10))

        # Invoice selection
        select_frame = ctk.CTkFrame(tab, fg_color="transparent")
        select_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(select_frame, text="Select Invoice:").pack(side="left", padx=(0, 10))

        self.eway_invoice_var = ctk.StringVar()
        self.eway_invoice_combo = ctk.CTkComboBox(
            select_frame,
            variable=self.eway_invoice_var,
            values=["Select an invoice..."],
            width=250,
            command=self._on_eway_invoice_select
        )
        self.eway_invoice_combo.pack(side="left")

        ctk.CTkButton(
            select_frame,
            text="Refresh List",
            width=100,
            command=self._refresh_eway_invoices
        ).pack(side="left", padx=10)

        # Transport details frame
        transport_frame = ctk.CTkFrame(tab)
        transport_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(
            transport_frame,
            text="Transport Details (for Part B)",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky="w", padx=15)

        # Transport mode
        ctk.CTkLabel(transport_frame, text="Mode:").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        self.eway_mode_var = ctk.StringVar(value="Road")
        ctk.CTkComboBox(
            transport_frame,
            variable=self.eway_mode_var,
            values=TRANSPORT_MODES,
            width=120
        ).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Vehicle number
        ctk.CTkLabel(transport_frame, text="Vehicle No:").grid(row=1, column=2, padx=15, pady=5, sticky="w")
        self.eway_vehicle_var = ctk.StringVar()
        ctk.CTkEntry(
            transport_frame,
            textvariable=self.eway_vehicle_var,
            width=120,
            placeholder_text="KL-01-AB-1234"
        ).grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Distance
        ctk.CTkLabel(transport_frame, text="Distance (km):").grid(row=2, column=0, padx=15, pady=5, sticky="w")
        self.eway_distance_var = ctk.StringVar(value="0")
        ctk.CTkEntry(
            transport_frame,
            textvariable=self.eway_distance_var,
            width=120
        ).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Transporter ID
        ctk.CTkLabel(transport_frame, text="Transporter ID:").grid(row=2, column=2, padx=15, pady=5, sticky="w")
        self.eway_transporter_var = ctk.StringVar()
        ctk.CTkEntry(
            transport_frame,
            textvariable=self.eway_transporter_var,
            width=120,
            placeholder_text="GSTIN (optional)"
        ).grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Recipient PIN
        ctk.CTkLabel(transport_frame, text="Recipient PIN:").grid(row=3, column=0, padx=15, pady=5, sticky="w")
        self.eway_pin_var = ctk.StringVar()
        ctk.CTkEntry(
            transport_frame,
            textvariable=self.eway_pin_var,
            width=120,
            placeholder_text="6-digit PIN"
        ).grid(row=3, column=1, padx=5, pady=(5, 15), sticky="w")

        # Action buttons
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkButton(
            action_frame,
            text="Generate e-Way Bill Data",
            fg_color="green",
            hover_color="darkgreen",
            command=self._generate_eway_bill
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Export as JSON",
            command=self._export_eway_json
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Save EWB Number",
            fg_color="orange",
            hover_color="darkorange",
            command=self._save_eway_number
        ).pack(side="left", padx=5)

        # Result display
        self.eway_result = ctk.CTkTextbox(tab, height=200, font=("Courier", 10))
        self.eway_result.pack(fill="both", expand=True, pady=10, padx=10)

        # Status label
        self.eway_status_label = ctk.CTkLabel(
            tab,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.eway_status_label.pack(pady=(0, 10))

        # Load invoices on init
        self._refresh_eway_invoices()

    def _refresh_eway_invoices(self):
        """Refresh invoice list for e-Way Bill"""
        from database.models import Invoice

        # Get recent invoices (last 30 days) that might need e-Way Bill
        from_date = date.today() - timedelta(days=30)
        to_date = date.today()

        invoices = Invoice.get_by_date_range(from_date, to_date)

        # Filter high-value invoices
        invoice_options = ["Select an invoice..."]
        self.eway_invoices = {}

        for inv in invoices:
            if inv.grand_total >= EWAY_BILL_THRESHOLD and not inv.is_cancelled:
                label = f"{inv.invoice_number} - ₹{inv.grand_total:,.2f} - {inv.customer_name or 'Cash'}"
                if inv.eway_bill_number:
                    label += f" [EWB: {inv.eway_bill_number}]"
                invoice_options.append(label)
                self.eway_invoices[label] = inv

        self.eway_invoice_combo.configure(values=invoice_options)

        # Show count
        count = len(invoice_options) - 1
        if count > 0:
            self.eway_status_label.configure(
                text=f"Found {count} invoice(s) requiring e-Way Bill (value > ₹{EWAY_BILL_THRESHOLD:,})"
            )
        else:
            self.eway_status_label.configure(
                text="No high-value invoices found in the last 30 days."
            )

    def _on_eway_invoice_select(self, value):
        """Handle invoice selection for e-Way Bill"""
        if value in self.eway_invoices:
            inv = self.eway_invoices[value]

            # Check requirements
            required, reason = self.eway_service.is_eway_bill_required(inv)

            self.eway_result.delete("1.0", "end")
            self.eway_result.insert("1.0", f"Invoice: {inv.invoice_number}\n")
            self.eway_result.insert("end", f"Value: ₹{inv.grand_total:,.2f}\n")
            self.eway_result.insert("end", f"Customer: {inv.customer_name or 'Cash'}\n\n")
            self.eway_result.insert("end", f"e-Way Bill Required: {'YES' if required else 'NO'}\n")
            self.eway_result.insert("end", f"Reason: {reason}\n\n")

            if inv.eway_bill_number:
                self.eway_result.insert("end", f"Existing EWB Number: {inv.eway_bill_number}\n")

            self.eway_result.insert("end", "\nClick 'Generate e-Way Bill Data' to create portal entry data.")

    def _generate_eway_bill(self):
        """Generate e-Way Bill data for selected invoice"""
        selected = self.eway_invoice_var.get()

        if selected not in self.eway_invoices:
            messagebox.showwarning("Select Invoice", "Please select an invoice first.")
            return

        invoice = self.eway_invoices[selected]

        try:
            distance = int(self.eway_distance_var.get() or 0)
        except ValueError:
            distance = 0

        # Generate e-Way Bill data
        self.current_eway_data = self.eway_service.generate_eway_bill_data(
            invoice=invoice,
            vehicle_number=self.eway_vehicle_var.get().upper(),
            transport_mode=self.eway_mode_var.get(),
            transporter_id=self.eway_transporter_var.get(),
            transport_distance=distance,
            recipient_pin=self.eway_pin_var.get()
        )

        # Display formatted data
        formatted = self.eway_service.format_for_display(self.current_eway_data)

        self.eway_result.delete("1.0", "end")
        self.eway_result.insert("1.0", formatted)

        self.eway_status_label.configure(
            text="e-Way Bill data generated. Copy above data to portal or export as JSON."
        )

    def _export_eway_json(self):
        """Export e-Way Bill data as JSON"""
        if not hasattr(self, 'current_eway_data') or not self.current_eway_data:
            messagebox.showwarning("No Data", "Please generate e-Way Bill data first.")
            return

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfilename=f"eway_bill_{self.current_eway_data.document_number.replace('/', '_')}.json"
        )

        if filename:
            json_data = self.eway_service.export_to_json(self.current_eway_data)
            with open(filename, 'w') as f:
                json.dump(json_data, f, indent=2)
            messagebox.showinfo("Success", f"e-Way Bill data exported to:\n{filename}")

    def _save_eway_number(self):
        """Save e-Way Bill number after manual portal entry"""
        selected = self.eway_invoice_var.get()

        if selected not in self.eway_invoices:
            messagebox.showwarning("Select Invoice", "Please select an invoice first.")
            return

        invoice = self.eway_invoices[selected]

        # Ask for EWB number
        dialog = ctk.CTkInputDialog(
            text="Enter the e-Way Bill number from GST portal:",
            title="Save e-Way Bill Number"
        )
        ewb_number = dialog.get_input()

        if ewb_number:
            if self.eway_service.save_eway_bill_number(invoice.id, ewb_number.strip()):
                messagebox.showinfo("Saved", f"e-Way Bill number saved:\n{ewb_number}")
                self._refresh_eway_invoices()
            else:
                messagebox.showerror("Error", "Failed to save e-Way Bill number.")

    def _export_sales_excel(self):
        """Export sales report to Excel"""
        if not ExcelExporter.is_available():
            messagebox.showerror("Not Available", "Excel export requires openpyxl.\nInstall with: pip install openpyxl")
            return

        if not self.current_sales_report:
            messagebox.showwarning("No Data", "Please generate a sales report first.")
            return

        # Get company name
        company = Company.get()
        company_name = company.name if company else "GST Billing"

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfilename=f"Sales_Report_{self.current_sales_report.get('date', date.today())}.xlsx"
        )

        if filename:
            result = self.excel_exporter.export_sales_report(
                report_data=self.current_sales_report,
                invoices=self.current_sales_invoices,
                output_path=filename,
                company_name=company_name
            )

            if result['success']:
                messagebox.showinfo("Success", f"Sales report exported to:\n{filename}")
            else:
                messagebox.showerror("Error", f"Export failed:\n{result.get('error', 'Unknown error')}")

    def _export_gst_excel(self):
        """Export GST report to Excel"""
        if not ExcelExporter.is_available():
            messagebox.showerror("Not Available", "Excel export requires openpyxl.\nInstall with: pip install openpyxl")
            return

        if not self.current_gst_report:
            messagebox.showwarning("No Data", "Please generate a GST report first.")
            return

        # Get company name
        company = Company.get()
        company_name = company.name if company else "GST Billing"

        # Ask for save location
        start_date = self.current_gst_report.get('start_date', date.today())
        end_date = self.current_gst_report.get('end_date', date.today())
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfilename=f"GST_Report_{start_date}_to_{end_date}.xlsx"
        )

        if filename:
            result = self.excel_exporter.export_gst_report(
                gst_summary=self.current_gst_report,
                output_path=filename,
                company_name=company_name
            )

            if result['success']:
                messagebox.showinfo("Success", f"GST report exported to:\n{filename}")
            else:
                messagebox.showerror("Error", f"Export failed:\n{result.get('error', 'Unknown error')}")

    def _export_stock_excel(self):
        """Export stock report to Excel"""
        if not ExcelExporter.is_available():
            messagebox.showerror("Not Available", "Excel export requires openpyxl.\nInstall with: pip install openpyxl")
            return

        if not self.current_stock_report:
            # Generate if not available
            self.current_stock_report = self.stock_service.get_stock_report()

        # Get company name
        company = Company.get()
        company_name = company.name if company else "GST Billing"

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfilename=f"Stock_Report_{date.today()}.xlsx"
        )

        if filename:
            result = self.excel_exporter.export_stock_report(
                stock_items=self.current_stock_report,
                output_path=filename,
                company_name=company_name
            )

            if result['success']:
                messagebox.showinfo("Success", f"Stock report exported to:\n{filename}")
            else:
                messagebox.showerror("Error", f"Export failed:\n{result.get('error', 'Unknown error')}")

    def refresh(self):
        """Refresh reports"""
        self._refresh_eway_invoices()
