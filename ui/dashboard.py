"""Dashboard screen with quick stats"""
import customtkinter as ctk
from datetime import date, timedelta
from database.models import Invoice
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
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # Stats Cards Row 1 - Today's stats
        stats_row1 = ctk.CTkFrame(self, fg_color="transparent")
        stats_row1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        stats_row1.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.today_sales_card = self._create_stat_card(
            stats_row1, "Today's Sales", "0.00", col=0, color="green"
        )
        self.today_invoices_card = self._create_stat_card(
            stats_row1, "Invoices Today", "0", col=1
        )
        self.month_sales_card = self._create_stat_card(
            stats_row1, "This Month", "0.00", col=2, color="blue"
        )
        self.low_stock_card = self._create_stat_card(
            stats_row1, "Low Stock", "0", col=3, color="orange"
        )

        # Quick Actions
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 10), padx=15, anchor="w")

        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            buttons_frame,
            text="New Bill (F1)",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            command=lambda: self.controller.show_frame("billing")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons_frame,
            text="Add Product",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self.controller.show_frame("products")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons_frame,
            text="View Invoices",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            fg_color="purple",
            hover_color="darkviolet",
            command=lambda: self.controller.show_frame("invoices")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons_frame,
            text="Reports",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            fg_color="gray",
            hover_color="darkgray",
            command=lambda: self.controller.show_frame("reports")
        ).pack(side="left")

        # Bottom section - Recent Invoices and Low Stock side by side
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Recent Invoices (left)
        recent_frame = ctk.CTkFrame(bottom_frame)
        recent_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(
            recent_frame,
            text="Recent Invoices",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")

        self.recent_invoices_list = ctk.CTkScrollableFrame(recent_frame, height=200)
        self.recent_invoices_list.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Low Stock Alert (right)
        self.low_stock_frame = ctk.CTkFrame(bottom_frame)
        self.low_stock_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ctk.CTkLabel(
            self.low_stock_frame,
            text="Low Stock Alert",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")

        self.low_stock_list = ctk.CTkScrollableFrame(self.low_stock_frame, height=200)
        self.low_stock_list.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _create_stat_card(self, parent, title: str, value: str, col: int, color: str = None) -> dict:
        """Create a statistics card"""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="ew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        title_label.pack(pady=(10, 3), padx=15)

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=color if color else None
        )
        value_label.pack(pady=(0, 10), padx=15)

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

        # This month's sales
        today = date.today()
        month_start = today.replace(day=1)
        month_sales = self.invoice_service.get_sales_by_date_range(month_start, today)
        self.month_sales_card['value'].configure(
            text=format_currency(month_sales.get('total_sales', 0), "")
        )

        # Low stock
        low_stock = self.stock_service.get_low_stock_products()
        self.low_stock_card['value'].configure(text=str(len(low_stock)))

        # Update recent invoices list
        for widget in self.recent_invoices_list.winfo_children():
            widget.destroy()

        recent_invoices = Invoice.get_by_date_range(today - timedelta(days=7), today)
        if recent_invoices:
            for inv in recent_invoices[:10]:  # Show last 10
                item_frame = ctk.CTkFrame(self.recent_invoices_list, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)
                item_frame.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    item_frame,
                    text=inv.invoice_number,
                    font=ctk.CTkFont(size=11),
                    text_color="blue"
                ).pack(side="left", padx=(0, 10))

                ctk.CTkLabel(
                    item_frame,
                    text=inv.customer_name or "Cash",
                    font=ctk.CTkFont(size=11)
                ).pack(side="left")

                ctk.CTkLabel(
                    item_frame,
                    text=format_currency(inv.grand_total),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="green"
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                self.recent_invoices_list,
                text="No recent invoices",
                text_color="gray"
            ).pack(pady=20)

        # Update low stock list
        for widget in self.low_stock_list.winfo_children():
            widget.destroy()

        if low_stock:
            for product in low_stock[:10]:  # Show top 10
                item_frame = ctk.CTkFrame(self.low_stock_list, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    item_frame,
                    text=product.name[:25],
                    font=ctk.CTkFont(size=11)
                ).pack(side="left")

                ctk.CTkLabel(
                    item_frame,
                    text=f"{product.stock_qty} {product.unit}",
                    font=ctk.CTkFont(size=11),
                    text_color="orange"
                ).pack(side="right")
        else:
            ctk.CTkLabel(
                self.low_stock_list,
                text="All items in stock",
                text_color="green"
            ).pack(pady=20)
