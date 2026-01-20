"""Products management screen"""
import customtkinter as ctk
from tkinter import messagebox
from database.models import Product
from services.stock_service import StockService
from utils.formatters import format_currency
from utils.validators import validate_hsn
from config import UNITS, GST_RATES


class ProductsFrame(ctk.CTkFrame):
    """Products listing and management"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.stock_service = StockService()

        self._create_widgets()

    def _create_widgets(self):
        """Create products screen widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Products",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Search
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            placeholder_text="Search products...",
            width=250
        )
        search_entry.grid(row=0, column=1, padx=20)
        search_entry.bind('<KeyRelease>', self._on_search)

        # Add button
        ctk.CTkButton(
            header,
            text="+ Add Product",
            command=self._show_add_dialog
        ).grid(row=0, column=2)

        # Products list
        self.products_frame = ctk.CTkScrollableFrame(self)
        self.products_frame.grid(row=1, column=0, sticky="nsew")
        self.products_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Table header
        headers = ['Name', 'Barcode', 'HSN', 'Price', 'GST', 'Stock', 'Actions']
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                self.products_frame,
                text=h,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=i, padx=10, pady=10, sticky="w")

    def _on_search(self, event=None):
        """Handle search"""
        self.refresh()

    def refresh(self):
        """Refresh products list"""
        # Clear existing rows (keep header)
        for widget in self.products_frame.winfo_children():
            if int(widget.grid_info().get('row', 0)) > 0:
                widget.destroy()

        # Get products
        query = self.search_var.get().strip()
        if query:
            products = Product.search(query)
        else:
            products = Product.get_all()

        # Display products
        for idx, product in enumerate(products, 1):
            self._create_product_row(product, idx)

    def _create_product_row(self, product: Product, row: int):
        """Create a product row"""
        # Name
        ctk.CTkLabel(
            self.products_frame,
            text=product.name[:25]
        ).grid(row=row, column=0, padx=10, pady=5, sticky="w")

        # Barcode
        ctk.CTkLabel(
            self.products_frame,
            text=product.barcode or "-"
        ).grid(row=row, column=1, padx=10, pady=5, sticky="w")

        # HSN
        ctk.CTkLabel(
            self.products_frame,
            text=product.hsn_code or "-"
        ).grid(row=row, column=2, padx=10, pady=5, sticky="w")

        # Price
        ctk.CTkLabel(
            self.products_frame,
            text=format_currency(product.price)
        ).grid(row=row, column=3, padx=10, pady=5, sticky="w")

        # GST
        ctk.CTkLabel(
            self.products_frame,
            text=f"{int(product.gst_rate)}%"
        ).grid(row=row, column=4, padx=10, pady=5, sticky="w")

        # Stock
        stock_color = "red" if product.stock_qty <= product.low_stock_alert else None
        ctk.CTkLabel(
            self.products_frame,
            text=f"{product.stock_qty} {product.unit}",
            text_color=stock_color
        ).grid(row=row, column=5, padx=10, pady=5, sticky="w")

        # Actions
        actions = ctk.CTkFrame(self.products_frame, fg_color="transparent")
        actions.grid(row=row, column=6, padx=10, pady=5)

        ctk.CTkButton(
            actions,
            text="Edit",
            width=60,
            height=28,
            command=lambda p=product: self._show_edit_dialog(p)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions,
            text="Stock",
            width=60,
            height=28,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda p=product: self._show_stock_dialog(p)
        ).pack(side="left", padx=2)

    def _show_add_dialog(self):
        """Show add product dialog"""
        dialog = ProductDialog(self, "Add Product")
        self.wait_window(dialog)
        self.refresh()

    def _show_edit_dialog(self, product: Product):
        """Show edit product dialog"""
        dialog = ProductDialog(self, "Edit Product", product)
        self.wait_window(dialog)
        self.refresh()

    def _show_stock_dialog(self, product: Product):
        """Show stock adjustment dialog"""
        dialog = StockDialog(self, product)
        self.wait_window(dialog)
        self.refresh()


