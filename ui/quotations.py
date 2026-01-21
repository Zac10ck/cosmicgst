"""Quotations screen with Create/History tabs"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date, timedelta
from database.models import Product, Customer, Quotation
from services.quotation_service import QuotationService
from services.pdf_generator import PDFGenerator
from services.gst_calculator import GSTCalculator, CartItem
from utils.formatters import format_currency, format_date


class QuotationsFrame(ctk.CTkFrame):
    """Quotations management screen with tabs"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.quotation_service = QuotationService()
        self.pdf_gen = PDFGenerator()
        self.gst_calc = GSTCalculator()

        # Cart for new quotation
        self.cart = []
        self.selected_customer = None
        self.edit_quotation_id = None  # For editing existing quotations

        self._create_widgets()

    def _create_widgets(self):
        """Create quotations screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="Quotations / Estimates",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("Create Quotation")
        self.tabview.add("Quotation History")

        self._create_quotation_tab()
        self._create_history_tab()

    def _create_quotation_tab(self):
        """Create the quotation creation tab"""
        tab = self.tabview.tab("Create Quotation")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Top section - Product search and customer
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(1, weight=1)

        # Product search
        ctk.CTkLabel(top_frame, text="Product:").grid(row=0, column=0, padx=(0, 10))

        self.product_search_var = ctk.StringVar()
        self.product_search = ctk.CTkEntry(
            top_frame,
            textvariable=self.product_search_var,
            placeholder_text="Search product by name or barcode...",
            width=300
        )
        self.product_search.grid(row=0, column=1, sticky="w")
        self.product_search.bind('<Return>', lambda e: self._search_product())

        ctk.CTkButton(
            top_frame,
            text="Add",
            width=60,
            command=self._search_product
        ).grid(row=0, column=2, padx=10)

        # Customer selection
        ctk.CTkLabel(top_frame, text="Customer:").grid(row=0, column=3, padx=(20, 10))

        self.customer_var = ctk.StringVar()
        self.customer_combo = ctk.CTkComboBox(
            top_frame,
            variable=self.customer_var,
            values=["Cash Customer"],
            width=200,
            command=self._on_customer_select
        )
        self.customer_combo.grid(row=0, column=4)

        # Validity date
        ctk.CTkLabel(top_frame, text="Valid for (days):").grid(row=0, column=5, padx=(20, 10))

        self.validity_var = ctk.StringVar(value="30")
        ctk.CTkEntry(
            top_frame,
            textvariable=self.validity_var,
            width=60
        ).grid(row=0, column=6)

        # Cart section (left)
        cart_frame = ctk.CTkFrame(tab)
        cart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=5)
        cart_frame.grid_rowconfigure(1, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cart_frame,
            text="Items",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), padx=15, sticky="w")

        # Cart headers
        headers_frame = ctk.CTkFrame(cart_frame, fg_color="gray70")
        headers_frame.grid(row=1, column=0, sticky="ew", padx=10)

        headers = ['Product', 'Qty', 'Rate', 'GST%', 'Total', '']
        widths = [200, 60, 80, 60, 80, 40]
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=11, weight="bold"),
                width=width
            ).grid(row=0, column=i, padx=5, pady=5)

        # Cart items
        self.cart_list = ctk.CTkScrollableFrame(cart_frame, height=250)
        self.cart_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Notes and Terms (right)
        details_frame = ctk.CTkFrame(tab)
        details_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=5)
        details_frame.grid_rowconfigure(3, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            details_frame,
            text="Notes & Terms",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), padx=15, sticky="w")

        ctk.CTkLabel(details_frame, text="Notes:").grid(row=1, column=0, padx=15, sticky="w")
        self.notes_text = ctk.CTkTextbox(details_frame, height=80)
        self.notes_text.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        ctk.CTkLabel(details_frame, text="Terms & Conditions:").grid(row=3, column=0, padx=15, sticky="w")
        self.terms_text = ctk.CTkTextbox(details_frame, height=80)
        self.terms_text.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        # Default terms
        default_terms = """1. Prices are valid until the validity date mentioned.
