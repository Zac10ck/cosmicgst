"""Dashboard blueprint"""
from flask import Blueprint, render_template
from flask_login import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # TODO: Add statistics from database
    stats = {
        'today_sales': 0,
        'today_invoices': 0,
        'monthly_sales': 0,
        'pending_quotations': 0,
        'low_stock_items': 0,
        'total_customers': 0
    }

    recent_invoices = []
    low_stock_products = []

    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_invoices=recent_invoices,
        low_stock_products=low_stock_products
    )
