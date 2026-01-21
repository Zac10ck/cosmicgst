"""Dashboard screen with quick stats and charts"""
import customtkinter as ctk
from datetime import date, timedelta
from database.models import Invoice
from services.invoice_service import InvoiceService
from services.stock_service import StockService
from utils.formatters import format_currency

# Matplotlib imports for charts
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class DashboardFrame(ctk.CTkFrame):
    """Dashboard with today's sales, charts, and quick stats"""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.invoice_service = InvoiceService()
        self.stock_service = StockService()

        # Chart period (7 or 30 days)
        self.chart_period = 7

        # Chart canvases for cleanup
        self.sales_canvas = None
        self.payment_canvas = None

        self._create_widgets()

    def _create_widgets(self):
        """Create dashboard widgets"""
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)

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

        # Charts Section
        charts_frame = ctk.CTkFrame(self)
        charts_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)

        # Charts header with period selector
        charts_header = ctk.CTkFrame(charts_frame, fg_color="transparent")
        charts_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            charts_header,
            text="Sales Analytics",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # Period toggle
        period_frame = ctk.CTkFrame(charts_header, fg_color="transparent")
        period_frame.pack(side="right")

        self.period_7_btn = ctk.CTkButton(
            period_frame,
            text="7 Days",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#2980b9",
            command=lambda: self._set_chart_period(7)
        )
        self.period_7_btn.pack(side="left", padx=(0, 5))

        self.period_30_btn = ctk.CTkButton(
            period_frame,
            text="30 Days",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="gray",
            command=lambda: self._set_chart_period(30)
        )
        self.period_30_btn.pack(side="left")

        # Sales trend chart (left)
        self.sales_chart_frame = ctk.CTkFrame(charts_frame)
        self.sales_chart_frame.grid(row=1, column=0, sticky="nsew", padx=(15, 5), pady=(0, 10))

        ctk.CTkLabel(
            self.sales_chart_frame,
            text="Sales Trend",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(5, 0))

        self.sales_chart_container = ctk.CTkFrame(self.sales_chart_frame, fg_color="white", height=180)
        self.sales_chart_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.sales_chart_container.pack_propagate(False)

        # Payment mode chart (right)
        self.payment_chart_frame = ctk.CTkFrame(charts_frame)
        self.payment_chart_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 15), pady=(0, 10))

        ctk.CTkLabel(
            self.payment_chart_frame,
            text="Payment Modes",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(5, 0))

        self.payment_chart_container = ctk.CTkFrame(self.payment_chart_frame, fg_color="white", height=180)
        self.payment_chart_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.payment_chart_container.pack_propagate(False)

        # Quick Actions
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

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
        bottom_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)
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

        self.recent_invoices_list = ctk.CTkScrollableFrame(recent_frame, height=150)
        self.recent_invoices_list.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Low Stock Alert (right)
        self.low_stock_frame = ctk.CTkFrame(bottom_frame)
        self.low_stock_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ctk.CTkLabel(
            self.low_stock_frame,
            text="Low Stock Alert",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")

        self.low_stock_list = ctk.CTkScrollableFrame(self.low_stock_frame, height=150)
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

    def _set_chart_period(self, days: int):
        """Set chart period and refresh"""
        self.chart_period = days

        # Update button colors
        if days == 7:
            self.period_7_btn.configure(fg_color="#2980b9")
            self.period_30_btn.configure(fg_color="gray")
        else:
            self.period_7_btn.configure(fg_color="gray")
            self.period_30_btn.configure(fg_color="#2980b9")

        # Refresh charts
        self._update_charts()

    def _update_charts(self):
        """Update both charts with current data"""
        self._create_sales_trend_chart()
        self._create_payment_mode_chart()

    def _create_sales_trend_chart(self):
        """Create sales trend line chart"""
        # Clear previous chart
        for widget in self.sales_chart_container.winfo_children():
            widget.destroy()

        # Get data
        sales_data = self.invoice_service.get_sales_trend(self.chart_period)

        if not sales_data:
            ctk.CTkLabel(
                self.sales_chart_container,
                text="No data available",
                text_color="gray"
            ).pack(expand=True)
            return

        # Extract data for plotting
        dates = [d['date'].strftime('%d/%m') for d in sales_data]
        totals = [d['total'] for d in sales_data]

        # Create figure
        fig = Figure(figsize=(4, 1.8), dpi=80)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)

        # Plot
        ax.plot(dates, totals, color='#2980b9', linewidth=2, marker='o', markersize=4)
        ax.fill_between(range(len(dates)), totals, alpha=0.3, color='#2980b9')

        # Styling
        ax.set_facecolor('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(axis='both', colors='#666666', labelsize=7)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Show only some x-labels to avoid crowding
        if len(dates) > 10:
            step = len(dates) // 5
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)])

        fig.tight_layout(pad=0.5)

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.sales_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.sales_canvas = canvas

    def _create_payment_mode_chart(self):
        """Create payment mode pie chart"""
        # Clear previous chart
        for widget in self.payment_chart_container.winfo_children():
            widget.destroy()

        # Get data
        end_date = date.today()
        start_date = end_date - timedelta(days=self.chart_period - 1)
        payment_data = self.invoice_service.get_payment_mode_distribution(start_date, end_date)

        if not payment_data or sum(payment_data.values()) == 0:
            ctk.CTkLabel(
                self.payment_chart_container,
                text="No data available",
                text_color="gray"
            ).pack(expand=True)
            return

        # Extract data for plotting
        labels = list(payment_data.keys())
        values = list(payment_data.values())

        # Colors for different payment modes
        colors = {
            'CASH': '#27ae60',
            'UPI': '#3498db',
            'CARD': '#9b59b6',
            'CHEQUE': '#f39c12',
            'CREDIT': '#e74c3c'
        }
        pie_colors = [colors.get(label, '#95a5a6') for label in labels]

        # Create figure
        fig = Figure(figsize=(4, 1.8), dpi=80)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)

        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.0f%%',
            colors=pie_colors,
            startangle=90,
            textprops={'fontsize': 8}
        )

        # Style autopct
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(7)
            autotext.set_fontweight('bold')

        ax.set_facecolor('white')
        fig.tight_layout(pad=0.5)

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.payment_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.payment_canvas = canvas

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

        # Update charts
        self._update_charts()

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