2. Payment terms: 50% advance, 50% on delivery.
3. Delivery: Within 7-10 working days after order confirmation.
4. This is a quotation and not a tax invoice."""
        self.terms_text.insert("1.0", default_terms)

        # Totals section (bottom left)
        totals_frame = ctk.CTkFrame(tab)
        totals_frame.grid(row=2, column=0, sticky="ew", padx=(0, 5), pady=5)

        self.subtotal_label = ctk.CTkLabel(totals_frame, text="Subtotal: 0.00")
        self.subtotal_label.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(totals_frame, text="Discount:").pack(side="left", padx=(20, 5))
        self.discount_var = ctk.StringVar(value="0")
        ctk.CTkEntry(totals_frame, textvariable=self.discount_var, width=80).pack(side="left")
        self.discount_var.trace_add('write', lambda *args: self._update_totals())

        self.tax_label = ctk.CTkLabel(totals_frame, text="Tax: 0.00")
        self.tax_label.pack(side="left", padx=20)

        self.total_label = ctk.CTkLabel(
            totals_frame,
            text="Total: 0.00",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="green"
        )
        self.total_label.pack(side="right", padx=15)

        # Action buttons (bottom right)
        action_frame = ctk.CTkFrame(tab)
        action_frame.grid(row=2, column=1, sticky="ew", padx=(5, 0), pady=5)

        ctk.CTkButton(
            action_frame,
            text="Clear",
            fg_color="gray",
            command=self._clear_cart
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkButton(
            action_frame,
            text="Save as Draft",
            fg_color="#95a5a6",
            command=lambda: self._save_quotation("DRAFT")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Save & Print",
            fg_color="#e67e22",
            hover_color="#d35400",
            command=lambda: self._save_quotation("SENT", print_pdf=True)
        ).pack(side="right", padx=15)

    def _create_history_tab(self):
        """Create the quotation history tab"""
        tab = self.tabview.tab("Quotation History")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Filters
        filter_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(filter_frame, text="From:").pack(side="left", padx=(0, 5))

        # Default to start of month
        month_start = date.today().replace(day=1)
        self.history_from_var = ctk.StringVar(value=month_start.strftime("%Y-%m-%d"))
        ctk.CTkEntry(filter_frame, textvariable=self.history_from_var, width=100).pack(side="left")

        ctk.CTkLabel(filter_frame, text="To:").pack(side="left", padx=(15, 5))
        self.history_to_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(filter_frame, textvariable=self.history_to_var, width=100).pack(side="left")

        ctk.CTkLabel(filter_frame, text="Status:").pack(side="left", padx=(15, 5))
        self.status_filter_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(
            filter_frame,
            variable=self.status_filter_var,
            values=["All", "DRAFT", "SENT", "ACCEPTED", "REJECTED", "EXPIRED", "CONVERTED"],
            width=120
        ).pack(side="left")

        ctk.CTkButton(
            filter_frame,
            text="Search",
            command=self._load_quotations
        ).pack(side="left", padx=15)

        ctk.CTkButton(
            filter_frame,
            text="Check Expired",
            fg_color="orange",
            command=self._check_expired
        ).pack(side="left")

        # Quotations list
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="both", expand=True, pady=10)

        # Headers
        headers_frame = ctk.CTkFrame(list_frame, fg_color=("gray80", "gray30"))
        headers_frame.pack(fill="x", padx=5, pady=(5, 0))

        headers = ['Quotation No', 'Date', 'Customer', 'Amount', 'Status', 'Valid Until', 'Actions']
        widths = [120, 90, 150, 100, 80, 90, 200]
        for header, width in zip(headers, widths):
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=width
            ).pack(side="left", padx=5, pady=8)

        # Scrollable list
        self.quotation_list = ctk.CTkScrollableFrame(list_frame, height=400)
        self.quotation_list.pack(fill="both", expand=True, padx=5, pady=(0, 5))

    def _search_product(self):
        """Search and add product to cart"""
        query = self.product_search_var.get().strip()
        if not query:
            return

        # Search by barcode first, then by name
        product = Product.get_by_barcode(query)
        if not product:
            products = Product.search(query)
            if products:
                product = products[0]

        if product:
            self._add_to_cart(product)
            self.product_search_var.set("")
            self.product_search.focus()
        else:
            messagebox.showwarning("Not Found", f"Product '{query}' not found")

    def _add_to_cart(self, product: Product, qty: float = 1):
        """Add product to cart"""
        # Check if product already in cart
        for item in self.cart:
            if item['product_id'] == product.id:
                item['qty'] += qty
                self._refresh_cart_display()
                return

        # Add new item
        self.cart.append({
            'product_id': product.id,
            'product_name': product.name,
            'qty': qty,
            'rate': product.price,
            'gst_rate': product.gst_rate,
            'unit': product.unit,
            'hsn_code': product.hsn_code or ''
        })
        self._refresh_cart_display()

    def _refresh_cart_display(self):
        """Refresh cart display"""
        # Clear existing items
        for widget in self.cart_list.winfo_children():
            widget.destroy()

        # Display cart items
        for idx, item in enumerate(self.cart):
            row = ctk.CTkFrame(self.cart_list, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Product name
            ctk.CTkLabel(row, text=item['product_name'][:25], width=200, anchor="w").pack(side="left", padx=5)

            # Quantity (editable)
            qty_var = ctk.StringVar(value=str(item['qty']))
            qty_entry = ctk.CTkEntry(row, textvariable=qty_var, width=60)
            qty_entry.pack(side="left", padx=5)
            qty_entry.bind('<FocusOut>', lambda e, i=idx, v=qty_var: self._update_qty(i, v.get()))

            # Rate (editable for quotations)
            rate_var = ctk.StringVar(value=str(item['rate']))
            rate_entry = ctk.CTkEntry(row, textvariable=rate_var, width=80)
            rate_entry.pack(side="left", padx=5)
            rate_entry.bind('<FocusOut>', lambda e, i=idx, v=rate_var: self._update_rate(i, v.get()))

            # GST rate
            ctk.CTkLabel(row, text=f"{item['gst_rate']}%", width=60).pack(side="left", padx=5)

            # Line total
            line_total = item['qty'] * item['rate'] * (1 + item['gst_rate'] / 100)
            ctk.CTkLabel(row, text=format_currency(line_total, ""), width=80).pack(side="left", padx=5)

            # Remove button
            ctk.CTkButton(
                row,
                text="X",
                width=30,
                fg_color="red",
                hover_color="darkred",
                command=lambda i=idx: self._remove_from_cart(i)
            ).pack(side="left", padx=5)

        self._update_totals()

    def _update_qty(self, index: int, qty_str: str):
        """Update item quantity"""
        try:
            qty = float(qty_str)
            if qty > 0:
                self.cart[index]['qty'] = qty
                self._refresh_cart_display()
        except ValueError:
            pass

    def _update_rate(self, index: int, rate_str: str):
        """Update item rate"""
        try:
            rate = float(rate_str)
            if rate >= 0:
                self.cart[index]['rate'] = rate
                self._refresh_cart_display()
        except ValueError:
            pass

    def _remove_from_cart(self, index: int):
        """Remove item from cart"""
        del self.cart[index]
        self._refresh_cart_display()

    def _update_totals(self):
        """Update totals display"""
        subtotal = 0
        total_tax = 0

        for item in self.cart:
            taxable = item['qty'] * item['rate']
            tax = taxable * item['gst_rate'] / 100
            subtotal += taxable
            total_tax += tax

        try:
            discount = float(self.discount_var.get() or 0)
        except ValueError:
            discount = 0

        grand_total = subtotal + total_tax - discount

        self.subtotal_label.configure(text=f"Subtotal: {format_currency(subtotal, '')}")
        self.tax_label.configure(text=f"Tax: {format_currency(total_tax, '')}")
        self.total_label.configure(text=f"Total: {format_currency(grand_total, '')}")

    def _on_customer_select(self, value):
        """Handle customer selection"""
        if value == "Cash Customer":
            self.selected_customer = None
        else:
            customers = Customer.search(value.split(' - ')[0])
            if customers:
                self.selected_customer = customers[0]

    def _clear_cart(self):
        """Clear cart and reset form"""
        self.cart = []
        self.selected_customer = None
        self.edit_quotation_id = None
        self.discount_var.set("0")
        self.customer_var.set("Cash Customer")
        self.validity_var.set("30")
        self.notes_text.delete("1.0", "end")
        self.terms_text.delete("1.0", "end")
        # Reset default terms
        default_terms = """1. Prices are valid until the validity date mentioned.
