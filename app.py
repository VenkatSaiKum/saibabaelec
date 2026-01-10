#!/usr/bin/env python3
"""
Flask Web Application for Electrical Shop Stock Management System
"""

from flask import Flask, render_template, request, jsonify, send_file, g, session, redirect, url_for
from flask_cors import CORS
from products import ProductManager
from stock import StockManager
from billing import BillingManager
from expenses import ExpenseManager
from supplier_bills import SupplierBillManager
from cleanup_old_records import DatabaseCleaner
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
import json
from datetime import datetime
import io
from functools import wraps
import logging

app = Flask(__name__)
app.secret_key = 'saibaba_venkata_secret_key_2026'  # Secret key for session management
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize background scheduler for automatic cleanup - COMMENTED OUT FOR NOW
# scheduler = BackgroundScheduler()

# def run_weekly_cleanup():
#     """Run database cleanup automatically every Sunday at 2 AM"""
#     try:
#         logger.info("Starting automatic weekly database cleanup...")
#         cleaner = DatabaseCleaner()
#         cleaner.cleanup()
#         cleaner.close()
#         logger.info("Weekly cleanup completed successfully")
#     except Exception as e:
#         logger.error(f"Error during weekly cleanup: {e}")

# Schedule cleanup for every Sunday at 2 AM
# scheduler.add_job(
#     func=run_weekly_cleanup,
#     trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
#     id='weekly_cleanup',
#     name='Weekly Database Cleanup',
#     replace_existing=True
# )

# Start scheduler immediately when app starts
# if not scheduler.running:
#     scheduler.start()
#     logger.info("Background scheduler started - automatic cleanup enabled")

def get_managers():
    """Get or create managers for current request"""
    if 'managers' not in g:
        g.managers = {
            'products': ProductManager(),
            'stock': StockManager(),
            'billing': BillingManager(),
            'expenses': ExpenseManager(),
            'supplier_bills': SupplierBillManager()
        }
    return g.managers

@app.teardown_appcontext
def close_managers(error):
    """Close database connections at end of request"""
    managers = g.pop('managers', None)
    if managers:
        for mgr in managers.values():
            mgr.close()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return redirect(url_for('billing_page'))  # Staff can only access billing and expenses
        return f(*args, **kwargs)
    return decorated_function

# ============ AUTHENTICATION ROUTES ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Admin credentials: admin / saibaba99
        # Staff credentials: staff / staff123
        if username == 'admin' and password == 'saibaba99':
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin'
            return redirect(url_for('index'))
        elif username == 'staff' and password == 'staff123':
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'staff'
            return redirect(url_for('billing_page'))  # Staff goes directly to billing
        else:
            return render_template('login.html', error='Invalid username or password')
    
    # If already logged in, redirect to dashboard
    if 'logged_in' in session:
        if session.get('role') == 'staff':
            return redirect(url_for('billing_page'))
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

# ============ DASHBOARD ROUTES ============

@app.route('/')
@login_required
def index():
    """Dashboard home page - admin only"""
    if session.get('role') == 'staff':
        return redirect(url_for('billing_page'))
    return render_template('index.html')

@app.route('/api/dashboard')
@admin_required
def get_dashboard_data():
    """Get dashboard statistics"""
    try:
        mgr = get_managers()
        # Get product stats
        all_products = mgr['products'].get_all_products()
        low_stock = mgr['products'].get_low_stock_products()
        
        # Get sales stats
        sales_summary = mgr['billing'].get_sales_summary()
        total_bills, total_sales, avg_bill, max_bill = sales_summary if sales_summary else (0, 0, 0, 0)
        
        # Get stock report
        stock_report = mgr['stock'].get_stock_report()
        total_inventory_value = sum(item[6] for item in stock_report) if stock_report else 0
        
        data = {
            'total_products': len(all_products) if all_products else 0,
            'low_stock_count': len(low_stock) if low_stock else 0,
            'total_bills': int(total_bills) if total_bills else 0,
            'total_sales': float(total_sales) if total_sales else 0.0,
            'avg_bill_value': float(avg_bill) if avg_bill else 0.0,
            'inventory_value': float(total_inventory_value)
        }
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PRODUCT ROUTES ============

