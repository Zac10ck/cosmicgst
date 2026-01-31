"""Dashboard blueprint with analytics and charts"""
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func, extract
from app.extensions import db
from app.models.invoice import Invoice, InvoiceItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.decorators import admin_required

dashboard_bp = Blueprint('dashboard', __name__)


def get_date_range(period='month'):
    """Get date range for different periods"""
    today = date.today()
    if period == 'today':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'month':
        start = date(today.year, today.month, 1)
        return start, today
    elif period == 'year':
        # Financial year (April to March)
        if today.month >= 4:
            start = date(today.year, 4, 1)
        else:
            start = date(today.year - 1, 4, 1)
        return start, today
    return today, today


@dashboard_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard home page with statistics"""
    try:
        today = date.today()
        month_start = date(today.year, today.month, 1)

        # Today's stats
        today_invoices = Invoice.query.filter(
            Invoice.invoice_date == today,
            Invoice.is_cancelled == False
        ).all()
        today_sales = sum(inv.grand_total or 0 for inv in today_invoices)

        # Monthly stats
        monthly_invoices = Invoice.query.filter(
            Invoice.invoice_date >= month_start,
            Invoice.is_cancelled == False
        ).all()
        monthly_sales = sum(inv.grand_total or 0 for inv in monthly_invoices)

        # Pending quotations (DRAFT or SENT status)
        try:
            pending_quotations = Quotation.query.filter(
                Quotation.status.in_(['DRAFT', 'SENT'])
            ).count()
        except Exception:
            pending_quotations = 0

        # Low stock items
        try:
            low_stock_products = Product.query.filter(
                Product.is_active == True,
                Product.stock_qty <= Product.low_stock_alert
            ).order_by(Product.stock_qty).limit(10).all()
        except Exception:
            low_stock_products = []

        # Total customers
        total_customers = Customer.query.filter_by(is_active=True).count()

        # Unpaid invoices
        unpaid_invoices = Invoice.query.filter(
            Invoice.is_cancelled == False,
            Invoice.payment_status.in_(['UNPAID', 'PARTIAL'])
        ).all()
        total_receivables = sum(inv.balance_due or 0 for inv in unpaid_invoices)

        # Recent invoices
        recent_invoices = Invoice.query.filter_by(is_cancelled=False)\
            .order_by(Invoice.created_at.desc()).limit(10).all()

        # Top products this month
        try:
            top_products = db.session.query(
                InvoiceItem.product_name,
                func.sum(InvoiceItem.qty).label('total_qty'),
                func.sum(InvoiceItem.total).label('total_sales')
            ).join(Invoice).filter(
                Invoice.invoice_date >= month_start,
                Invoice.is_cancelled == False
            ).group_by(InvoiceItem.product_name)\
             .order_by(func.sum(InvoiceItem.total).desc()).limit(5).all()
        except Exception:
            top_products = []

        stats = {
            'today_sales': f"₹{today_sales:,.0f}",
            'today_invoices': len(today_invoices),
            'monthly_sales': f"₹{monthly_sales:,.0f}",
            'pending_quotations': pending_quotations,
            'low_stock_items': len(low_stock_products),
            'total_customers': total_customers,
            'total_receivables': f"₹{total_receivables:,.0f}",
            'unpaid_count': len(unpaid_invoices)
        }

        return render_template(
            'dashboard/index.html',
            stats=stats,
            recent_invoices=recent_invoices,
            low_stock_products=low_stock_products,
            top_products=top_products,
            now=datetime.now()
        )
    except Exception as e:
        # Log the error and show a basic dashboard
        import traceback
        print(f"Dashboard error: {e}")
        print(traceback.format_exc())

        # Return basic stats on error
        stats = {
            'today_sales': "₹0",
            'today_invoices': 0,
            'monthly_sales': "₹0",
            'pending_quotations': 0,
            'low_stock_items': 0,
            'total_customers': 0,
            'total_receivables': "₹0",
            'unpaid_count': 0
        }
        return render_template(
            'dashboard/index.html',
            stats=stats,
            recent_invoices=[],
            low_stock_products=[],
            top_products=[],
            now=datetime.now()
        )


@dashboard_bp.route('/api/sales-chart')
@login_required
@admin_required
def sales_chart_data():
    """API endpoint for sales chart data (last 30 days)"""
    today = date.today()
    start_date = today - timedelta(days=29)

    # Get daily sales for last 30 days
    daily_sales = db.session.query(
        Invoice.invoice_date,
        func.sum(Invoice.grand_total).label('total')
    ).filter(
        Invoice.invoice_date >= start_date,
        Invoice.is_cancelled == False
    ).group_by(Invoice.invoice_date).all()

    # Create a dict for easy lookup
    sales_dict = {str(d.invoice_date): float(d.total) for d in daily_sales}

    # Generate all dates and fill in zeros
    labels = []
    data = []
    current = start_date
    while current <= today:
        labels.append(current.strftime('%d %b'))
        data.append(sales_dict.get(str(current), 0))
        current += timedelta(days=1)

    return jsonify({
        'labels': labels,
        'data': data
    })


@dashboard_bp.route('/api/monthly-sales-chart')
@login_required
@admin_required
def monthly_sales_chart_data():
    """API endpoint for monthly sales chart (last 12 months)"""
    today = date.today()

    # Get monthly sales for last 12 months
    monthly_data = []
    for i in range(11, -1, -1):
        # Calculate month
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # Get sales for this month
        sales = db.session.query(
            func.sum(Invoice.grand_total)
        ).filter(
            Invoice.invoice_date.between(month_start, month_end),
            Invoice.is_cancelled == False
        ).scalar() or 0

        monthly_data.append({
            'label': month_start.strftime('%b %Y'),
            'sales': float(sales)
        })

    return jsonify({
        'labels': [d['label'] for d in monthly_data],
        'data': [d['sales'] for d in monthly_data]
    })


@dashboard_bp.route('/api/category-sales-chart')
@login_required
@admin_required
def category_sales_chart_data():
    """API endpoint for sales by category (current month)"""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Get sales by category
    from app.models.category import Category

    category_sales = db.session.query(
        Category.name,
        func.sum(InvoiceItem.total).label('total')
    ).join(Product, Product.category_id == Category.id)\
     .join(InvoiceItem, InvoiceItem.product_id == Product.id)\
     .join(Invoice, Invoice.id == InvoiceItem.invoice_id)\
     .filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False
    ).group_by(Category.name).all()

    # Also get uncategorized sales
    uncategorized = db.session.query(
        func.sum(InvoiceItem.total)
    ).join(Invoice).outerjoin(Product, Product.id == InvoiceItem.product_id)\
     .filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False,
        Product.category_id == None
    ).scalar() or 0

    labels = [c.name for c in category_sales]
    data = [float(c.total) for c in category_sales]

    if uncategorized > 0:
        labels.append('Uncategorized')
        data.append(float(uncategorized))

    return jsonify({
        'labels': labels if labels else ['No Data'],
        'data': data if data else [0]
    })


@dashboard_bp.route('/api/payment-status-chart')
@login_required
@admin_required
def payment_status_chart_data():
    """API endpoint for payment status breakdown"""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    paid = db.session.query(func.sum(Invoice.grand_total)).filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False,
        Invoice.payment_status == 'PAID'
    ).scalar() or 0

    partial = db.session.query(func.sum(Invoice.grand_total)).filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False,
        Invoice.payment_status == 'PARTIAL'
    ).scalar() or 0

    unpaid = db.session.query(func.sum(Invoice.grand_total)).filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False,
        Invoice.payment_status == 'UNPAID'
    ).scalar() or 0

    return jsonify({
        'labels': ['Paid', 'Partial', 'Unpaid'],
        'data': [float(paid), float(partial), float(unpaid)]
    })


@dashboard_bp.route('/api/top-customers')
@login_required
@admin_required
def top_customers_data():
    """API endpoint for top customers this month"""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    top_customers = db.session.query(
        Invoice.customer_name,
        func.count(Invoice.id).label('invoice_count'),
        func.sum(Invoice.grand_total).label('total_sales')
    ).filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False
    ).group_by(Invoice.customer_name)\
     .order_by(func.sum(Invoice.grand_total).desc()).limit(10).all()

    return jsonify({
        'customers': [{
            'name': c.customer_name or 'Walk-in',
            'invoices': c.invoice_count,
            'sales': float(c.total_sales)
        } for c in top_customers]
    })