class ProductDialog(ctk.CTkToplevel):
    """Dialog for adding/editing products"""

    def __init__(self, parent, title: str, product: Product = None):
        super().__init__(parent)
        self.product = product
        self.result = None

        self.title(title)
        self.geometry("450x550")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if product:
            self._populate_fields()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Name
        ctk.CTkLabel(self, text="Product Name *").pack(pady=(20, 5), padx=20, anchor="w")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.name_var, width=400).pack(padx=20)

        # Barcode
        ctk.CTkLabel(self, text="Barcode").pack(pady=(15, 5), padx=20, anchor="w")
        self.barcode_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.barcode_var, width=400).pack(padx=20)

        # HSN Code
        ctk.CTkLabel(self, text="HSN Code").pack(pady=(15, 5), padx=20, anchor="w")
        self.hsn_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.hsn_var, width=400).pack(padx=20)

        # Price and GST row
        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=(15, 0))

        # Price
        price_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        price_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(price_frame, text="Price *").pack(anchor="w")
        self.price_var = ctk.StringVar()
        ctk.CTkEntry(price_frame, textvariable=self.price_var, width=180).pack()

        # GST Rate
        gst_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        gst_frame.pack(side="left", fill="x", expand=True, padx=(20, 0))
        ctk.CTkLabel(gst_frame, text="GST Rate *").pack(anchor="w")
        self.gst_var = ctk.StringVar(value="18")
        gst_values = [f"{r}%" for r in GST_RATES]
        ctk.CTkComboBox(gst_frame, variable=self.gst_var, values=gst_values, width=180).pack()

        # Unit and Stock row
        row_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        row_frame2.pack(fill="x", padx=20, pady=(15, 0))

        # Unit
        unit_frame = ctk.CTkFrame(row_frame2, fg_color="transparent")
        unit_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(unit_frame, text="Unit").pack(anchor="w")
        self.unit_var = ctk.StringVar(value="NOS")
        ctk.CTkComboBox(unit_frame, variable=self.unit_var, values=UNITS, width=180).pack()

        # Initial Stock (only for new products)
        if not self.product:
            stock_frame = ctk.CTkFrame(row_frame2, fg_color="transparent")
            stock_frame.pack(side="left", fill="x", expand=True, padx=(20, 0))
            ctk.CTkLabel(stock_frame, text="Initial Stock").pack(anchor="w")
            self.stock_var = ctk.StringVar(value="0")
            ctk.CTkEntry(stock_frame, textvariable=self.stock_var, width=180).pack()

        # Low Stock Alert
        ctk.CTkLabel(self, text="Low Stock Alert").pack(pady=(15, 5), padx=20, anchor="w")
        self.alert_var = ctk.StringVar(value="10")
        ctk.CTkEntry(self, textvariable=self.alert_var, width=400).pack(padx=20)

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
        self.name_var.set(self.product.name)
        self.barcode_var.set(self.product.barcode or "")
        self.hsn_var.set(self.product.hsn_code or "")
        self.price_var.set(str(self.product.price))
        self.gst_var.set(f"{int(self.product.gst_rate)}%")
        self.unit_var.set(self.product.unit)
        self.alert_var.set(str(self.product.low_stock_alert))

    def _save(self):
        """Save product"""
        # Validate
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Product name is required")
            return

        try:
            price = float(self.price_var.get())
            if price < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Invalid price")
            return

        # Validate HSN
        hsn = self.hsn_var.get().strip()
        if hsn:
            valid, error = validate_hsn(hsn)
            if not valid:
                messagebox.showerror("Error", error)
                return

        # Get GST rate
        gst_str = self.gst_var.get().replace("%", "")
        gst_rate = float(gst_str)

        # Get alert level
        try:
            alert = float(self.alert_var.get() or 10)
        except ValueError:
            alert = 10

        if self.product:
            # Update existing
            self.product.name = name
            self.product.barcode = self.barcode_var.get().strip() or None
            self.product.hsn_code = hsn or None
            self.product.price = price
            self.product.gst_rate = gst_rate
            self.product.unit = self.unit_var.get()
            self.product.low_stock_alert = alert
            self.product.save()
        else:
            # Create new
            try:
                stock = float(self.stock_var.get() or 0)
            except ValueError:
                stock = 0

            product = Product(
                name=name,
                barcode=self.barcode_var.get().strip() or None,
                hsn_code=hsn or None,
                price=price,
                gst_rate=gst_rate,
                unit=self.unit_var.get(),
                stock_qty=stock,
                low_stock_alert=alert
            )
            product.save()

        self.destroy()


class StockDialog(ctk.CTkToplevel):
    """Dialog for stock adjustment"""

    def __init__(self, parent, product: Product):
        super().__init__(parent)
        self.product = product

        self.title(f"Adjust Stock - {product.name}")
        self.geometry("350x300")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Current stock
        ctk.CTkLabel(
            self,
            text=f"Current Stock: {self.product.stock_qty} {self.product.unit}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(30, 20))

        # Adjustment type
        ctk.CTkLabel(self, text="Adjustment Type").pack(pady=(10, 5), padx=20, anchor="w")
        self.type_var = ctk.StringVar(value="add")
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack(padx=20, anchor="w")

        ctk.CTkRadioButton(
            type_frame, text="Add Stock", variable=self.type_var, value="add"
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            type_frame, text="Remove Stock", variable=self.type_var, value="remove"
        ).pack(side="left")

        # Quantity
        ctk.CTkLabel(self, text="Quantity").pack(pady=(20, 5), padx=20, anchor="w")
        self.qty_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.qty_var, width=300).pack(padx=20)

        # Reason
        ctk.CTkLabel(self, text="Reason").pack(pady=(15, 5), padx=20, anchor="w")
        self.reason_var = ctk.StringVar(value="ADJUSTMENT")
        ctk.CTkComboBox(
            self,
            variable=self.reason_var,
            values=["PURCHASE", "ADJUSTMENT", "DAMAGE", "RETURN", "OTHER"],
            width=300
        ).pack(padx=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=30)

        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_frame, text="Update", command=self._save).pack(side="right")

    def _save(self):
        """Save stock adjustment"""
        try:
            qty = float(self.qty_var.get())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return

        if self.type_var.get() == "remove":
            qty = -qty

        self.product.update_stock(qty, self.reason_var.get())
        self.destroy()
