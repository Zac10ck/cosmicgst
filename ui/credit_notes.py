"""Credit Notes management screen"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta
from database.models import Invoice, CreditNote, Customer
from services.credit_note_service import CreditNoteService
from services.pdf_generator import PDFGenerator
from utils.formatters import format_currency, format_date


class CreditNotesFrame(ctk.CTkFrame):
    """Credit notes management screen"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.credit_note_service = CreditNoteService()
        self.pdf_gen = PDFGenerator()

        self.selected_invoice = None
        self.returnable_items = []

        self._create_widgets()

    def _create_widgets(self):
        """Create credit notes screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="Credit Notes",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, pady=(0, 15), sticky="w")

        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("Create Credit Note")
        self.tabview.add("Credit Note History")

        self._create_new_credit_note_tab()
        self._create_history_tab()

    def _create_new_credit_note_tab(self):
        """Create the new credit note tab"""
        tab = self.tabview.tab("Create Credit Note")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Step 1: Select Invoice
        step1_frame = ctk.CTkFrame(tab)
        step1_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        step1_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            step1_frame,
            text="Step 1: Select Original Invoice",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(step1_frame, text="Invoice #:").grid(row=1, column=0, padx=10, pady=5)

        self.invoice_search_var = ctk.StringVar()
        self.invoice_search_entry = ctk.CTkEntry(
            step1_frame,
            textvariable=self.invoice_search_var,
            placeholder_text="Enter invoice number...",
            width=200
        )
        self.invoice_search_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.invoice_search_entry.bind('<Return>', self._search_invoice)

        ctk.CTkButton(
            step1_frame,
            text="Search",
            width=80,
            command=self._search_invoice
        ).grid(row=1, column=2, padx=10, pady=5)

        # Invoice info display
        self.invoice_info_label = ctk.CTkLabel(
            step1_frame,
            text="No invoice selected",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.invoice_info_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))

        # Step 2: Select Items to Return
        step2_frame = ctk.CTkFrame(tab)
        step2_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        step2_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            step2_frame,
            text="Step 2: Select Items to Return",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # Items list
        self.items_scroll = ctk.CTkScrollableFrame(step2_frame, height=150)
        self.items_scroll.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.items_scroll.grid_columnconfigure(0, weight=1)

        self.item_checkboxes = []  # List of {'var': BooleanVar, 'qty_var': StringVar, 'item': dict}

        # Step 3: Reason and Create
        step3_frame = ctk.CTkFrame(tab)
        step3_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        step3_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            step3_frame,
            text="Step 3: Reason & Create",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(step3_frame, text="Reason:").grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.reason_var = ctk.StringVar(value="RETURN")
        self.reason_combo = ctk.CTkComboBox(
            step3_frame,
            values=CreditNoteService.REASONS,
            variable=self.reason_var,
            width=200
        )
        self.reason_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(step3_frame, text="Details:").grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.reason_details_var = ctk.StringVar()
        ctk.CTkEntry(
            step3_frame,
            textvariable=self.reason_details_var,
            placeholder_text="Optional details...",
            width=300
        ).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Preview totals
        self.preview_label = ctk.CTkLabel(
            step3_frame,
            text="Credit Amount: 0.00",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#c0392b"
        )
        self.preview_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Create button
        ctk.CTkButton(
            step3_frame,
            text="Create Credit Note",
            fg_color="#c0392b",
            hover_color="#a93226",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._create_credit_note
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def _create_history_tab(self):
        """Create the history tab"""
        tab = self.tabview.tab("Credit Note History")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Filters
        filter_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="From:").pack(side="left", padx=5)

        self.history_start_var = ctk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        ctk.CTkEntry(
            filter_frame,
            textvariable=self.history_start_var,
            width=100,
            placeholder_text="YYYY-MM-DD"
        ).pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="To:").pack(side="left", padx=5)

        self.history_end_var = ctk.StringVar(value=date.today().isoformat())
        ctk.CTkEntry(
            filter_frame,
            textvariable=self.history_end_var,
            width=100,
            placeholder_text="YYYY-MM-DD"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Search",
            width=80,
            command=self._load_credit_notes
        ).pack(side="left", padx=10)

        # Credit notes list
        self.history_scroll = ctk.CTkScrollableFrame(tab)
        self.history_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.history_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Header
        headers = ['CN Number', 'Date', 'Original Invoice', 'Customer', 'Amount', 'Actions']
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                self.history_scroll,
                text=h,
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")

    def _search_invoice(self, event=None):
        """Search for invoice by number"""
        invoice_number = self.invoice_search_var.get().strip()
        if not invoice_number:
            return

        invoice = Invoice.get_by_number(invoice_number)
        if not invoice:
            messagebox.showwarning("Not Found", f"Invoice '{invoice_number}' not found.")
            return

        if invoice.is_cancelled:
            messagebox.showwarning("Cancelled", "Cannot create credit note for cancelled invoice.")
            return

        self.selected_invoice = invoice

        # Update info label
        self.invoice_info_label.configure(
            text=f"Invoice: {invoice.invoice_number} | Date: {format_date(invoice.invoice_date)} | "
                 f"Customer: {invoice.customer_name} | Total: {format_currency(invoice.grand_total)}",
            text_color="#27ae60"
        )

        # Load returnable items
        self._load_returnable_items()

    def _load_returnable_items(self):
        """Load items that can be returned from selected invoice"""
        # Clear previous items
        for widget in self.items_scroll.winfo_children():
            widget.destroy()
        self.item_checkboxes = []

        if not self.selected_invoice:
            return

        self.returnable_items = self.credit_note_service.get_returnable_items(self.selected_invoice)

        if not self.returnable_items:
            ctk.CTkLabel(
                self.items_scroll,
                text="No items available for return (all items already returned)",
                text_color="gray"
            ).pack(pady=10)
            return

        # Header
        header_frame = ctk.CTkFrame(self.items_scroll, fg_color=("gray80", "gray30"))
        header_frame.pack(fill="x", pady=2)

        headers = ['Select', 'Product', 'Original Qty', 'Returned', 'Return Qty', 'Rate']
        for h in headers:
            ctk.CTkLabel(
                header_frame,
                text=h,
                font=ctk.CTkFont(size=10, weight="bold"),
                width=80
            ).pack(side="left", padx=5, pady=3)

        # Items
        for item in self.returnable_items:
            row_frame = ctk.CTkFrame(self.items_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            # Checkbox
            select_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=select_var,
                width=20,
                command=self._update_preview
            ).pack(side="left", padx=5)

            # Product name
            ctk.CTkLabel(
                row_frame,
                text=item['product_name'][:20],
                width=120,
                anchor="w"
            ).pack(side="left", padx=5)

            # Original qty
            ctk.CTkLabel(
                row_frame,
                text=str(item['original_qty']),
                width=60
            ).pack(side="left", padx=5)

            # Already returned
            ctk.CTkLabel(
                row_frame,
                text=str(item['returned_qty']),
                width=60
            ).pack(side="left", padx=5)

            # Return qty entry
            qty_var = ctk.StringVar(value=str(item['returnable_qty']))
            qty_entry = ctk.CTkEntry(
                row_frame,
                textvariable=qty_var,
                width=60
            )
            qty_entry.pack(side="left", padx=5)
            qty_entry.bind('<KeyRelease>', lambda e: self._update_preview())

            # Rate
            ctk.CTkLabel(
                row_frame,
                text=format_currency(item['rate']),
                width=80
            ).pack(side="left", padx=5)

            self.item_checkboxes.append({
                'var': select_var,
                'qty_var': qty_var,
                'item': item
            })

    def _update_preview(self):
        """Update credit amount preview"""
        total = 0
        for checkbox in self.item_checkboxes:
            if checkbox['var'].get():
                try:
                    qty = float(checkbox['qty_var'].get() or 0)
                    qty = min(qty, checkbox['item']['returnable_qty'])  # Cap at returnable
                    rate = checkbox['item']['rate']
                    gst_rate = checkbox['item']['gst_rate']
                    taxable = qty * rate
                    gst = taxable * gst_rate / 100
                    total += taxable + gst
                except ValueError:
                    pass

        self.preview_label.configure(text=f"Credit Amount: {format_currency(total)}")

    def _create_credit_note(self):
        """Create the credit note"""
        if not self.selected_invoice:
            messagebox.showwarning("No Invoice", "Please select an invoice first.")
            return

        # Collect selected items
        items_to_return = []
        for checkbox in self.item_checkboxes:
            if checkbox['var'].get():
                try:
                    qty = float(checkbox['qty_var'].get() or 0)
                    qty = min(qty, checkbox['item']['returnable_qty'])
                    if qty > 0:
                        items_to_return.append({
                            'product_id': checkbox['item']['product_id'],
                            'qty': qty
                        })
                except ValueError:
                    pass

        if not items_to_return:
            messagebox.showwarning("No Items", "Please select at least one item to return.")
            return

        # Create credit note
        try:
            credit_note = self.credit_note_service.create_credit_note(
                original_invoice=self.selected_invoice,
                items_to_return=items_to_return,
                reason=self.reason_var.get(),
                reason_details=self.reason_details_var.get()
            )

            # Print credit note
            try:
                self.pdf_gen.print_credit_note(credit_note)
            except Exception as e:
                print(f"Print error: {e}")

            messagebox.showinfo(
                "Credit Note Created",
                f"Credit Note {credit_note.credit_note_number} created successfully!\n"
                f"Amount: {format_currency(credit_note.grand_total)}"
            )

            # Reset form
            self._reset_form()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create credit note: {e}")

    def _reset_form(self):
        """Reset the create credit note form"""
        self.selected_invoice = None
        self.invoice_search_var.set("")
        self.invoice_info_label.configure(text="No invoice selected", text_color="gray")
        self.reason_var.set("RETURN")
        self.reason_details_var.set("")
        self.preview_label.configure(text="Credit Amount: 0.00")

        for widget in self.items_scroll.winfo_children():
            widget.destroy()
        self.item_checkboxes = []

    def _load_credit_notes(self):
        """Load credit notes for history tab"""
        # Clear existing rows (except header)
        for widget in self.history_scroll.winfo_children():
            grid_info = widget.grid_info()
            if grid_info.get('row', 0) > 0:
                widget.destroy()

        try:
            start_date = date.fromisoformat(self.history_start_var.get())
            end_date = date.fromisoformat(self.history_end_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please enter valid dates (YYYY-MM-DD)")
            return

        credit_notes = self.credit_note_service.get_credit_notes_by_date_range(start_date, end_date)

        if not credit_notes:
            ctk.CTkLabel(
                self.history_scroll,
                text="No credit notes found",
                text_color="gray"
            ).grid(row=1, column=0, columnspan=6, pady=20)
            return

        for row, cn in enumerate(credit_notes, 1):
            cn_date = cn.credit_note_date
            if isinstance(cn_date, str):
                cn_date = date.fromisoformat(cn_date)

            ctk.CTkLabel(
                self.history_scroll,
                text=cn.credit_note_number,
                font=ctk.CTkFont(size=10)
            ).grid(row=row, column=0, padx=5, pady=3, sticky="w")

            ctk.CTkLabel(
                self.history_scroll,
                text=format_date(cn_date),
                font=ctk.CTkFont(size=10)
            ).grid(row=row, column=1, padx=5, pady=3, sticky="w")

            ctk.CTkLabel(
                self.history_scroll,
                text=cn.original_invoice_number or "-",
                font=ctk.CTkFont(size=10)
            ).grid(row=row, column=2, padx=5, pady=3, sticky="w")

            ctk.CTkLabel(
                self.history_scroll,
                text=cn.customer_name[:15] if cn.customer_name else "Cash",
                font=ctk.CTkFont(size=10)
            ).grid(row=row, column=3, padx=5, pady=3, sticky="w")

            ctk.CTkLabel(
                self.history_scroll,
                text=format_currency(cn.grand_total),
                font=ctk.CTkFont(size=10),
                text_color="#c0392b"
            ).grid(row=row, column=4, padx=5, pady=3, sticky="w")

            # Actions frame
            actions_frame = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            actions_frame.grid(row=row, column=5, padx=5, pady=3, sticky="w")

            ctk.CTkButton(
                actions_frame,
                text="Print",
                width=50,
                height=25,
                fg_color="#3498db",
                command=lambda c=cn: self._print_credit_note(c)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame,
                text="PDF",
                width=45,
                height=25,
                fg_color="purple",
                hover_color="darkviolet",
                command=lambda c=cn: self._save_credit_note_pdf(c)
            ).pack(side="left", padx=2)

            if cn.status == "ACTIVE":
                ctk.CTkButton(
                    actions_frame,
                    text="Cancel",
                    width=50,
                    height=25,
                    fg_color="#e74c3c",
                    command=lambda c=cn: self._cancel_credit_note(c)
                ).pack(side="left", padx=2)

    def _print_credit_note(self, credit_note):
        """Print a credit note"""
        try:
            self.pdf_gen.print_credit_note(credit_note)
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print: {e}")

    def _save_credit_note_pdf(self, credit_note):
        """Save credit note as PDF file"""
        from tkinter import filedialog
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"{credit_note.credit_note_number}.pdf"
            )

            if filename:
                self.pdf_gen.generate_credit_note_pdf(credit_note, filename)
                messagebox.showinfo("Saved", f"Credit note saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {e}")

    def _cancel_credit_note(self, credit_note):
        """Cancel a credit note"""
        if messagebox.askyesno(
            "Confirm Cancel",
            f"Cancel credit note {credit_note.credit_note_number}?\n"
            "This will reverse the stock changes."
        ):
            if self.credit_note_service.cancel_credit_note(credit_note.id):
                messagebox.showinfo("Cancelled", "Credit note cancelled successfully.")
                self._load_credit_notes()
            else:
                messagebox.showerror("Error", "Failed to cancel credit note.")

    def refresh(self):
        """Refresh the screen"""
        self._load_credit_notes()
