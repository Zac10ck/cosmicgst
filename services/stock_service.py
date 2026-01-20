"""Stock/Inventory management service"""
from typing import List, Optional
from database.models import Product, StockLog


class StockService:
    """Service for managing product stock"""

    @staticmethod
    def get_all_products(active_only: bool = True) -> List[Product]:
        """Get all products"""
        return Product.get_all(active_only)

    @staticmethod
    def search_products(query: str) -> List[Product]:
        """Search products by name or barcode"""
        return Product.search(query)

    @staticmethod
    def get_product_by_barcode(barcode: str) -> Optional[Product]:
        """Get product by barcode for quick billing"""
        return Product.get_by_barcode(barcode)

    @staticmethod
    def add_product(
        name: str,
        price: float,
        gst_rate: float = 18.0,
        barcode: str = "",
        hsn_code: str = "",
        unit: str = "NOS",
        stock_qty: float = 0,
        low_stock_alert: float = 10
    ) -> Product:
        """Add a new product"""
        product = Product(
            name=name,
            barcode=barcode,
            hsn_code=hsn_code,
            unit=unit,
            price=price,
            gst_rate=gst_rate,
            stock_qty=stock_qty,
            low_stock_alert=low_stock_alert
        )
        product.save()
        return product

    @staticmethod
    def update_product(product_id: int, **kwargs) -> Optional[Product]:
        """Update product details"""
        product = Product.get_by_id(product_id)
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.save()
        return product

    @staticmethod
    def adjust_stock(
        product_id: int,
        qty_change: float,
        reason: str = "ADJUSTMENT"
    ) -> bool:
        """
        Manually adjust stock (for damage, theft, correction, etc.)

        Args:
            product_id: Product ID
            qty_change: Positive to add, negative to remove
            reason: Reason for adjustment
        """
        product = Product.get_by_id(product_id)
        if not product:
            return False

        product.update_stock(qty_change, reason)
        return True

    @staticmethod
    def add_stock(product_id: int, qty: float, reference: str = "") -> bool:
        """Add stock (purchase/restock)"""
        product = Product.get_by_id(product_id)
        if not product:
            return False

        product.update_stock(qty, f"PURCHASE:{reference}" if reference else "PURCHASE")
        return True

    @staticmethod
    def get_low_stock_products() -> List[Product]:
        """Get products with stock below alert level"""
        return Product.get_low_stock()

    @staticmethod
    def get_stock_report() -> List[dict]:
        """Get stock report for all products"""
        products = Product.get_all(active_only=True)

        report = []
        for p in products:
            report.append({
                'id': p.id,
                'name': p.name,
                'barcode': p.barcode,
                'unit': p.unit,
                'stock_qty': p.stock_qty,
                'low_stock_alert': p.low_stock_alert,
                'is_low': p.stock_qty <= p.low_stock_alert,
                'value': round(p.stock_qty * p.price, 2)
            })

        return report

    @staticmethod
    def get_stock_value() -> dict:
        """Get total stock value"""
        products = Product.get_all(active_only=True)

        total_items = 0
        total_value = 0

        for p in products:
            total_items += p.stock_qty
            total_value += p.stock_qty * p.price

        return {
            'total_items': total_items,
            'total_value': round(total_value, 2),
            'product_count': len(products)
        }

    @staticmethod
    def get_stock_history(product_id: int) -> List[dict]:
        """Get stock movement history for a product"""
        logs = StockLog.get_by_product(product_id)

        history = []
        for log in logs:
            history.append({
                'date': log.created_at,
                'change': log.change_qty,
                'reason': log.reason,
                'reference': log.reference_id
            })

        return history