@app.route('/products')
@admin_required
def products_page():
    """Products management page - admin only"""
    return render_template('products.html')

@app.route('/api/products')
@login_required
def get_products():
    """Get all products"""
    try:
        products = get_managers()['products'].get_all_products()
        if not products:
            return jsonify([]), 200
        result = []
        for product in products:
            result.append({
                'id': product[0],
                'name': product[1],
                'category': product[2],
                'unit_price': product[3],
                'quantity': product[4],
                'minimum_stock': product[5],
                'status': 'LOW' if product[4] <= product[5] else 'OK'
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    """Add new product"""
    try:
        data = request.json
        if get_managers()['products'].add_product(
            data['name'],
            data['category'],
            float(data['unit_price']),

            int(data['quantity']),
            int(data['minimum_stock'])
        ):
            return jsonify({'success': True, 'message': 'Product added successfully'}), 201
        else:
            return jsonify({'error': 'Failed to add product'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Update product"""
    try:
        data = request.json
        if get_managers()['products'].update_product(
            product_id,
            name=data.get('name'),
            category=data.get('category'),
            unit_price=float(data['unit_price']) if data.get('unit_price') else None,
            minimum_stock=int(data['minimum_stock']) if data.get('minimum_stock') else None
        ):

            return jsonify({'success': True, 'message': 'Product updated'}), 200
        else:
            return jsonify({'error': 'Failed to update product'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Delete product"""
    try:
        if get_managers()['products'].delete_product(product_id):
            return jsonify({'success': True, 'message': 'Product deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete product'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ STOCK ROUTES ============

@app.route('/stock')

@admin_required
def stock_page():
    """Stock management page - admin only"""
    return render_template('stock.html')

@app.route('/api/stock-report')
@login_required
def get_stock_report():
    """Get stock report with valuations"""
    try:
        report = get_managers()['stock'].get_stock_report()
        if not report:
            return jsonify([]), 200
        
        result = []
        total_value = 0
        for item in report:
            value = item[6]
            total_value += value
            result.append({
                'id': item[0],
                'name': item[1],
                'category': item[2],
                'quantity': item[3],
                'unit_price': item[4],
                'min_stock': item[5],
                'total_value': value,
                'status': 'LOW' if item[3] <= item[5] else 'OK'
            })
        
        return jsonify({
            'items': result,
            'total_inventory_value': total_value
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/add', methods=['POST'])
@login_required
def add_stock():
    """Add stock to product"""
    try:
        data = request.json
        if get_managers()['stock'].add_stock(data['product_id'], int(data['quantity']), data.get('notes', '')):
            return jsonify({'success': True, 'message': 'Stock added'}), 200
        else:
            return jsonify({'error': 'Failed to add stock'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/remove', methods=['POST'])
@login_required
def remove_stock():
    """Remove stock from product"""
    try:
        data = request.json
        if get_managers()['stock'].remove_stock(data['product_id'], int(data['quantity']), data.get('notes', '')):
            return jsonify({'success': True, 'message': 'Stock removed'}), 200
        else:
            return jsonify({'error': 'Failed to remove stock'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/history/<int:product_id>')
@login_required
def get_stock_history(product_id):
    """Get stock movement history"""
    try:
        history = get_managers()['stock'].get_stock_history(product_id, limit=20)
        if not history:
            return jsonify([]), 200
        
        result = []
        for record in history:
            result.append({
                'id': record[0],
                'movement_type': record[2],
                'quantity': record[3],
                'notes': record[4] or 'N/A',
                'created_at': record[5]
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ BILLING ROUTES ============

@app.route('/billing')
@login_required
def billing_page():
    """Billing/invoicing page"""
    return render_template('billing.html')

@app.route('/api/billing/create', methods=['POST'])
@login_required
def create_bill():
    """Create new bill"""
    try:
        data = request.json
        # New format includes product_id, quantity, unit_price, and name
        items_list = [
            (
                item['product_id'], 
                item['quantity'],
                item.get('unit_price'),
                item.get('name')
            ) for item in data['items']
        ]
        
        bill_number = get_managers()['billing'].create_bill(
            data['customer_name'],
            items_list,
            data.get('payment_method', 'CASH'),
            data.get('cash_amount'),
            data.get('upi_amount'),
            data.get('bill_type', 'REGULAR')
        )
        
        if bill_number:
            bill = get_managers()['billing'].get_bill(bill_number)
            if bill is None:
                return jsonify({'error': 'Bill created but could not retrieve details'}), 400
            
            return jsonify({
                'success': True,
                'bill_number': bill_number,
                'bill': {
                    'bill_number': bill.get('bill_number'),
                    'customer_name': bill.get('customer_name'),
                    'total_amount': bill.get('total_amount'),
                    'payment_method': bill.get('payment_method'),
                    'created_at': bill.get('created_at'),
                    'items': bill.get('items', [])
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to create bill'}), 400
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Create bill error: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500

@app.route('/api/bills')
@login_required
def get_bills():
    """Get recent bills with items"""
    try:
        limit = request.args.get('limit', 10, type=int)
        bills = get_managers()['billing'].get_all_bills(limit)
        
        if not bills:
            return jsonify([]), 200
        
        result = []
        for bill in bills:
            bill_number = bill[0]
            bill_detail = get_managers()['billing'].get_bill(bill_number)
            
            # Convert items tuples to dictionaries
            items_data = []
            if bill_detail.get('items'):
                for item in bill_detail['items']:
                    items_data.append({
                        'product_name': item[2],
                        'quantity': item[3],
                        'unit_price': item[4],
                        'total_price': item[5]
                    })
            
            result.append({
                'bill_number': bill_detail['bill_number'],
                'customer_name': bill_detail['customer_name'],
                'total_amount': bill_detail['total_amount'],
                'payment_method': bill_detail['payment_method'],
                'created_at': bill_detail['created_at'],
                'items': items_data
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bills/<bill_number>')
@login_required
def get_bill_detail(bill_number):
    """Get bill details"""
    try:
        bill = get_managers()['billing'].get_bill(bill_number)
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        
        print(f"DEBUG: Bill retrieved: {bill_number}")
        print(f"DEBUG: Items in bill: {bill.get('items')}")
        
        items_data = []
        if bill.get('items'):
            for item in bill['items']:
                print(f"DEBUG: Processing item: {item}")
                items_data.append({
                    'product_name': item[2], 
                    'quantity': item[3], 
                    'unit_price': item[4], 
                    'total_price': item[5]
                })
        
        print(f"DEBUG: Final items_data: {items_data}")
        
        return jsonify({
            'bill_number': bill['bill_number'],
            'customer_name': bill['customer_name'],
            'total_amount': bill['total_amount'],
            'payment_method': bill['payment_method'],
            'created_at': bill['created_at'],
            'items': items_data
        }), 200
    except Exception as e:
        import traceback
        print(f"DEBUG: Error in get_bill_detail: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/daily')
@login_required
def get_daily_sales():
    """Get daily sales - excludes credit and replacement transactions"""
    try:
        date = request.args.get('date')
        bills = get_managers()['billing'].get_daily_sales(date)
        
        if not bills:
            return jsonify({'items': [], 'total': 0.0}), 200
        
        result = []
        total = 0
        for bill in bills:
            bill_num, customer, amount, created_at = bill
            result.append({
                'bill_number': bill_num,
                'customer': customer,
                'amount': amount,
                'time': created_at
            })
            total += amount
        
        return jsonify({'items': result, 'total': total}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/credit')
@login_required
def get_credit_transactions():
    """Get credit transactions (Wholesale customers on credit)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        transactions = get_managers()['billing'].get_credit_transactions(limit)
        
        if not transactions:
            return jsonify([]), 200
        
        result = []
        for txn in transactions:
            result.append({
                'bill_number': txn[0],
                'customer_name': txn[1],
                'total_amount': txn[2],
                'payment_method': txn[3],
                'created_at': txn[4]
            })
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/replacements')
@login_required
def get_replacement_transactions():
    """Get replacement transactions"""
    try:
        limit = request.args.get('limit', 50, type=int)
        transactions = get_managers()['billing'].get_replacement_transactions(limit)
        
        if not transactions:
            return jsonify([]), 200
        
        result = []
        for txn in transactions:
            result.append({
                'bill_number': txn[0],
                'customer_name': txn[1],
                'total_amount': txn[2],
                'created_at': txn[3]
            })
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ REPORTS ROUTES ============

@app.route('/reports')
@login_required
def reports_page():
    """Reports page"""
    return render_template('reports.html')

@app.route('/api/reports/sales-summary')
@login_required
def get_sales_summary():
    """Get sales summary"""
    try:
        summary = get_managers()['billing'].get_sales_summary()
        if summary and summary[0] > 0:
            return jsonify({
                'total_bills': int(summary[0]),
                'total_sales': float(summary[1]),
                'avg_bill_value': float(summary[2]),
                'max_bill_value': float(summary[3])
            }), 200
        else:
            return jsonify({
                'total_bills': 0,
                'total_sales': 0.0,
                'avg_bill_value': 0.0,
                'max_bill_value': 0.0
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/low-stock')
@login_required
def get_low_stock_report():
    """Get low stock products"""
    try:
        low_stock = get_managers()['products'].get_low_stock_products()
        if not low_stock:
            return jsonify([]), 200
        
        result = []
        for product in low_stock:
            result.append({
                'id': product[0],
                'name': product[1],
                'category': product[2],
                'current_quantity': product[4],
                'minimum_stock': product[5],
                'shortage': product[5] - product[4]
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ EXPENSES ROUTES ============

@app.route('/expenses')
@login_required
def expenses_page():
    """Expenses management page"""
    return render_template('expenses.html')

@app.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    """Get expenses for a date"""
    try:
        date = request.args.get('date')
        if date:
            expenses = get_managers()['expenses'].get_expenses_by_date(date)
        else:
            expenses = get_managers()['expenses'].get_all_expenses()
        
        if not expenses:
            return jsonify([]), 200
        
        result = []
        for expense in expenses:
            result.append({
                'id': expense[0],
                'category': expense[1],
                'description': expense[2],
                'amount': expense[3],
                'expense_date': expense[4]
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    """Add new expense"""
    try:
        data = request.json
        if get_managers()['expenses'].add_expense(
            data['category'],
            data['description'],
            float(data['amount']),
            data.get('expense_date')
        ):
            return jsonify({'success': True, 'message': 'Expense added'}), 201
        else:
            return jsonify({'error': 'Failed to add expense'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """Delete expense"""
    try:
        if get_managers()['expenses'].delete_expense(expense_id):
            return jsonify({'success': True, 'message': 'Expense deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete expense'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/daily-summary')
@login_required
def get_daily_expenses_summary():
    """Get daily expenses summary"""
    try:
        date = request.args.get('date')
        summary = get_managers()['expenses'].get_daily_expenses_summary(date)
        total = get_managers()['expenses'].get_total_expenses_today(date)
        
        result = []
        if summary:
            for item in summary:
                result.append({
                    'category': item[0],
                    'count': item[1],
                    'total': item[2]
                })
        
        return jsonify({
            'summary': result,
            'total': total
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ SUPPLIER BILLS ROUTES ============

@app.route('/supplier-bills')
def supplier_bills():
    """Supplier bills page"""
    return render_template('supplier_bills.html')

# Wholesale credit bills (customer credit) page
@app.route('/wholesale-bills')
@admin_required
def wholesale_bills():
    """Wholesale credit bills page"""
    return render_template('wholesale_bills.html')

@app.route('/api/supplier-bills', methods=['GET'])
def get_supplier_bills():
    """Get supplier bills with optional status filter; aggregate when requested"""
    try:
        mgr = get_managers()
        status = request.args.get('status')
        aggregate = request.args.get('aggregate')
        try:
            if aggregate:
                bills = mgr['supplier_bills'].get_supplier_groups(status)
            else:
                bills = mgr['supplier_bills'].get_all_bills(status)
        except Exception as inner_e:
            logger.error(f"Error in supplier bills query: {inner_e}")
            return jsonify({'error': f"Database error: {str(inner_e)}"}), 500
        return jsonify(bills), 200
    except Exception as e:
        logger.error(f"Error in get_supplier_bills: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/supplier-bills/supplier/<supplier_name>', methods=['GET'])
def get_supplier_bills_by_supplier(supplier_name):
    """Get all bills for a supplier with payment history"""
    try:
        mgr = get_managers()
        bills = mgr['supplier_bills'].get_bills_by_supplier(supplier_name)
        return jsonify(bills), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/supplier-bills/supplier/<supplier_name>/pay', methods=['POST'])
def pay_supplier_bills(supplier_name):
    """Record payment for a supplier; cascades across unpaid bills FIFO"""
    try:
        data = request.json or {}
        amount = data.get('payment_amount')
        payment_date = data.get('payment_date') or datetime.now().strftime('%Y-%m-%d')
        notes = data.get('notes', '')

        if amount is None or amount == "":
            success, status_text = True, 'PAID'
            allocations = []
        else:
            success, status_text, allocations = get_managers()['supplier_bills'].add_supplier_payment(
                supplier_name, amount, payment_date, notes
            )

        if success:
            return jsonify({'success': True, 'status': status_text, 'allocations': allocations}), 200
        return jsonify({'error': status_text or 'Failed to record payment'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/supplier-bills', methods=['POST'])
def add_supplier_bill():
    """Add a new supplier bill"""
    try:
        mgr = get_managers()
        data = request.json
        
        bill_id = mgr['supplier_bills'].add_bill(
            data['supplier_name'],
            data['bill_number'],
            data['bill_date'],
            float(data['total_amount']),
            data.get('description', ''),
            data.get('due_date')
        )
        
        return jsonify({'success': True, 'bill_id': bill_id}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/supplier-bills/<int:bill_id>', methods=['GET'])
def get_supplier_bill(bill_id):
    """Get a single supplier bill by ID"""
    try:
        mgr = get_managers()
        bill = mgr['supplier_bills'].get_bill(bill_id)
        if bill:
            # Add payment history
            bill['payment_history'] = mgr['supplier_bills'].get_payment_history(bill_id)
            return jsonify(bill), 200
        return jsonify({'error': 'Bill not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/supplier-bills/<int:bill_id>/pay', methods=['POST'])
def pay_supplier_bill(bill_id):
    """Make a payment towards a supplier bill"""
    try:
        mgr = get_managers()
        data = request.json
        payment_amount = float(data.get('payment_amount', 0))
        payment_date = data.get('payment_date')
        
        if payment_amount > 0:
            success = mgr['supplier_bills'].make_payment(bill_id, payment_amount, payment_date)
        else:
            success = mgr['supplier_bills'].mark_as_paid(bill_id, payment_date)
        
        return jsonify({'success': success}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/supplier-bills/<int:bill_id>', methods=['DELETE'])
def delete_supplier_bill(bill_id):
    """Delete a supplier bill"""
    try:
        mgr = get_managers()
        success = mgr['supplier_bills'].delete_bill(bill_id)
        return jsonify({'success': success}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/supplier-bills/summary', methods=['GET'])
def get_supplier_bills_summary():
    """Get summary statistics for supplier bills"""
    try:
        mgr = get_managers()
        summary = mgr['supplier_bills'].get_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ WHOLESALE CREDIT BILLS ROUTES ============

@app.route('/api/credit-bills', methods=['GET'])
@admin_required
def get_credit_bills():
    """List credit customers aggregated (one row per customer)"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 200, type=int)
        bills = get_managers()['billing'].get_credit_bills(status, limit)
        result = []
        for b in bills:
            customer, bill_count, total, received, balance, first_created, last_created, open_bills, partial_bills, unpaid_bills, primary_bill = b
            if open_bills == 0:
                status_text = 'PAID'
            elif received and received > 0:
                status_text = 'PARTIAL'
            else:
                status_text = 'UNPAID'
            result.append({
                'customer_name': customer,
                'bill_count': bill_count,
                'total_amount': total,
                'received_amount': received,
                'balance': balance,
                'credit_status': status_text,
                'primary_bill_number': primary_bill,
                'first_created_at': first_created,
                'last_created_at': last_created,
                'open_bills': open_bills
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credit-bills/customer/<customer_name>', methods=['GET'])
@admin_required
def get_credit_bills_customer(customer_name):
    """Get all credit bills for a specific customer"""
    try:
        bills = get_managers()['billing'].get_credit_bills_by_customer(customer_name)
        return jsonify(bills), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credit-bills/<bill_number>', methods=['GET'])
@admin_required
def get_credit_bill_detail(bill_number):
    """Get single credit bill with payment history"""
    try:
        bill = get_managers()['billing'].get_credit_bill(bill_number)
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        payments_fmt = []
        for p in bill['payments']:
            payments_fmt.append({
                'id': p[0],
                'payment_amount': p[1],
                'payment_date': p[2],
                'notes': p[3],
                'created_at': p[4]
            })
        bill['payments'] = payments_fmt
        return jsonify(bill), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credit-bills/<bill_number>/pay', methods=['POST'])
@admin_required
def pay_credit_bill(bill_number):
    """Record payment for a credit bill; empty amount marks fully paid"""
    try:
        data = request.json or {}
        amount = data.get('payment_amount')
        notes = data.get('notes', '')
        payment_date = data.get('payment_date') or datetime.now().strftime('%Y-%m-%d')

        if amount is None or amount == "":
            success, status_text = get_managers()['billing'].mark_credit_paid(bill_number, payment_date, notes or 'Settled')
            allocations = []
        else:
            success, status_text, allocations = get_managers()['billing'].add_credit_payment(bill_number, amount, payment_date, notes)

        if success:
            return jsonify({'success': True, 'status': status_text, 'allocations': allocations}), 200
        return jsonify({'error': status_text or 'Failed to record payment'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@admin_required
def delete_transaction(transaction_id):
    """Delete a transaction (credit/replacement bill)"""
    try:
        mgr = get_managers()
        cursor = mgr['billing'].db.cursor
        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        mgr['billing'].db.connection.commit()
        return jsonify({'success': True, 'message': 'Transaction deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credit-bills/summary', methods=['GET'])
@admin_required
def credit_bills_summary():
    """Summary totals for credit bills"""
    try:
        summary = get_managers()['billing'].get_credit_summary()
        if not summary:
            return jsonify({
                'unpaid_count': 0,
                'partial_count': 0,
                'paid_count': 0,
                'total_balance': 0,
                'total_credit': 0
            }), 200
        return jsonify({
            'unpaid_count': summary[0] or 0,
            'partial_count': summary[1] or 0,
            'paid_count': summary[2] or 0,
            'total_balance': float(summary[3] or 0),
            'total_credit': float(summary[4] or 0)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
