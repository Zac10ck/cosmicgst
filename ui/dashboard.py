"""Dashboard screen with quick stats"""
import customtkinter as ctk
from datetime import date
from services.invoice_service import InvoiceService
from services.stock_service import StockService
from utils.formatters import format_currency


class DashboardFrame(ctk.CTkFrame):
    """Dashboard with today's sales and quick stats"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.invoice_service = InvoiceService()
        self.stock_service = StockService()

        self._create_widgets()

    def _create_widgets(self):
        """Create dashboard widgets"""
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        # Stats Cards Row 1
        self.today_sales_card = self._create_stat_card(
            "Today's Sales", "0.00", row=1, col=0
        )
        self.today_invoices_card = self._create_stat_card(
            "Invoices Today", "0", row=1, col=1
        )
        self.low_stock_card = self._create_stat_card(
            "Low Stock Items", "0", row=1, col=2, color="orange"
        )

        # Quick Actions
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, columnspan=3, pady=20, sticky="new")

        ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15), padx=20, anchor="w")

        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            buttons_frame,
            text="New Bill",
            font=ctk.CTkFont(size=14),
            height=50,
            width=150,
            command=lambda: self.controller.show_frame("billing")
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            buttons_frame,
            text="Add Product",
            font=ctk.CTkFont(size=14),
            height=50,
            width=150,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self.controller.show_frame("products")
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            buttons_frame,
            text="View Reports",
            font=ctk.CTkFont(size=14),
            height=50,
            width=150,
            fg_color="gray",
            hover_color="darkgray",
            command=lambda: self.controller.show_frame("reports")
        ).pack(side="left")

        # Low Stock List
        self.low_stock_frame = ctk.CTkFrame(self)
        self.low_stock_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.low_stock_frame,
            text="Low Stock Alert",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 10), padx=20, anchor="w")

        self.low_stock_list = ctk.CTkScrollableFrame(
            self.low_stock_frame,
            height=150
        )
        self.low_stock_list.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _create_stat_card(self, title: str, value: str, row: int, col: int, color: str = None) -> dict:
        """Create a statistics card"""
        card = ctk.CTkFrame(self)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        title_label.pack(pady=(15, 5), padx=20)

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color if color else None
        )
        value_label.pack(pady=(0, 15), padx=20)

        return {'card': card, 'title': title_label, 'value': value_label}

    def refresh(self):
        """Refresh dashboard data"""
        # Today's sales
        daily_sales = self.invoice_service.get_daily_sales(date.today())

        self.today_sales_card['value'].configure(
            text=format_currency(daily_sales['total_sales'], "")
        )
        self.today_invoices_card['value'].configure(
            text=str(daily_sales['invoice_count'])
        )

        # Low stock
        low_stock = self.stock_service.get_low_stock_products()
        self.low_stock_card['value'].configure(text=str(len(low_stock)))

        # Update low stock list
        for widget in self.low_stock_list.winfo_children():
            widget.destroy()

        if low_stock:
            for product in low_stock[:10]:  # Show top 10
                item_frame = ctk.CTkFrame(self.low_stock_list, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    item_frame,
                    text=product.name,
                    font=ctk.CTkFont(size=12)
                ).pack(side="left")

                ctk.CTkLabel(
                    item_frame,
                    text=f"Stock: {product.stock_qty} {product.unit}",
                    font=ctk.CTkFont(size=12),
                    text_color="orange"
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                self.low_stock_list,
                text="No low stock items",
                text_color="gray"
            ).pack(pady=20)
