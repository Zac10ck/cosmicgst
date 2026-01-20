"""Customers management screen"""
import customtkinter as ctk
from tkinter import messagebox
from database.models import Customer
from utils.validators import validate_gstin, validate_phone
from utils.constants import STATE_CODES


class CustomersFrame(ctk.CTkFrame):
    """Customers listing and management"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self._create_widgets()

    def _create_widgets(self):
        """Create customers screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Customers",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Search
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            placeholder_text="Search customers...",
            width=250
        )
        search_entry.grid(row=0, column=1, padx=20)
        search_entry.bind('<KeyRelease>', self._on_search)

        # Add button
        ctk.CTkButton(
            header,
            text="+ Add Customer",
            command=self._show_add_dialog
        ).grid(row=0, column=2)

        # Customers list
        self.customers_frame = ctk.CTkScrollableFrame(self)
        self.customers_frame.grid(row=1, column=0, sticky="nsew")
        self.customers_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Table header
        headers = ['Name', 'Phone', 'GSTIN', 'State', 'Actions']
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                self.customers_frame,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=i, padx=10, pady=10, sticky="w")

    def _on_search(self, event=None):
        """Handle search"""
        self.refresh()

    def refresh(self):
        """Refresh customers list"""
        # Clear existing rows (keep header)
        for widget in self.customers_frame.winfo_children():
            if int(widget.grid_info().get('row', 0)) > 0:
                widget.destroy()

        # Get customers
        query = self.search_var.get().strip()
        if query:
            customers = Customer.search(query)
        else:
            customers = Customer.get_all()

        # Display customers
        for idx, customer in enumerate(customers, 1):
            self._create_customer_row(customer, idx)

    def _create_customer_row(self, customer: Customer, row: int):
        """Create a customer row"""
        # Name
        ctk.CTkLabel(
            self.customers_frame,
            text=customer.name[:30]
        ).grid(row=row, column=0, padx=10, pady=5, sticky="w")

        # Phone
        ctk.CTkLabel(
            self.customers_frame,
            text=customer.phone or "-"
        ).grid(row=row, column=1, padx=10, pady=5, sticky="w")

        # GSTIN
        ctk.CTkLabel(
            self.customers_frame,
            text=customer.gstin or "-"
        ).grid(row=row, column=2, padx=10, pady=5, sticky="w")

        # State
        state_name = STATE_CODES.get(customer.state_code, "Kerala")
        ctk.CTkLabel(
            self.customers_frame,
            text=state_name[:15]
        ).grid(row=row, column=3, padx=10, pady=5, sticky="w")

        # Actions
        actions = ctk.CTkFrame(self.customers_frame, fg_color="transparent")
        actions.grid(row=row, column=4, padx=10, pady=5)

        ctk.CTkButton(
            actions,
            text="Edit",
            width=60,
            height=28,
            command=lambda c=customer: self._show_edit_dialog(c)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions,
            text="Delete",
            width=60,
            height=28,
            fg_color="red",
            hover_color="darkred",
            command=lambda c=customer: self._delete_customer(c)
        ).pack(side="left", padx=2)

    def _show_add_dialog(self):
        """Show add customer dialog"""
        dialog = CustomerDialog(self, "Add Customer")
        self.wait_window(dialog)
        self.refresh()

    def _show_edit_dialog(self, customer: Customer):
        """Show edit customer dialog"""
        dialog = CustomerDialog(self, "Edit Customer", customer)
        self.wait_window(dialog)
        self.refresh()

    def _delete_customer(self, customer: Customer):
        """Delete (deactivate) customer"""
        if messagebox.askyesno("Confirm Delete", f"Delete customer '{customer.name}'?"):
            customer.is_active = False
            customer.save()
            self.refresh()


class CustomerDialog(ctk.CTkToplevel):
    """Dialog for adding/editing customers"""

    def __init__(self, parent, title: str, customer: Customer = None):
        super().__init__(parent)
        self.customer = customer

        self.title(title)
        self.geometry("450x450")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if customer:
            self._populate_fields()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Name
        ctk.CTkLabel(self, text="Customer Name *").pack(pady=(20, 5), padx=20, anchor="w")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.name_var, width=400).pack(padx=20)

        # Phone
        ctk.CTkLabel(self, text="Phone").pack(pady=(15, 5), padx=20, anchor="w")
        self.phone_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.phone_var, width=400).pack(padx=20)

        # GSTIN
        ctk.CTkLabel(self, text="GSTIN (for B2B)").pack(pady=(15, 5), padx=20, anchor="w")
        self.gstin_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.gstin_var, width=400).pack(padx=20)

        # State
        ctk.CTkLabel(self, text="State").pack(pady=(15, 5), padx=20, anchor="w")
        self.state_var = ctk.StringVar(value="32 - Kerala")
        state_values = [f"{code} - {name}" for code, name in sorted(STATE_CODES.items())]
        ctk.CTkComboBox(
            self,
            variable=self.state_var,
            values=state_values,
            width=400
        ).pack(padx=20)

        # Address
        ctk.CTkLabel(self, text="Address").pack(pady=(15, 5), padx=20, anchor="w")
        self.address_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.address_var, width=400).pack(padx=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=30)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save
        ).pack(side="right")

    def _populate_fields(self):
        """Populate fields for editing"""
        self.name_var.set(self.customer.name)
        self.phone_var.set(self.customer.phone or "")
        self.gstin_var.set(self.customer.gstin or "")
        state_name = STATE_CODES.get(self.customer.state_code, "Kerala")
        self.state_var.set(f"{self.customer.state_code} - {state_name}")
        self.address_var.set(self.customer.address or "")

    def _save(self):
        """Save customer"""
        # Validate
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return

        # Validate phone
        phone = self.phone_var.get().strip()
        if phone:
            valid, error = validate_phone(phone)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Validate GSTIN
        gstin = self.gstin_var.get().strip().upper()
        if gstin:
            valid, error = validate_gstin(gstin)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Get state code
        state_str = self.state_var.get()
        state_code = state_str.split(" - ")[0] if " - " in state_str else "32"

        if self.customer:
            # Update existing
            self.customer.name = name
            self.customer.phone = phone or None
            self.customer.gstin = gstin or None
            self.customer.state_code = state_code
            self.customer.address = self.address_var.get().strip() or None
            self.customer.save()
        else:
            # Create new
            customer = Customer(
                name=name,
                phone=phone or None,
                gstin=gstin or None,
                state_code=state_code,
                address=self.address_var.get().strip() or None
            )
            customer.save()

        self.destroy()
