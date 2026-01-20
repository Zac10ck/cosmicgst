"""Invoice History screen with filters and sorting"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta
from database.models import Invoice, Customer
from services.pdf_generator import PDFGenerator
from utils.formatters import format_currency, format_date


class InvoicesFrame(ctk.CTkFrame):
    """Invoice history with filters and sorting"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.pdf_gen = PDFGenerator()

        # Current filter/sort state
        self.current_invoices = []
        self.sort_column = "date"
        self.sort_reverse = True  # Newest first

        self._create_widgets()

    def _create_widgets(self):
        """Create invoice history screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="Invoice History",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(0, 15), sticky="w")

        # Filters Frame
        filters_frame = ctk.CTkFrame(self)
        filters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        filters_frame.grid_columnconfigure(6, weight=1)

        # Date From
        ctk.CTkLabel(filters_frame, text="From:").grid(row=0, column=0, padx=(15, 5), pady=15)

        # Default: 30 days ago
        default_from = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.date_from_var = ctk.StringVar(value=default_from)
        self.date_from_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.date_from_var,
            width=110,
            placeholder_text="YYYY-MM-DD"
        )
        self.date_from_entry.grid(row=0, column=1, padx=5, pady=15)

        # Date To
        ctk.CTkLabel(filters_frame, text="To:").grid(row=0, column=2, padx=(15, 5), pady=15)

        self.date_to_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.date_to_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.date_to_var,
            width=110,
            placeholder_text="YYYY-MM-DD"
        )
        self.date_to_entry.grid(row=0, column=3, padx=5, pady=15)

        # Quick date filters
        quick_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        quick_frame.grid(row=0, column=4, padx=15, pady=15)

        ctk.CTkButton(
            quick_frame,
            text="Today",
            width=60,
            height=28,
            command=self._filter_today
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            quick_frame,
            text="This Week",
            width=80,
            height=28,
            command=self._filter_week
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            quick_frame,
            text="This Month",
            width=90,
            height=28,
            command=self._filter_month
        ).pack(side="left", padx=2)

        # Payment Mode Filter
        ctk.CTkLabel(filters_frame, text="Payment:").grid(row=0, column=5, padx=(15, 5), pady=15)

        self.payment_filter_var = ctk.StringVar(value="All")
        self.payment_filter = ctk.CTkComboBox(
            filters_frame,
            variable=self.payment_filter_var,
            values=["All", "CASH", "UPI", "CARD", "CREDIT", "BANK TRANSFER"],
            width=120,
            command=lambda x: self._apply_filters()
        )
        self.payment_filter.grid(row=0, column=6, padx=5, pady=15)

        # Search
        ctk.CTkLabel(filters_frame, text="Search:").grid(row=0, column=7, padx=(15, 5), pady=15)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.search_var,
            width=150,
            placeholder_text="Invoice # or Customer"
        )
        self.search_entry.grid(row=0, column=8, padx=5, pady=15)
        self.search_entry.bind('<KeyRelease>', lambda e: self._apply_filters())

        # Apply Filter Button
        ctk.CTkButton(
            filters_frame,
            text="Apply",
            width=70,
            command=self._apply_filters
        ).grid(row=0, column=9, padx=15, pady=15)

        # Results summary
        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.summary_label.grid(row=1, column=0, sticky="e", padx=15)

        # Invoice list with headers
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        # Column headers (clickable for sorting)
        header_frame = ctk.CTkFrame(list_frame, fg_color=("gray80", "gray30"), height=40)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        headers = [
            ("Invoice #", "number", 120),
            ("Date", "date", 100),
            ("Customer", "customer", 150),
            ("Amount", "amount", 100),
            ("Payment", "payment", 100),
            ("Status", "status", 80),
            ("Actions", None, 150),
        ]

        for col, (text, sort_key, width) in enumerate(headers):
            if sort_key:
                btn = ctk.CTkButton(
                    header_frame,
                    text=text + " ↕",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray40"),
                    width=width,
                    command=lambda k=sort_key: self._sort_by(k)
                )
                btn.grid(row=0, column=col, padx=5, pady=8)
            else:
                ctk.CTkLabel(
                    header_frame,
                    text=text,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=width
                ).grid(row=0, column=col, padx=5, pady=8)

        # Scrollable invoice list
        self.invoice_list = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.invoice_list.grid(row=1, column=0, sticky="nsew")
        self.invoice_list.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Totals bar at bottom
        totals_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        totals_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.totals_label = ctk.CTkLabel(
            totals_frame,
            text="Total: ₹0.00 | Invoices: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.totals_label.pack(pady=10, padx=20, side="left")

        # Export button
        ctk.CTkButton(
            totals_frame,
            text="Export List",
            width=100,
            fg_color="green",
            hover_color="darkgreen",
            command=self._export_list
        ).pack(pady=10, padx=20, side="right")

    def _filter_today(self):
        """Set filter to today"""
        today = date.today().strftime("%Y-%m-%d")
        self.date_from_var.set(today)
        self.date_to_var.set(today)
        self._apply_filters()

    def _filter_week(self):
        """Set filter to this week"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        self.date_from_var.set(week_start.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
        self._apply_filters()

    def _filter_month(self):
        """Set filter to this month"""
        today = date.today()
        month_start = today.replace(day=1)
        self.date_from_var.set(month_start.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
        self._apply_filters()

    def _apply_filters(self):
        """Apply all filters and refresh list"""
        try:
            from_date = date.fromisoformat(self.date_from_var.get())
            to_date = date.fromisoformat(self.date_to_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        # Get invoices in date range
        invoices = Invoice.get_by_date_range(from_date, to_date)

        # Filter by payment mode
        payment_filter = self.payment_filter_var.get()
        if payment_filter != "All":
            invoices = [inv for inv in invoices if inv.payment_mode == payment_filter]

        # Filter by search term
        search_term = self.search_var.get().strip().lower()
        if search_term:
            invoices = [
                inv for inv in invoices
                if search_term in inv.invoice_number.lower()
                or search_term in (inv.customer_name or "").lower()
            ]

        self.current_invoices = invoices
        self._sort_invoices()
        self._display_invoices()

    def _sort_by(self, column: str):
        """Sort by column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = True if column == "date" else False

        self._sort_invoices()
        self._display_invoices()

    def _sort_invoices(self):
        """Sort current invoices"""
        if not self.current_invoices:
            return

        key_map = {
            "number": lambda x: x.invoice_number,
            "date": lambda x: x.invoice_date if isinstance(x.invoice_date, date) else date.fromisoformat(str(x.invoice_date)),
            "customer": lambda x: x.customer_name or "",
            "amount": lambda x: x.grand_total,
            "payment": lambda x: x.payment_mode,
            "status": lambda x: x.is_cancelled,
        }

        key_func = key_map.get(self.sort_column, key_map["date"])
        self.current_invoices.sort(key=key_func, reverse=self.sort_reverse)

    def _display_invoices(self):
        """Display invoices in the list"""
        # Clear existing rows
        for widget in self.invoice_list.winfo_children():
            widget.destroy()

        if not self.current_invoices:
            ctk.CTkLabel(
                self.invoice_list,
                text="No invoices found for the selected filters",
                text_color="gray"
            ).grid(row=0, column=0, columnspan=7, pady=50)
            self._update_totals([])
            return

        # Display invoices
        for idx, invoice in enumerate(self.current_invoices):
            self._create_invoice_row(invoice, idx)

        self._update_totals(self.current_invoices)

    def _create_invoice_row(self, invoice: Invoice, row: int):
        """Create a row for an invoice"""
        # Alternate row colors
        bg_color = ("gray95", "gray20") if row % 2 == 0 else ("white", "gray17")

        row_frame = ctk.CTkFrame(self.invoice_list, fg_color=bg_color, height=40)
        row_frame.grid(row=row, column=0, columnspan=7, sticky="ew", pady=1)
        row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Invoice Number
        ctk.CTkLabel(
            row_frame,
            text=invoice.invoice_number,
            font=ctk.CTkFont(size=12),
            width=120
        ).grid(row=0, column=0, padx=10, pady=8)

        # Date
        inv_date = invoice.invoice_date
        if isinstance(inv_date, str):
            inv_date = date.fromisoformat(inv_date)
        ctk.CTkLabel(
            row_frame,
            text=format_date(inv_date),
            font=ctk.CTkFont(size=12),
            width=100
        ).grid(row=0, column=1, padx=10, pady=8)

        # Customer
        ctk.CTkLabel(
            row_frame,
            text=(invoice.customer_name or "Cash")[:20],
            font=ctk.CTkFont(size=12),
            width=150
        ).grid(row=0, column=2, padx=10, pady=8)

        # Amount
        ctk.CTkLabel(
            row_frame,
            text=format_currency(invoice.grand_total, "₹"),
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100
        ).grid(row=0, column=3, padx=10, pady=8)

        # Payment Mode
        ctk.CTkLabel(
            row_frame,
            text=invoice.payment_mode,
            font=ctk.CTkFont(size=12),
            width=100
        ).grid(row=0, column=4, padx=10, pady=8)

        # Status
        if invoice.is_cancelled:
            status_text = "Cancelled"
            status_color = "red"
        else:
            status_text = "Active"
            status_color = "green"

        ctk.CTkLabel(
            row_frame,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color,
            width=80
        ).grid(row=0, column=5, padx=10, pady=8)

        # Actions
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=6, padx=10, pady=5)

        ctk.CTkButton(
            actions_frame,
            text="View",
            width=50,
            height=26,
            font=ctk.CTkFont(size=11),
            command=lambda inv=invoice: self._view_invoice(inv)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_frame,
            text="Print",
            width=50,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="green",
            hover_color="darkgreen",
            command=lambda inv=invoice: self._print_invoice(inv)
        ).pack(side="left", padx=2)

        if not invoice.is_cancelled:
            ctk.CTkButton(
                actions_frame,
                text="Cancel",
                width=55,
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="red",
                hover_color="darkred",
                command=lambda inv=invoice: self._cancel_invoice(inv)
            ).pack(side="left", padx=2)

    def _update_totals(self, invoices):
        """Update totals bar"""
        total_amount = sum(inv.grand_total for inv in invoices if not inv.is_cancelled)
        active_count = sum(1 for inv in invoices if not inv.is_cancelled)
        cancelled_count = sum(1 for inv in invoices if inv.is_cancelled)

        summary = f"Showing {len(invoices)} invoice(s)"
        self.summary_label.configure(text=summary)

        totals_text = f"Total: {format_currency(total_amount, '₹')} | Active: {active_count}"
        if cancelled_count:
            totals_text += f" | Cancelled: {cancelled_count}"

        self.totals_label.configure(text=totals_text)

    def _view_invoice(self, invoice: Invoice):
        """View invoice details"""
        dialog = InvoiceDetailDialog(self, invoice)
        self.wait_window(dialog)

    def _print_invoice(self, invoice: Invoice):
        """Print invoice"""
        try:
            # Get full invoice with items
            full_invoice = Invoice.get_by_id(invoice.id)
            self.pdf_gen.print_invoice(full_invoice)
            messagebox.showinfo("Print", f"Invoice {invoice.invoice_number} sent to printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print: {e}")

    def _cancel_invoice(self, invoice: Invoice):
        """Cancel an invoice"""
        if messagebox.askyesno(
            "Cancel Invoice",
            f"Are you sure you want to cancel invoice {invoice.invoice_number}?\n\nThis will restore the stock for all items."
        ):
            from services.invoice_service import InvoiceService
            service = InvoiceService()
            if service.cancel_invoice(invoice.id):
                messagebox.showinfo("Cancelled", f"Invoice {invoice.invoice_number} has been cancelled")
                self._apply_filters()  # Refresh list
            else:
                messagebox.showerror("Error", "Failed to cancel invoice")

    def _export_list(self):
        """Export invoice list to CSV"""
        from tkinter import filedialog
        import csv

        if not self.current_invoices:
            messagebox.showwarning("No Data", "No invoices to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename=f"invoices_{date.today().strftime('%Y%m%d')}.csv"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Invoice Number", "Date", "Customer", "Subtotal",
                        "CGST", "SGST", "IGST", "Total", "Payment Mode", "Status"
                    ])

                    for inv in self.current_invoices:
                        inv_date = inv.invoice_date
                        if isinstance(inv_date, str):
                            inv_date = date.fromisoformat(inv_date)

                        writer.writerow([
                            inv.invoice_number,
                            inv_date.strftime("%Y-%m-%d"),
                            inv.customer_name or "Cash",
                            inv.subtotal,
                            inv.cgst_total,
                            inv.sgst_total,
                            inv.igst_total,
                            inv.grand_total,
                            inv.payment_mode,
                            "Cancelled" if inv.is_cancelled else "Active"
                        ])

                messagebox.showinfo("Export Complete", f"Exported {len(self.current_invoices)} invoices to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def refresh(self):
        """Refresh invoice list"""
        self._apply_filters()


class InvoiceDetailDialog(ctk.CTkToplevel):
    """Dialog showing invoice details"""

    def __init__(self, parent, invoice: Invoice):
        super().__init__(parent)
        self.invoice = Invoice.get_by_id(invoice.id)  # Get full invoice with items

        self.title(f"Invoice {invoice.invoice_number}")
        self.geometry("600x500")
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""
        inv = self.invoice

        # Header
        header_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            header_frame,
            text=inv.invoice_number,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(15, 5))

        inv_date = inv.invoice_date
        if isinstance(inv_date, str):
            inv_date = date.fromisoformat(inv_date)

        ctk.CTkLabel(
            header_frame,
            text=f"Date: {format_date(inv_date)} | Customer: {inv.customer_name or 'Cash'}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 15))

        # Status badge
        if inv.is_cancelled:
            ctk.CTkLabel(
                header_frame,
                text="CANCELLED",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
                fg_color="red",
                corner_radius=5
            ).pack(pady=(0, 15))

        # Items table
        items_frame = ctk.CTkScrollableFrame(self, height=200)
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Headers
        headers = ["#", "Product", "Qty", "Rate", "GST", "Amount"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                items_frame,
                text=h,
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=0, column=col, padx=8, pady=5, sticky="w")

        # Items
        for idx, item in enumerate(inv.items, 1):
            ctk.CTkLabel(items_frame, text=str(idx), font=ctk.CTkFont(size=11)).grid(row=idx, column=0, padx=8, pady=3)
            ctk.CTkLabel(items_frame, text=item.product_name[:25], font=ctk.CTkFont(size=11)).grid(row=idx, column=1, padx=8, pady=3, sticky="w")
            ctk.CTkLabel(items_frame, text=f"{item.qty} {item.unit}", font=ctk.CTkFont(size=11)).grid(row=idx, column=2, padx=8, pady=3)
            ctk.CTkLabel(items_frame, text=format_currency(item.rate), font=ctk.CTkFont(size=11)).grid(row=idx, column=3, padx=8, pady=3)
            ctk.CTkLabel(items_frame, text=f"{int(item.gst_rate)}%", font=ctk.CTkFont(size=11)).grid(row=idx, column=4, padx=8, pady=3)
            ctk.CTkLabel(items_frame, text=format_currency(item.total), font=ctk.CTkFont(size=11)).grid(row=idx, column=5, padx=8, pady=3)

        # Totals
        totals_frame = ctk.CTkFrame(self, fg_color="transparent")
        totals_frame.pack(fill="x", padx=20, pady=10)

        totals_data = [
            ("Subtotal:", format_currency(inv.subtotal)),
            ("CGST:", format_currency(inv.cgst_total)),
            ("SGST:", format_currency(inv.sgst_total)),
        ]

        if inv.igst_total > 0:
            totals_data.append(("IGST:", format_currency(inv.igst_total)))

        if inv.discount > 0:
            totals_data.append(("Discount:", f"- {format_currency(inv.discount)}"))

        totals_data.append(("Grand Total:", format_currency(inv.grand_total)))

        for label, value in totals_data:
            row = ctk.CTkFrame(totals_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, width=150, anchor="e").pack(side="left", expand=True)
            weight = "bold" if "Total" in label else "normal"
            ctk.CTkLabel(row, text=value, width=100, font=ctk.CTkFont(weight=weight)).pack(side="right")

        # Payment mode
        ctk.CTkLabel(
            self,
            text=f"Payment Mode: {inv.payment_mode}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Close",
            width=100,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Print Invoice",
            width=120,
            fg_color="green",
            hover_color="darkgreen",
            command=self._print
        ).pack(side="right")

    def _print(self):
        """Print this invoice"""
        try:
            from services.pdf_generator import PDFGenerator
            pdf_gen = PDFGenerator()
            pdf_gen.print_invoice(self.invoice)
            messagebox.showinfo("Print", "Invoice sent to printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print: {e}")
