"""Billing screen with barcode scanner support"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from database.models import Product, Customer
from services.invoice_service import InvoiceService
from services.gst_calculator import GSTCalculator, CartItem
from services.pdf_generator import PDFGenerator
from utils.formatters import format_currency
from config import PAYMENT_MODES


class BillingFrame(ctk.CTkFrame):
    """Main billing/invoicing screen"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.invoice_service = InvoiceService()
        self.gst_calc = GSTCalculator()
        self.pdf_gen = PDFGenerator()

        # Cart items: list of dicts with product_id, product, qty
        self.cart = []
        self.selected_customer = None
        self.last_invoice = None  # Store last created invoice for PDF operations

        self._create_widgets()
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for quick billing"""
        # Get the top-level window and bind to it (bind_all not allowed in CustomTkinter)
        root = self.winfo_toplevel()
        root.bind('<F1>', lambda e: self._focus_search())
        root.bind('<F2>', lambda e: self._clear_cart())
        root.bind('<F3>', lambda e: self._save_and_print())
        root.bind('<F4>', lambda e: self._focus_discount())
        root.bind('<F5>', lambda e: self._hold_bill())
        root.bind('<F6>', lambda e: self._recall_bill())
        root.bind('<Escape>', lambda e: self._on_escape())

    def _focus_search(self):
        """Focus on search entry (F1)"""
        self.search_entry.focus_set()
        self.search_var.set("")

    def _focus_discount(self):
        """Focus on discount entry (F4)"""
        self.discount_entry.focus_set()
        self.discount_entry.select_range(0, 'end')

    def _on_escape(self):
        """Handle escape key - clear search or unfocus"""
        if self.search_var.get():
            self.search_var.set("")
            self.search_results_frame.grid_remove()
        self.focus_set()

    def _create_widgets(self):
        """Create billing screen widgets"""
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="New Bill",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # Left side - Product search and cart
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)

        # Search bar (barcode scanner input goes here)
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        search_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            search_frame,
            text="Scan Barcode or Search Product:",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w")

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Scan barcode or type product name...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.search_entry.bind('<Return>', self._on_search)
        self.search_entry.bind('<KeyRelease>', self._on_search_key)

        # Search results dropdown
        self.search_results_frame = ctk.CTkFrame(left_frame)
        self.search_results_frame.grid(row=1, column=0, sticky="ew", padx=15)
        self.search_results_frame.grid_remove()  # Hidden initially

        # Cart table
        cart_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        cart_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=10)
        cart_frame.grid_columnconfigure(0, weight=1)
        cart_frame.grid_rowconfigure(1, weight=1)

        # Cart header
        header_frame = ctk.CTkFrame(cart_frame, fg_color=("gray80", "gray30"), height=40)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        headers = ['#', 'Product', 'Rate', 'Qty', 'GST', 'Amount']
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=h,
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=i, padx=10, pady=8)

        # Cart items scrollable
        self.cart_scroll = ctk.CTkScrollableFrame(cart_frame, fg_color="transparent")
        self.cart_scroll.grid(row=1, column=0, sticky="nsew")
        self.cart_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Right side - Customer and totals
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=1, column=1, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)

        # Customer selection
        customer_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        customer_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        customer_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            customer_frame,
            text="Customer (Optional):",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w")

        self.customer_var = ctk.StringVar(value="Cash Customer")
        self.customer_combo = ctk.CTkComboBox(
            customer_frame,
            variable=self.customer_var,
            values=["Cash Customer"],
            height=35,
            command=self._on_customer_select
        )
        self.customer_combo.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Totals display
        totals_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        totals_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        totals_frame.grid_columnconfigure(1, weight=1)

        self.subtotal_label = self._create_total_row(totals_frame, "Subtotal:", 0)
        self.cgst_label = self._create_total_row(totals_frame, "CGST:", 1)
        self.sgst_label = self._create_total_row(totals_frame, "SGST:", 2)

        # Discount
        ctk.CTkLabel(
            totals_frame,
            text="Discount:",
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, sticky="w", pady=5)

        self.discount_var = ctk.StringVar(value="0")
        self.discount_entry = ctk.CTkEntry(
            totals_frame,
            textvariable=self.discount_var,
            width=100,
            height=30
        )
        self.discount_entry.grid(row=3, column=1, sticky="e", pady=5)
        self.discount_entry.bind('<KeyRelease>', self._update_totals)

        # Grand total
        ctk.CTkFrame(totals_frame, height=2, fg_color="gray").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=10
        )

        self.grand_total_label = ctk.CTkLabel(
            totals_frame,
            text="0.00",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        ctk.CTkLabel(
            totals_frame,
            text="Grand Total:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=5, column=0, sticky="w")
        self.grand_total_label.grid(row=5, column=1, sticky="e")

        # Payment mode section
        payment_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        payment_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)

        ctk.CTkLabel(
            payment_frame,
            text="Payment:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        # Quick payment buttons
        quick_buttons = ctk.CTkFrame(payment_frame, fg_color="transparent")
        quick_buttons.pack(fill="x", pady=5)

        self.payment_mode = "single"  # "single" or "split"
        self.payment_var = ctk.StringVar(value="CASH")
        self.split_payments = []  # List of payment dicts
        self.split_payment_rows = []  # List of split payment row widgets

        ctk.CTkButton(
            quick_buttons,
            text="Cash",
            width=60,
            height=30,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=lambda: self._set_payment_mode("CASH")
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            quick_buttons,
            text="UPI",
            width=60,
            height=30,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=lambda: self._set_payment_mode("UPI")
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            quick_buttons,
            text="Card",
            width=60,
            height=30,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            command=lambda: self._set_payment_mode("CARD")
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            quick_buttons,
            text="Split",
            width=60,
            height=30,
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self._show_split_payment
        ).pack(side="left", padx=(0, 5))

        # Payment mode indicator
        self.payment_indicator = ctk.CTkLabel(
            payment_frame,
            text="Mode: CASH",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.payment_indicator.pack(anchor="w", pady=(5, 0))

        # Split payment container (hidden by default)
        self.split_frame = ctk.CTkFrame(payment_frame, fg_color=("gray90", "gray20"))
        self.split_payments_container = None

        # Action buttons
        actions_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        actions_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=20)
        actions_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions_frame,
            text="Clear Cart",
            height=45,
            fg_color="gray",
            hover_color="darkgray",
            command=self._clear_cart
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            actions_frame,
            text="Save & Print (F3)",
            height=45,
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_and_print
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Save PDF button row
        pdf_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        pdf_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 5))
        pdf_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            pdf_frame,
            text="Save PDF",
            height=35,
            fg_color="purple",
            hover_color="darkviolet",
            command=self._save_as_pdf
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            pdf_frame,
            text="View PDF",
            height=35,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self._view_pdf
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Hold/Recall buttons
        hold_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        hold_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 10))
        hold_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            hold_frame,
            text="Hold Bill (F5)",
            height=35,
            fg_color="orange",
            hover_color="darkorange",
            command=self._hold_bill
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            hold_frame,
            text="Recall Bill (F6)",
            height=35,
            fg_color="purple",
            hover_color="darkviolet",
            command=self._recall_bill
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Keyboard shortcuts hint
        shortcuts_label = ctk.CTkLabel(
            right_frame,
            text="Shortcuts: F1-Search | F2-Clear | F3-Save | F4-Discount | F5-Hold | F6-Recall | Esc-Cancel",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        shortcuts_label.grid(row=6, column=0, sticky="ew", padx=15, pady=(5, 10))

    def _create_total_row(self, parent, label: str, row: int):
        """Create a totals row"""
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=12)
        ).grid(row=row, column=0, sticky="w", pady=3)

        value_label = ctk.CTkLabel(
            parent,
            text="0.00",
            font=ctk.CTkFont(size=12)
        )
        value_label.grid(row=row, column=1, sticky="e", pady=3)
        return value_label

    def _on_search(self, event=None):
        """Handle search/barcode scan"""
        query = self.search_var.get().strip()
        if not query:
            return

        # First try exact barcode match
        product = Product.get_by_barcode(query)
        if product:
            self._add_to_cart(product)
            self.search_var.set("")
            self.search_results_frame.grid_remove()
            return

        # Otherwise search by name
        products = Product.search(query)
        if len(products) == 1:
            self._add_to_cart(products[0])
            self.search_var.set("")
            self.search_results_frame.grid_remove()
        elif products:
            self._show_search_results(products)

    def _on_search_key(self, event=None):
        """Handle key release in search"""
        query = self.search_var.get().strip()
        if len(query) >= 2:
            products = Product.search(query)
            if products:
                self._show_search_results(products)
            else:
                self.search_results_frame.grid_remove()
        else:
            self.search_results_frame.grid_remove()

    def _show_search_results(self, products):
        """Show search results dropdown"""
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        self.search_results_frame.grid()

        for product in products[:8]:  # Show max 8 results
            btn = ctk.CTkButton(
                self.search_results_frame,
                text=f"{product.name} - {format_currency(product.price)}",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray30"),
                anchor="w",
                command=lambda p=product: self._select_search_result(p)
            )
            btn.pack(fill="x", pady=1)

    def _select_search_result(self, product):
        """Select a product from search results"""
        self._add_to_cart(product)
        self.search_var.set("")
        self.search_results_frame.grid_remove()
        self.search_entry.focus()

    def _add_to_cart(self, product: Product, qty: float = 1):
        """Add product to cart"""
        # Check if already in cart
        for item in self.cart:
            if item['product_id'] == product.id:
                item['qty'] += qty
                self._refresh_cart_display()
                return

        # Add new item
        self.cart.append({
            'product_id': product.id,
            'product': product,
            'qty': qty
        })
        self._refresh_cart_display()

    def _refresh_cart_display(self):
        """Refresh the cart display"""
        # Clear cart display
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()

        # Add items
        for idx, item in enumerate(self.cart, 1):
            product = item['product']
            qty = item['qty']

            row_frame = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

            # Index
            ctk.CTkLabel(row_frame, text=str(idx)).grid(row=0, column=0, padx=5)

            # Product name
            ctk.CTkLabel(
                row_frame,
                text=product.name[:20],
                anchor="w"
            ).grid(row=0, column=1, padx=5, sticky="w")

            # Rate
            ctk.CTkLabel(
                row_frame,
                text=format_currency(product.price)
            ).grid(row=0, column=2, padx=5)

            # Quantity (editable)
            qty_var = ctk.StringVar(value=str(qty))
            qty_entry = ctk.CTkEntry(row_frame, textvariable=qty_var, width=50, height=25)
            qty_entry.grid(row=0, column=3, padx=5)
            qty_entry.bind('<KeyRelease>', lambda e, i=item, v=qty_var: self._update_qty(i, v))

            # GST
            ctk.CTkLabel(
                row_frame,
                text=f"{int(product.gst_rate)}%"
            ).grid(row=0, column=4, padx=5)

            # Amount
            tax = self.gst_calc.calculate_item_tax(qty, product.price, product.gst_rate)
            ctk.CTkLabel(
                row_frame,
                text=format_currency(tax.total_amount)
            ).grid(row=0, column=5, padx=5)

            # Remove button
            ctk.CTkButton(
                row_frame,
                text="X",
                width=30,
                height=25,
                fg_color="red",
                hover_color="darkred",
                command=lambda i=item: self._remove_from_cart(i)
            ).grid(row=0, column=6, padx=5)

        self._update_totals()

    def _update_qty(self, item, qty_var):
        """Update quantity for an item"""
        try:
            qty = float(qty_var.get())
            if qty > 0:
                item['qty'] = qty
                self._update_totals()
        except ValueError:
            pass

    def _remove_from_cart(self, item):
        """Remove item from cart"""
        self.cart.remove(item)
        self._refresh_cart_display()

    def _update_totals(self, event=None):
        """Update totals display"""
        if not self.cart:
            self.subtotal_label.configure(text="0.00")
            self.cgst_label.configure(text="0.00")
            self.sgst_label.configure(text="0.00")
            self.grand_total_label.configure(text="0.00")
            return

        # Build cart items for calculation
        cart_items = []
        for item in self.cart:
            product = item['product']
            cart_items.append(CartItem(
                product_id=product.id,
                product_name=product.name,
                hsn_code=product.hsn_code or "",
                qty=item['qty'],
                unit=product.unit,
                rate=product.price,
                gst_rate=product.gst_rate
            ))

        # Get discount
        try:
            discount = float(self.discount_var.get() or 0)
        except ValueError:
            discount = 0

        # Calculate
        result = self.gst_calc.calculate_cart_total(cart_items, discount=discount)

        # Update labels
        self.subtotal_label.configure(text=format_currency(result['subtotal']))
        self.cgst_label.configure(text=format_currency(result['cgst_total']))
        self.sgst_label.configure(text=format_currency(result['sgst_total']))
        self.grand_total_label.configure(text=format_currency(result['grand_total']))

    def _on_customer_select(self, value):
        """Handle customer selection"""
        if value == "Cash Customer":
            self.selected_customer = None
        else:
            # Find customer by name
            customers = Customer.search(value)
            if customers:
                self.selected_customer = customers[0]

    def _clear_cart(self):
        """Clear the cart"""
        self.cart = []
        self.discount_var.set("0")
        self.selected_customer = None
        self.customer_var.set("Cash Customer")
        self._refresh_cart_display()

    def _save_and_print(self):
        """Save invoice and print"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add products to the cart.")
            return

        try:
            discount = float(self.discount_var.get() or 0)
        except ValueError:
            discount = 0

        # Create invoice
        cart_data = [{'product_id': item['product_id'], 'qty': item['qty']} for item in self.cart]

        # Get payment info
        payments_list = self._get_payments_list()
        primary_payment_mode = self.payment_var.get()

        # For split payments, use the first payment mode as primary
        if payments_list and len(payments_list) > 0:
            primary_payment_mode = payments_list[0]['mode']

        invoice = self.invoice_service.create_invoice(
            cart_items=cart_data,
            customer=self.selected_customer,
            discount=discount,
            payment_mode=primary_payment_mode
        )

        # Record payments
        if payments_list:
            from services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_split_payment(invoice.id, payments_list)
        else:
            # Single payment - record full amount
            from services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_payment(
                invoice_id=invoice.id,
                payment_mode=primary_payment_mode,
                amount=invoice.grand_total
            )

        # Store invoice for later PDF operations
        self.last_invoice = invoice

        # Generate and print PDF
        try:
            self.pdf_gen.print_invoice(invoice)

            # Get email status message
            email_msg = self._get_email_status_message()

            messagebox.showinfo(
                "Invoice Created",
                f"Invoice {invoice.invoice_number} created successfully!{email_msg}"
            )
        except Exception as e:
            email_msg = self._get_email_status_message()
            messagebox.showwarning(
                "Print Warning",
                f"Invoice saved but printing failed: {e}\n\nInvoice No: {invoice.invoice_number}{email_msg}"
            )

        # Clear cart and reset payment UI
        self._clear_cart()
        self._set_payment_mode("CASH")

    def _save_as_pdf(self):
        """Save current cart as invoice and save PDF to file"""
        if not self.cart:
            # If no cart but last invoice exists, save that
            if self.last_invoice:
                self._save_last_invoice_pdf()
                return
            messagebox.showwarning("Empty Cart", "Please add products to the cart or create an invoice first.")
            return

        # Create invoice first
        try:
            discount = float(self.discount_var.get() or 0)
        except ValueError:
            discount = 0

        cart_data = [{'product_id': item['product_id'], 'qty': item['qty']} for item in self.cart]
        payments_list = self._get_payments_list()
        primary_payment_mode = self.payment_var.get()

        if payments_list and len(payments_list) > 0:
            primary_payment_mode = payments_list[0]['mode']

        invoice = self.invoice_service.create_invoice(
            cart_items=cart_data,
            customer=self.selected_customer,
            discount=discount,
            payment_mode=primary_payment_mode
        )

        # Record payments
        if payments_list:
            from services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_split_payment(invoice.id, payments_list)
        else:
            from services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_payment(
                invoice_id=invoice.id,
                payment_mode=primary_payment_mode,
                amount=invoice.grand_total
            )

        self.last_invoice = invoice

        # Save PDF
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{invoice.invoice_number}.pdf"
        )

        if filename:
            try:
                self.pdf_gen.generate_invoice_pdf(invoice, filename)
                messagebox.showinfo("Success", f"Invoice {invoice.invoice_number} saved to:\n{filename}")
                self._clear_cart()
                self._set_payment_mode("CASH")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {e}")

    def _save_last_invoice_pdf(self):
        """Save the last created invoice as PDF"""
        if not self.last_invoice:
            messagebox.showwarning("No Invoice", "No invoice available. Create an invoice first.")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{self.last_invoice.invoice_number}.pdf"
        )

        if filename:
            try:
                self.pdf_gen.generate_invoice_pdf(self.last_invoice, filename)
                messagebox.showinfo("Success", f"Invoice saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {e}")

    def _view_pdf(self):
        """View the last created invoice as PDF"""
        if not self.last_invoice:
            messagebox.showwarning("No Invoice", "No invoice available. Create an invoice first using 'Save & Print'.")
            return

        import tempfile
        import os
        import platform

        try:
            # Generate PDF to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_path = f.name
                self.pdf_gen.generate_invoice_pdf(self.last_invoice, pdf_path)

            # Open PDF
            system = platform.system()
            if system == 'Windows':
                os.startfile(pdf_path)
            elif system == 'Darwin':  # macOS
                import subprocess
                subprocess.run(['open', pdf_path])
            else:  # Linux
                import subprocess
                subprocess.run(['xdg-open', pdf_path])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def _hold_bill(self):
        """Hold current bill for later recall (F5)"""
        if not self.cart:
            messagebox.showinfo("No Items", "Cart is empty. Nothing to hold.")
            return

        from database.models import HeldBill
        import json

        # Build items JSON
        items = []
        for item in self.cart:
            items.append({
                'product_id': item['product_id'],
                'qty': item['qty']
            })

        try:
            discount = float(self.discount_var.get() or 0)
        except ValueError:
            discount = 0

        # Create held bill
        held_bill = HeldBill(
            hold_name=f"Bill #{len(HeldBill.get_all()) + 1}",
            customer_id=self.selected_customer.id if self.selected_customer else None,
            customer_name=self.selected_customer.name if self.selected_customer else "Cash Customer",
            items_json=json.dumps(items),
            discount=discount
        )
        held_bill.save()

        messagebox.showinfo("Bill Held", f"Bill held as '{held_bill.hold_name}'.\nPress F6 to recall.")
        self._clear_cart()

    def _recall_bill(self):
        """Recall a held bill (F6)"""
        from database.models import HeldBill
        import json

        held_bills = HeldBill.get_all()
        if not held_bills:
            messagebox.showinfo("No Held Bills", "No bills on hold.")
            return

        # Show recall dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Recall Bill")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Select Bill to Recall:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(dialog, height=180)
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        def recall_selected(bill):
            # Load cart from held bill
            self._clear_cart()
            items = json.loads(bill.items_json)
            for item_data in items:
                product = Product.get_by_id(item_data['product_id'])
                if product:
                    self._add_to_cart(product, item_data['qty'])

            self.discount_var.set(str(bill.discount))
            if bill.customer_id:
                customer = Customer.get_by_id(bill.customer_id)
                if customer:
                    self.selected_customer = customer
                    self.customer_var.set(customer.name)

            # Delete the held bill
            bill.delete()
            dialog.destroy()

        for bill in held_bills:
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            ctk.CTkLabel(
                frame,
                text=f"{bill.hold_name} - {bill.customer_name}",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                frame,
                text="Recall",
                width=70,
                height=28,
                fg_color="purple",
                command=lambda b=bill: recall_selected(b)
            ).pack(side="right", padx=5)

            ctk.CTkButton(
                frame,
                text="Delete",
                width=70,
                height=28,
                fg_color="red",
                command=lambda b=bill, f=frame: self._delete_held_bill(b, f)
            ).pack(side="right", padx=2)

    def _delete_held_bill(self, bill, frame):
        """Delete a held bill"""
        bill.delete()
        frame.destroy()

    def _set_payment_mode(self, mode: str):
        """Set single payment mode"""
        self.payment_mode = "single"
        self.payment_var.set(mode)
        self.split_payments = []
        self.payment_indicator.configure(text=f"Mode: {mode}")
        # Hide split frame if shown
        self.split_frame.pack_forget()

    def _show_split_payment(self):
        """Show split payment UI"""
        self.payment_mode = "split"
        self.payment_indicator.configure(text="Mode: SPLIT PAYMENT")

        # Show split payment frame
        self.split_frame.pack(fill="x", pady=(10, 0))

        # Clear previous content
        for widget in self.split_frame.winfo_children():
            widget.destroy()

        self.split_payments = []
        self.split_payment_rows = []

        # Header
        header = ctk.CTkFrame(self.split_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(header, text="Split Payment", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(
            header,
            text="+ Add",
            width=50,
            height=25,
            fg_color="#27ae60",
            command=self._add_split_payment_row
        ).pack(side="right")

        # Container for payment rows
        self.split_payments_container = ctk.CTkFrame(self.split_frame, fg_color="transparent")
        self.split_payments_container.pack(fill="x", padx=10, pady=5)

        # Add two default rows
        self._add_split_payment_row()
        self._add_split_payment_row()

        # Total row
        self.split_total_frame = ctk.CTkFrame(self.split_frame, fg_color="transparent")
        self.split_total_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.split_total_label = ctk.CTkLabel(
            self.split_total_frame,
            text="Split Total: 0.00 | Balance: 0.00",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.split_total_label.pack(side="left")

    def _add_split_payment_row(self):
        """Add a split payment row"""
        row_frame = ctk.CTkFrame(self.split_payments_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        # Mode dropdown
        mode_var = ctk.StringVar(value="CASH")
        mode_combo = ctk.CTkComboBox(
            row_frame,
            values=PAYMENT_MODES,
            variable=mode_var,
            width=100,
            height=28
        )
        mode_combo.pack(side="left", padx=(0, 5))

        # Amount entry
        amount_var = ctk.StringVar(value="0")
        amount_entry = ctk.CTkEntry(
            row_frame,
            textvariable=amount_var,
            width=80,
            height=28,
            placeholder_text="Amount"
        )
        amount_entry.pack(side="left", padx=(0, 5))
        amount_entry.bind('<KeyRelease>', lambda e: self._update_split_total())

        # Reference entry
        ref_var = ctk.StringVar()
        ref_entry = ctk.CTkEntry(
            row_frame,
            textvariable=ref_var,
            width=80,
            height=28,
            placeholder_text="Ref #"
        )
        ref_entry.pack(side="left", padx=(0, 5))

        # Remove button
        ctk.CTkButton(
            row_frame,
            text="X",
            width=25,
            height=28,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self._remove_split_payment_row(row_frame, payment_data)
        ).pack(side="left")

        payment_data = {
            'frame': row_frame,
            'mode_var': mode_var,
            'amount_var': amount_var,
            'ref_var': ref_var
        }
        self.split_payment_rows.append(payment_data)

    def _remove_split_payment_row(self, frame, payment_data):
        """Remove a split payment row"""
        if len(self.split_payment_rows) > 1:
            frame.destroy()
            self.split_payment_rows.remove(payment_data)
            self._update_split_total()

    def _update_split_total(self):
        """Update split payment total"""
        total = 0
        for row in self.split_payment_rows:
            try:
                total += float(row['amount_var'].get() or 0)
            except ValueError:
                pass

        # Get grand total
        try:
            grand_total = float(self.grand_total_label.cget("text").replace(",", "").replace("₹", ""))
        except:
            grand_total = 0

        balance = grand_total - total
        color = "green" if balance <= 0 else "red"

        self.split_total_label.configure(
            text=f"Split Total: {format_currency(total)} | Balance: {format_currency(balance)}",
            text_color=color if balance != 0 else "gray"
        )

    def _get_payments_list(self):
        """Get list of payments for invoice creation"""
        if self.payment_mode == "single":
            return None  # Use legacy single payment mode

        payments = []
        for row in self.split_payment_rows:
            try:
                amount = float(row['amount_var'].get() or 0)
                if amount > 0:
                    payments.append({
                        'mode': row['mode_var'].get(),
                        'amount': amount,
                        'reference': row['ref_var'].get()
                    })
            except ValueError:
                pass
        return payments if payments else None

    def _get_email_status_message(self) -> str:
        """Get email status message for invoice creation feedback"""
        try:
            from services.email_service import is_email_auto_send_enabled
            if not is_email_auto_send_enabled():
                return ""

            from services.network_service import NetworkService
            network = NetworkService()

            if network.is_online():
                return "\n\nEmail will be sent shortly."
            else:
                return "\n\nEmail queued (will send when online)."
        except Exception:
            return ""

    def refresh(self):
        """Refresh customer list"""
        customers = Customer.get_all()
        customer_names = ["Cash Customer"] + [c.name for c in customers]
        self.customer_combo.configure(values=customer_names)
