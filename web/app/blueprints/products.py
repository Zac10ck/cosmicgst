"""Products blueprint - CRUD operations"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.product import Product, StockLog
from app.models.category import Category
from app.forms.product_forms import ProductForm, CategoryForm

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/')
@login_required
def index():
    """List all products"""
    show_inactive = request.args.get('show_inactive', '0') == '1'
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '').strip()

    query = Product.query

    if not show_inactive:
        query = query.filter_by(is_active=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.barcode.ilike(search_term),
                Product.hsn_code.ilike(search_term)
            )
        )

    products = query.order_by(Product.name).all()
    categories = Category.get_all()

    return render_template(
        'products/index.html',
        products=products,
        categories=categories,
        show_inactive=show_inactive,
        selected_category=category_id,
        search=search
    )


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new product"""
    form = ProductForm()
    form.category_id.choices = [(0, '-- No Category --')] + [
        (c.id, c.name) for c in Category.get_all()
    ]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            barcode=form.barcode.data or '',
            hsn_code=form.hsn_code.data or '',
            unit=form.unit.data,
            price=form.price.data,
            purchase_price=form.purchase_price.data or 0,
            gst_rate=float(form.gst_rate.data),
            stock_qty=form.stock_qty.data or 0,
            low_stock_alert=form.low_stock_alert.data or 10,
            category_id=form.category_id.data if form.category_id.data else None,
            batch_number=form.batch_number.data or '',
            expiry_date=form.expiry_date.data,
            is_active=form.is_active.data
        )
        product.save()
        flash(f'Product "{product.name}" added successfully!', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/form.html', form=form, title='Add Product')


@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit product"""
    product = Product.get_by_id(id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products.index'))

    form = ProductForm(obj=product)
    form.category_id.choices = [(0, '-- No Category --')] + [
        (c.id, c.name) for c in Category.get_all()
    ]
    form.gst_rate.data = str(int(product.gst_rate))

    if form.validate_on_submit():
        product.name = form.name.data
        product.barcode = form.barcode.data or ''
        product.hsn_code = form.hsn_code.data or ''
        product.unit = form.unit.data
        product.price = form.price.data
        product.purchase_price = form.purchase_price.data or 0
        product.gst_rate = float(form.gst_rate.data)
        product.stock_qty = form.stock_qty.data or 0
        product.low_stock_alert = form.low_stock_alert.data or 10
        product.category_id = form.category_id.data if form.category_id.data else None
        product.batch_number = form.batch_number.data or ''
        product.expiry_date = form.expiry_date.data
        product.is_active = form.is_active.data
        product.save()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/form.html', form=form, product=product, title='Edit Product')


@products_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Soft delete product (deactivate)"""
    product = Product.get_by_id(id)
    if product:
        product.is_active = False
        product.save()
        flash(f'Product "{product.name}" has been deactivated', 'success')
    return redirect(url_for('products.index'))


@products_bp.route('/<int:id>/stock-log')
@login_required
def stock_log(id):
    """View stock movement log for a product"""
    product = Product.get_by_id(id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products.index'))

    logs = StockLog.get_by_product(id)
    return render_template('products/stock_log.html', product=product, logs=logs)


# Category routes
@products_bp.route('/categories')
@login_required
def categories():
    """List all categories"""
    show_inactive = request.args.get('show_inactive', '0') == '1'
    categories = Category.get_all(active_only=not show_inactive)
    return render_template('products/categories.html', categories=categories, show_inactive=show_inactive)


@products_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Add new category"""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data or '',
            is_active=form.is_active.data
        )
        category.save()
        flash(f'Category "{category.name}" added successfully!', 'success')
        return redirect(url_for('products.categories'))

    return render_template('products/category_form.html', form=form, title='Add Category')


@products_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Edit category"""
    category = Category.get_by_id(id)
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('products.categories'))

    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data or ''
        category.is_active = form.is_active.data
        category.save()
        flash(f'Category "{category.name}" updated successfully!', 'success')
        return redirect(url_for('products.categories'))

    return render_template('products/category_form.html', form=form, category=category, title='Edit Category')


# API endpoints for AJAX
@products_bp.route('/api/search')
@login_required
def api_search():
    """Search products API for autocomplete"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    products = Product.search(query, limit=10)
    return jsonify([p.to_dict() for p in products])


@products_bp.route('/api/barcode/<barcode>')
@login_required
def api_barcode(barcode):
    """Get product by barcode"""
    product = Product.get_by_barcode(barcode)
    if product:
        return jsonify(product.to_dict())
    return jsonify({'error': 'Product not found'}), 404