2. Payment terms: 50% advance, 50% on delivery.
3. Delivery: Within 7-10 working days after order confirmation.
4. This is a quotation and not a tax invoice."""
        self.terms_text.insert("1.0", default_terms)
        self._refresh_cart_display()

    def _save_quotation(self, status: str = "DRAFT", print_pdf: bool = False):
        """Save quotation"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to the quotation")
            return

        try:
            discount = float(self.discount_var.get() or 0)
            validity_days = int(self.validity_var.get() or 30)
        except ValueError:
            messagebox.showerror("Error", "Invalid discount or validity days")
            return

        notes = self.notes_text.get("1.0", "end").strip()
        terms = self.terms_text.get("1.0", "end").strip()

        # Prepare cart items with rate override
        cart_items = []
        for item in self.cart:
            cart_items.append({
                'product_id': item['product_id'],
                'qty': item['qty'],
                'rate': item['rate']
            })

        try:
            if self.edit_quotation_id:
                # Update existing quotation
                quotation = self.quotation_service.update_quotation(
                    quotation_id=self.edit_quotation_id,
                    cart_items=cart_items,
                    customer=self.selected_customer,
                    discount=discount,
                    notes=notes,
                    terms=terms
                )
                if quotation and status != quotation.status:
                    quotation.update_status(status)
                msg = "Quotation updated"
            else:
                # Create new quotation
                quotation = self.quotation_service.create_quotation(
                    cart_items=cart_items,
                    customer=self.selected_customer,
                    discount=discount,
                    validity_days=validity_days,
                    notes=notes,
                    terms=terms,
                    status=status
                )
                msg = "Quotation created"

            if quotation:
                if print_pdf:
                    self.pdf_gen.print_quotation(quotation)
                    msg += " and sent to printer"

                messagebox.showinfo("Success", f"{msg}\n\n{quotation.quotation_number}")
                self._clear_cart()
                self._load_quotations()
            else:
                messagebox.showerror("Error", "Failed to save quotation")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save quotation:\n{str(e)}")

    def _load_quotations(self):
        """Load quotations list"""
        # Clear existing
        for widget in self.quotation_list.winfo_children():
            widget.destroy()

        try:
            from_date = date.fromisoformat(self.history_from_var.get())
            to_date = date.fromisoformat(self.history_to_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        status_filter = self.status_filter_var.get()
        status = None if status_filter == "All" else status_filter

        quotations = Quotation.get_by_date_range(from_date, to_date, status)

        if not quotations:
            ctk.CTkLabel(
                self.quotation_list,
                text="No quotations found",
                text_color="gray"
            ).pack(pady=20)
            return

        for q in quotations:
            row = ctk.CTkFrame(self.quotation_list, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Quotation number
            ctk.CTkLabel(row, text=q.quotation_number, width=120, anchor="w").pack(side="left", padx=5)

            # Date
            ctk.CTkLabel(row, text=format_date(q.quotation_date), width=90).pack(side="left", padx=5)

            # Customer
            ctk.CTkLabel(row, text=q.customer_name or "Cash", width=150, anchor="w").pack(side="left", padx=5)

            # Amount
            ctk.CTkLabel(
                row,
                text=format_currency(q.grand_total, ""),
                width=100,
                text_color="green"
            ).pack(side="left", padx=5)

            # Status with color
            status_colors = {
                'DRAFT': 'gray',
                'SENT': 'blue',
                'ACCEPTED': 'green',
                'REJECTED': 'red',
                'EXPIRED': 'orange',
                'CONVERTED': 'purple'
            }
            ctk.CTkLabel(
                row,
                text=q.status,
                width=80,
                text_color=status_colors.get(q.status, 'gray')
            ).pack(side="left", padx=5)

            # Valid until
            validity_color = "red" if q.is_expired() else "gray"
            ctk.CTkLabel(
                row,
                text=format_date(q.validity_date),
                width=90,
                text_color=validity_color
            ).pack(side="left", padx=5)

            # Actions
            actions_frame = ctk.CTkFrame(row, fg_color="transparent")
            actions_frame.pack(side="left", padx=5)

            ctk.CTkButton(
                actions_frame,
                text="View",
                width=50,
                height=25,
                font=ctk.CTkFont(size=11),
                command=lambda qid=q.id: self._view_quotation(qid)
            ).pack(side="left", padx=2)

            if q.status in ('DRAFT', 'SENT'):
                ctk.CTkButton(
                    actions_frame,
                    text="Edit",
                    width=50,
                    height=25,
                    font=ctk.CTkFont(size=11),
                    fg_color="gray",
                    command=lambda qid=q.id: self._edit_quotation(qid)
                ).pack(side="left", padx=2)

            if q.status in ('DRAFT', 'SENT', 'ACCEPTED'):
                ctk.CTkButton(
                    actions_frame,
                    text="Convert",
                    width=60,
                    height=25,
                    font=ctk.CTkFont(size=11),
                    fg_color="green",
                    command=lambda qid=q.id: self._convert_to_invoice(qid)
                ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame,
                text="Print",
                width=50,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color="#e67e22",
                command=lambda qid=q.id: self._print_quotation(qid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame,
                text="PDF",
                width=45,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color="purple",
                hover_color="darkviolet",
                command=lambda qid=q.id: self._save_quotation_pdf(qid)
            ).pack(side="left", padx=2)

    def _view_quotation(self, quotation_id: int):
        """View quotation details in popup"""
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return

        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(f"Quotation: {quotation.quotation_number}")
        popup.geometry("600x500")

        # Details
        details_frame = ctk.CTkFrame(popup)
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            details_frame,
            text=f"Quotation: {quotation.quotation_number}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))

        info = [
            f"Date: {format_date(quotation.quotation_date)}",
            f"Valid Until: {format_date(quotation.validity_date)}",
            f"Customer: {quotation.customer_name or 'Cash Customer'}",
            f"Status: {quotation.status}",
            f"",
            f"Subtotal: {format_currency(quotation.subtotal, '')}",
            f"CGST: {format_currency(quotation.cgst_total, '')}",
            f"SGST: {format_currency(quotation.sgst_total, '')}",
            f"IGST: {format_currency(quotation.igst_total, '')}",
            f"Discount: {format_currency(quotation.discount, '')}",
            f"Grand Total: {format_currency(quotation.grand_total, '')}",
        ]

        for line in info:
            ctk.CTkLabel(details_frame, text=line).pack(anchor="w", padx=20)

        # Items
        ctk.CTkLabel(
            details_frame,
            text="Items:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 5))

        for item in quotation.items:
            ctk.CTkLabel(
                details_frame,
                text=f"  {item.product_name} x {item.qty} @ {format_currency(item.rate, '')} = {format_currency(item.total, '')}"
            ).pack(anchor="w", padx=20)

        # Close button
        ctk.CTkButton(
            popup,
            text="Close",
            command=popup.destroy
        ).pack(pady=10)

    def _edit_quotation(self, quotation_id: int):
        """Load quotation for editing"""
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation or quotation.status not in ('DRAFT', 'SENT'):
            messagebox.showwarning("Cannot Edit", "Only DRAFT or SENT quotations can be edited")
            return

        # Clear current cart
        self._clear_cart()

        # Set edit mode
        self.edit_quotation_id = quotation_id

        # Load customer
        if quotation.customer_id:
            self.selected_customer = Customer.get_by_id(quotation.customer_id)
            if self.selected_customer:
                self.customer_var.set(f"{self.selected_customer.name} - {self.selected_customer.phone}")

        # Load items
        for item in quotation.items:
            self.cart.append({
                'product_id': item.product_id,
                'product_name': item.product_name,
                'qty': item.qty,
                'rate': item.rate,
                'gst_rate': item.gst_rate,
                'unit': item.unit,
                'hsn_code': item.hsn_code
            })

        # Load other details
        self.discount_var.set(str(quotation.discount))
        validity_days = (quotation.validity_date - quotation.quotation_date).days
        self.validity_var.set(str(validity_days))

        self.notes_text.delete("1.0", "end")
        if quotation.notes:
            self.notes_text.insert("1.0", quotation.notes)

        self.terms_text.delete("1.0", "end")
        if quotation.terms_conditions:
            self.terms_text.insert("1.0", quotation.terms_conditions)

        self._refresh_cart_display()

        # Switch to create tab
        self.tabview.set("Create Quotation")

        messagebox.showinfo("Edit Mode", f"Editing quotation: {quotation.quotation_number}")

    def _convert_to_invoice(self, quotation_id: int):
        """Convert quotation to invoice"""
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return

        if quotation.status not in ('DRAFT', 'SENT', 'ACCEPTED'):
            messagebox.showwarning("Cannot Convert", "Only active quotations can be converted to invoices")
            return

        if not messagebox.askyesno(
            "Confirm Conversion",
            f"Convert quotation {quotation.quotation_number} to invoice?\n\nThis will:\n- Create a new invoice\n- Deduct stock\n- Mark quotation as CONVERTED"
        ):
            return

        try:
            invoice = self.quotation_service.convert_to_invoice(
                quotation_id=quotation_id,
                payment_mode="CASH"
            )

            if invoice:
                messagebox.showinfo(
                    "Success",
                    f"Quotation converted to invoice!\n\nInvoice No: {invoice.invoice_number}"
                )
                self._load_quotations()
            else:
                messagebox.showerror("Error", "Failed to convert quotation")

        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{str(e)}")

    def _print_quotation(self, quotation_id: int):
        """Generate and print quotation PDF"""
        quotation = Quotation.get_by_id(quotation_id)
        if quotation:
            self.pdf_gen.print_quotation(quotation)

    def _save_quotation_pdf(self, quotation_id: int):
        """Save quotation as PDF file"""
        from tkinter import filedialog
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"{quotation.quotation_number}.pdf"
            )

            if filename:
                self.pdf_gen.generate_quotation_pdf(quotation, filename)
                messagebox.showinfo("Saved", f"Quotation saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {e}")

    def _check_expired(self):
        """Check and mark expired quotations"""
        expired = self.quotation_service.check_expired_quotations()
        if expired:
            messagebox.showinfo(
                "Expired Quotations",
                f"{len(expired)} quotation(s) have been marked as EXPIRED"
            )
            self._load_quotations()
        else:
            messagebox.showinfo("Check Complete", "No expired quotations found")

    def refresh(self):
        """Refresh quotation list and customer combo"""
        # Load customers for combo
        customers = Customer.get_all()
        customer_values = ["Cash Customer"]
        for c in customers:
            customer_values.append(f"{c.name} - {c.phone}")
        self.customer_combo.configure(values=customer_values)

        # Load quotations
        self._load_quotations()
