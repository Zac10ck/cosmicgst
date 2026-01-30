/**
 * Billing Cart Management
 * Handles product search, cart operations, and invoice creation
 */

class BillingCart {
    constructor() {
        this.items = [];
        this.customer = null;
        this.discount = 0;
        this.totals = {
            subtotal: 0,
            cgst_total: 0,
            sgst_total: 0,
            igst_total: 0,
            grand_total: 0
        };

        // E-Way bill threshold (Rs. 50,000)
        this.EWAY_THRESHOLD = 50000;

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateDisplay();
    }

    bindEvents() {
        // Product search
        const searchInput = document.getElementById('product-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.searchProducts(e.target.value);
            }, 300));

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    // Try to add by barcode if exact match
                    this.addByBarcode(e.target.value);
                }
            });
        }

        // Barcode input
        const barcodeInput = document.getElementById('barcode-input');
        if (barcodeInput) {
            barcodeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addByBarcode(e.target.value);
                    e.target.value = '';
                }
            });
        }

        // Customer search
        const customerSearch = document.getElementById('customer-search');
        if (customerSearch) {
            customerSearch.addEventListener('input', this.debounce((e) => {
                this.searchCustomers(e.target.value);
            }, 300));
        }

        // Discount input
        const discountInput = document.getElementById('discount-input');
        if (discountInput) {
            discountInput.addEventListener('input', (e) => {
                this.discount = parseFloat(e.target.value) || 0;
                this.calculateTotals();
            });
        }

        // Submit invoice
        const submitBtn = document.getElementById('submit-invoice');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitInvoice());
        }

        // Clear cart
        const clearBtn = document.getElementById('clear-cart');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearCart());
        }

        // E-Way bill transport distance - calculate validity
        const distanceInput = document.getElementById('transport-distance');
        if (distanceInput) {
            distanceInput.addEventListener('input', (e) => {
                this.updateEwayValidity(parseInt(e.target.value) || 0);
            });
        }

        // Vehicle number - format to uppercase with validation
        const vehicleInput = document.getElementById('vehicle-number');
        if (vehicleInput) {
            vehicleInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase();
            });
            vehicleInput.addEventListener('blur', (e) => {
                this.validateVehicleNumber(e.target);
            });
        }

        // Transporter ID - format to uppercase with validation
        const transporterInput = document.getElementById('transporter-id');
        if (transporterInput) {
            transporterInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase();
                this.validateGSTIN(e.target);
            });
        }

        // Transport mode change - show/hide port code
        const transportModeSelect = document.getElementById('transport-mode');
        if (transportModeSelect) {
            transportModeSelect.addEventListener('change', (e) => {
                this.togglePortCodeField(e.target.value);
            });
        }

        // Over-dimensional cargo checkbox - update validity
        const odcCheckbox = document.getElementById('is-over-dimensional');
        if (odcCheckbox) {
            odcCheckbox.addEventListener('change', () => {
                const distance = parseInt(document.getElementById('transport-distance')?.value) || 0;
                this.updateEwayValidity(distance);
            });
        }

        // Buyer state code dropdown
        const buyerStateSelect = document.getElementById('buyer-state-code');
        if (buyerStateSelect) {
            buyerStateSelect.addEventListener('change', () => {
                this.calculateTotals();
            });
        }
    }

    validateVehicleNumber(input) {
        const value = input.value.replace(/[-\s]/g, '').toUpperCase();
        const errorDiv = document.getElementById('vehicle-number-error');

        if (!value) {
            input.classList.remove('is-invalid');
            if (errorDiv) errorDiv.textContent = '';
            return true;
        }

        // Pattern: 2 letters + 1-2 digits + 1-3 letters + 1-4 digits
        const pattern = /^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$/;

        if (!pattern.test(value)) {
            input.classList.add('is-invalid');
            if (errorDiv) errorDiv.textContent = 'Invalid format. Expected: KL-01-AB-1234';
            return false;
        }

        input.classList.remove('is-invalid');
        if (errorDiv) errorDiv.textContent = '';
        return true;
    }

    validateGSTIN(input) {
        const value = input.value.toUpperCase().trim();
        const errorDiv = document.getElementById('transporter-id-error');

        if (!value) {
            input.classList.remove('is-invalid');
            if (errorDiv) errorDiv.textContent = '';
            return true;
        }

        // GSTIN pattern: 2 digits + 5 letters + 4 digits + 1 letter + 1 alphanumeric + Z + 1 alphanumeric
        const pattern = /^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$/;

        if (value.length !== 15) {
            input.classList.add('is-invalid');
            if (errorDiv) errorDiv.textContent = 'GSTIN must be 15 characters';
            return false;
        }

        if (!pattern.test(value)) {
            input.classList.add('is-invalid');
            if (errorDiv) errorDiv.textContent = 'Invalid GSTIN format';
            return false;
        }

        input.classList.remove('is-invalid');
        if (errorDiv) errorDiv.textContent = '';
        return true;
    }

    togglePortCodeField(transportMode) {
        const portCodeGroup = document.getElementById('port-code-group');
        if (portCodeGroup) {
            if (transportMode === 'Air' || transportMode === 'Ship') {
                portCodeGroup.style.display = 'block';
            } else {
                portCodeGroup.style.display = 'none';
            }
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async searchProducts(query) {
        if (query.length < 1) {
            this.hideSearchResults();
            return;
        }

        try {
            const response = await fetch(`/billing/api/products/search?q=${encodeURIComponent(query)}`);
            const products = await response.json();
            this.showSearchResults(products);
        } catch (error) {
            console.error('Error searching products:', error);
        }
    }

    showSearchResults(products) {
        const resultsDiv = document.getElementById('search-results');
        if (!resultsDiv) return;

        if (products.length === 0) {
            resultsDiv.innerHTML = '<div class="list-group-item text-muted">No products found</div>';
        } else {
            resultsDiv.innerHTML = products.map(p => `
                <a href="#" class="list-group-item list-group-item-action" onclick="cart.addProduct(${JSON.stringify(p).replace(/"/g, '&quot;')}); return false;">
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>${this.escapeHtml(p.name)}</strong>
                            ${p.barcode ? `<br><small class="text-muted">${this.escapeHtml(p.barcode)}</small>` : ''}
                        </div>
                        <div class="text-end">
                            <strong>Rs. ${p.price.toFixed(2)}</strong>
                            <br><small class="text-muted">Stock: ${p.stock_qty}</small>
                        </div>
                    </div>
                </a>
            `).join('');
        }
        resultsDiv.style.display = 'block';
    }

    hideSearchResults() {
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    }

    async addByBarcode(barcode) {
        if (!barcode) return;

        try {
            const response = await fetch(`/billing/api/products/barcode/${encodeURIComponent(barcode)}`);
            if (response.ok) {
                const product = await response.json();
                this.addProduct(product);
                document.getElementById('product-search').value = '';
                this.hideSearchResults();
            } else {
                // Try search instead
                this.searchProducts(barcode);
            }
        } catch (error) {
            console.error('Error fetching product by barcode:', error);
        }
    }

    addProduct(product) {
        // Check if product already in cart
        const existingIndex = this.items.findIndex(item => item.product_id === product.id);

        if (existingIndex >= 0) {
            // Increment quantity
            this.items[existingIndex].qty += 1;
        } else {
            // Add new item
            this.items.push({
                product_id: product.id,
                product_name: product.name,
                hsn_code: product.hsn_code || '',
                qty: 1,
                unit: product.unit || 'NOS',
                rate: product.price,
                gst_rate: product.gst_rate || 18
            });
        }

        this.calculateTotals();
        this.hideSearchResults();

        // Clear search input if it exists (may not exist if using modal)
        const searchInput = document.getElementById('product-search');
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
        }
    }

    updateQuantity(index, qty) {
        qty = parseFloat(qty);
        if (qty <= 0) {
            this.removeItem(index);
        } else {
            this.items[index].qty = qty;
            this.calculateTotals();
        }
    }

    updateRate(index, rate) {
        rate = parseFloat(rate);
        if (rate >= 0) {
            this.items[index].rate = rate;
            this.calculateTotals();
        }
    }

    removeItem(index) {
        this.items.splice(index, 1);
        this.calculateTotals();
    }

    async searchCustomers(query) {
        if (query.length < 1) {
            this.hideCustomerResults();
            return;
        }

        try {
            const response = await fetch(`/billing/api/customers/search?q=${encodeURIComponent(query)}`);
            const customers = await response.json();
            this.showCustomerResults(customers);
        } catch (error) {
            console.error('Error searching customers:', error);
        }
    }

    showCustomerResults(customers) {
        const resultsDiv = document.getElementById('customer-results');
        if (!resultsDiv) return;

        if (customers.length === 0) {
            resultsDiv.innerHTML = '<div class="list-group-item text-muted">No customers found</div>';
        } else {
            resultsDiv.innerHTML = customers.map(c => `
                <a href="#" class="list-group-item list-group-item-action" onclick="cart.selectCustomer(${JSON.stringify(c).replace(/"/g, '&quot;')}); return false;">
                    <strong>${this.escapeHtml(c.name)}</strong>
                    ${c.phone ? `<br><small class="text-muted">${this.escapeHtml(c.phone)}</small>` : ''}
                    ${c.gstin ? `<br><small class="text-muted">GSTIN: ${this.escapeHtml(c.gstin)}</small>` : ''}
                </a>
            `).join('');
        }
        resultsDiv.style.display = 'block';
    }

    hideCustomerResults() {
        const resultsDiv = document.getElementById('customer-results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    }

    selectCustomer(customer) {
        this.customer = customer;
        document.getElementById('customer-search').value = customer.name;

        // Check credit status
        let creditWarning = '';
        if (customer.credit_limit > 0) {
            const usedPercent = (customer.credit_balance / customer.credit_limit) * 100;
            if (customer.credit_balance >= customer.credit_limit) {
                creditWarning = `<div class="alert alert-danger py-1 mt-2 mb-0 small">
                    <i class="bi bi-exclamation-triangle-fill me-1"></i>
                    <strong>Credit Limit Exceeded!</strong><br>
                    Balance: Rs.${customer.credit_balance.toFixed(2)} / Limit: Rs.${customer.credit_limit.toFixed(2)}
                </div>`;
            } else if (usedPercent >= 80) {
                creditWarning = `<div class="alert alert-warning py-1 mt-2 mb-0 small">
                    <i class="bi bi-exclamation-circle me-1"></i>
                    Credit ${usedPercent.toFixed(0)}% used: Rs.${customer.credit_balance.toFixed(2)} / Rs.${customer.credit_limit.toFixed(2)}
                </div>`;
            }
        } else if (customer.credit_balance > 0) {
            creditWarning = `<div class="alert alert-secondary py-1 mt-2 mb-0 small">
                Outstanding: Rs.${customer.credit_balance.toFixed(2)}
            </div>`;
        }

        document.getElementById('selected-customer-info').innerHTML = `
            <div class="alert alert-info py-2 mb-0">
                <strong>${this.escapeHtml(customer.name)}</strong>
                ${customer.phone ? `<br><small>${this.escapeHtml(customer.phone)}</small>` : ''}
                ${customer.gstin ? `<br><small>GSTIN: ${this.escapeHtml(customer.gstin)}</small>` : ''}
                <button type="button" class="btn-close btn-sm float-end" onclick="cart.clearCustomer()"></button>
            </div>
            ${creditWarning}
        `;
        this.hideCustomerResults();
        this.calculateTotals(); // Recalculate for state-based GST
    }

    clearCustomer() {
        this.customer = null;
        document.getElementById('customer-search').value = '';
        document.getElementById('selected-customer-info').innerHTML = '';
        this.calculateTotals();
    }

    // Alias for selectCustomer - used by modal-based customer selection
    setCustomer(customer) {
        if (customer) {
            this.customer = customer;
            this.calculateTotals();
        } else {
            this.clearCustomer();
        }
    }

    async calculateTotals() {
        if (this.items.length === 0) {
            this.totals = {
                subtotal: 0,
                cgst_total: 0,
                sgst_total: 0,
                igst_total: 0,
                grand_total: 0
            };
            this.updateDisplay();
            return;
        }

        try {
            const response = await fetch('/billing/api/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    items: this.items,
                    buyer_state_code: this.customer?.state_code || null,
                    discount: this.discount
                })
            });

            const result = await response.json();
            this.totals = {
                subtotal: result.subtotal,
                cgst_total: result.cgst_total,
                sgst_total: result.sgst_total,
                igst_total: result.igst_total,
                grand_total: result.grand_total
            };

            // Update items with calculated values
            if (result.items) {
                this.items = result.items;
            }

            this.updateDisplay();
        } catch (error) {
            console.error('Error calculating totals:', error);
        }
    }

    updateDisplay() {
        // Update cart items table
        const tbody = document.getElementById('cart-items');
        if (tbody) {
            if (this.items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-muted py-4">
                            <i class="bi bi-cart" style="font-size: 2rem;"></i>
                            <p class="mb-0 mt-2">Cart is empty. Search for products above.</p>
                        </td>
                    </tr>
                `;
            } else {
                tbody.innerHTML = this.items.map((item, index) => `
                    <tr>
                        <td title="${this.escapeHtml(item.product_name)}">
                            <strong>${this.escapeHtml(item.product_name)}</strong>
                            <br><small class="text-muted">${item.hsn_code || '-'}</small>
                        </td>
                        <td>
                            <input type="number" class="form-control form-control-sm text-center"
                                   value="${item.qty}" min="0.01" step="0.01"
                                   onchange="cart.updateQuantity(${index}, this.value)">
                        </td>
                        <td class="text-center">${item.unit}</td>
                        <td>
                            <input type="number" class="form-control form-control-sm text-end"
                                   value="${item.rate.toFixed(2)}" min="0" step="0.01"
                                   onchange="cart.updateRate(${index}, this.value)">
                        </td>
                        <td class="text-end">${(item.taxable_value || item.qty * item.rate).toFixed(2)}</td>
                        <td class="text-center"><span class="badge bg-secondary">${item.gst_rate}%</span></td>
                        <td class="text-end fw-bold">${(item.total || (item.qty * item.rate * (1 + item.gst_rate/100))).toFixed(2)}</td>
                        <td class="text-center">
                            <button type="button" class="btn btn-sm btn-outline-danger" onclick="cart.removeItem(${index})" title="Remove">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        }

        // Update totals
        document.getElementById('subtotal').textContent = this.totals.subtotal.toFixed(2);
        document.getElementById('cgst-total').textContent = this.totals.cgst_total.toFixed(2);
        document.getElementById('sgst-total').textContent = this.totals.sgst_total.toFixed(2);
        document.getElementById('igst-total').textContent = this.totals.igst_total.toFixed(2);
        document.getElementById('grand-total').textContent = this.totals.grand_total.toFixed(2);

        // Show/hide CGST/SGST vs IGST rows
        const cgstRow = document.getElementById('cgst-row');
        const sgstRow = document.getElementById('sgst-row');
        const igstRow = document.getElementById('igst-row');

        if (this.totals.igst_total > 0) {
            cgstRow.style.display = 'none';
            sgstRow.style.display = 'none';
            igstRow.style.display = '';
        } else {
            cgstRow.style.display = '';
            sgstRow.style.display = '';
            igstRow.style.display = 'none';
        }

        // Update item count
        const itemCount = document.getElementById('item-count');
        if (itemCount) {
            itemCount.textContent = this.items.length;
        }

        // Check e-Way bill requirement
        this.checkEwayBillRequired();
    }

    checkEwayBillRequired() {
        const badge = document.getElementById('eway-threshold-badge');
        const section = document.getElementById('ewayBillSection');

        if (!badge) return;

        if (this.totals.grand_total >= this.EWAY_THRESHOLD) {
            badge.style.display = 'inline-block';
            // Auto-expand the e-Way bill section
            if (section && !section.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(section, { show: true });
            }
        } else {
            badge.style.display = 'none';
        }
    }

    updateEwayValidity(distanceKm) {
        const validityInfo = document.getElementById('validity-info');
        if (!validityInfo) return;

        if (distanceKm > 0) {
            const isODC = document.getElementById('is-over-dimensional')?.checked || false;
            let validityDays;

            if (isODC) {
                // ODC: 1 day per 20 km (or part thereof)
                validityDays = Math.max(1, Math.ceil(distanceKm / 20));
                validityInfo.textContent = `E-Way bill validity: ${validityDays} day(s) (ODC: 20 km/day)`;
                validityInfo.className = 'text-warning';
            } else {
                // Regular: 1 day per 100 km (or part thereof)
                validityDays = Math.max(1, Math.ceil(distanceKm / 100));
                validityInfo.textContent = `E-Way bill validity: ${validityDays} day(s)`;
                validityInfo.className = 'text-info';
            }
        } else {
            validityInfo.textContent = '';
        }
    }

    async submitInvoice() {
        if (this.items.length === 0) {
            alert('Cart is empty!');
            return;
        }

        const paymentMode = document.getElementById('payment-mode').value;

        // Get GST options
        const isReverseCharge = document.getElementById('reverse-charge')?.checked || false;

        // Get e-Way bill transport details
        const transportMode = document.getElementById('transport-mode')?.value || 'Road';
        const vehicleNumber = document.getElementById('vehicle-number')?.value || '';
        const transportDistance = parseInt(document.getElementById('transport-distance')?.value) || 0;
        const transporterId = document.getElementById('transporter-id')?.value || '';
        const isOverDimensional = document.getElementById('is-over-dimensional')?.checked || false;
        const portCode = document.getElementById('port-code')?.value || '';
        const buyerStateCodeSelect = document.getElementById('buyer-state-code');
        const buyerStateCode = buyerStateCodeSelect?.value || this.customer?.state_code || '';

        // Validate vehicle number if provided
        const vehicleInput = document.getElementById('vehicle-number');
        if (vehicleNumber && vehicleInput && !this.validateVehicleNumber(vehicleInput)) {
            alert('Please enter a valid vehicle number format (e.g., KL-01-AB-1234)');
            return;
        }

        // Validate transporter GSTIN if provided
        const transporterInput = document.getElementById('transporter-id');
        if (transporterId && transporterInput && !this.validateGSTIN(transporterInput)) {
            alert('Please enter a valid GSTIN for Transporter ID');
            return;
        }

        // Warn if e-Way bill is required but no vehicle number provided
        if (this.totals.grand_total >= this.EWAY_THRESHOLD && !vehicleNumber) {
            if (!confirm('E-Way bill is required for invoices over Rs. ' + this.EWAY_THRESHOLD.toLocaleString() + '.\n\nVehicle number is not provided. Continue anyway?')) {
                return;
            }
        }

        // Warn if Air/Sea transport but no port code
        if ((transportMode === 'Air' || transportMode === 'Ship') && !portCode) {
            if (!confirm(`Port code is recommended for ${transportMode} transport. Continue anyway?`)) {
                return;
            }
        }

        try {
            const response = await fetch('/billing/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    items: this.items,
                    customer_id: this.customer?.id || null,
                    customer_name: this.customer?.name || 'Walk-in Customer',
                    buyer_state_code: buyerStateCode || this.customer?.state_code || null,
                    discount: this.discount,
                    payment_mode: paymentMode,
                    // GST options
                    is_reverse_charge: isReverseCharge,
                    // E-Way bill transport details
                    transport_mode: transportMode,
                    vehicle_number: vehicleNumber,
                    transport_distance: transportDistance,
                    transporter_id: transporterId,
                    is_over_dimensional: isOverDimensional,
                    port_code: portCode
                })
            });

            const result = await response.json();

            if (result.success) {
                // Show success message with payment status
                let message = result.message;
                if (result.credit_warning) {
                    message += '\n\n⚠️ WARNING: ' + result.credit_warning;
                }
                if (result.payment_status === 'UNPAID') {
                    message += '\n\nPayment Status: UNPAID (Credit Sale)';
                }
                if (result.eway_required) {
                    message += '\n\nNote: E-Way bill is required for this invoice.';
                }
                alert(message);
                window.location.href = `/billing/invoices/${result.invoice_id}`;
            } else {
                alert('Error: ' + (result.error || 'Failed to create invoice'));
            }
        } catch (error) {
            console.error('Error creating invoice:', error);
            alert('Error creating invoice. Please try again.');
        }
    }

    clearCart() {
        if (this.items.length > 0 && !confirm('Clear all items from cart?')) {
            return;
        }
        this.items = [];
        this.discount = 0;
        document.getElementById('discount-input').value = '0';
        this.calculateTotals();
    }

    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize cart when DOM is ready
let cart;
document.addEventListener('DOMContentLoaded', () => {
    cart = new BillingCart();
});
