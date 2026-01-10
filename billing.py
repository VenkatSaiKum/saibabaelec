from database import Database, get_ist_datetime
from datetime import datetime
import os

class BillingManager:
    def __init__(self):
        self.db = Database()

    def create_bill(self, customer_name, items_list, payment_method="CASH", cash_amount=None, upi_amount=None, bill_type="REGULAR"):
        """
        Create a bill/transaction
        items_list: [(product_id, quantity, unit_price, product_name), ...]
        product_id can be 0 for manual items (no stock tracking)
        bill_type: REGULAR, CREDIT, or REPLACEMENT
        """
        if not items_list:
            print("✗ Bill must have at least one item")
            return None

        # Validate bill_type
        if bill_type not in ["REGULAR", "CREDIT", "REPLACEMENT"]:
            bill_type = "REGULAR"

        # Generate bill number
        bill_number = self._generate_bill_number()

        total_amount = 0
        transaction_items = []

        # Validate all items and calculate total
        for item_data in items_list:
            if len(item_data) == 2:
                # Old format: (product_id, quantity)
                product_id, quantity = item_data
                unit_price = None
                product_name = None
            elif len(item_data) == 4:
                # New format: (product_id, quantity, unit_price, product_name)
                product_id, quantity, unit_price, product_name = item_data
            else:
                print(f"✗ Invalid item format")
                continue

            # Ensure product_id is int
            product_id = int(product_id) if product_id else 0

            # If product_id is 0, it's a manual entry (no stock tracking)
            if product_id == 0:
                if not unit_price or not product_name:
                    print("✗ Manual items require unit_price and product_name")
                    continue
                
                # Ensure types for manual items
                quantity = int(quantity)
                unit_price = float(unit_price)
                
                item_total = unit_price * quantity
                total_amount += item_total
                transaction_items.append({
                    'product_id': 0,
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total,
                    'is_manual': True
                })
            else:
                # Regular product - fetch from database
                product = self.db.fetch_one(
                    'SELECT id, name, unit_price, quantity FROM products WHERE id = ?',
                    (product_id,)
                )

                if not product:
                    print(f"✗ Product ID {product_id} not found")
                    return None

                db_product_id, db_product_name, db_unit_price, available_qty = product

                # Ensure types are correct
                quantity = int(quantity)
                available_qty = int(available_qty)
                unit_price = float(unit_price) if unit_price else None
                db_unit_price = float(db_unit_price)

                # Use provided price if given, otherwise use database price
                final_price = unit_price if unit_price else db_unit_price
                final_name = product_name if product_name else db_product_name

                if available_qty < quantity:
                    print(f"✗ Insufficient stock for {final_name}. Available: {available_qty}")
                    return None

                item_total = final_price * quantity
                total_amount += item_total
                transaction_items.append({
                    'product_id': product_id,
                    'product_name': final_name,
                    'quantity': quantity,
                    'unit_price': final_price,
                    'total_price': item_total,
                    'is_manual': False
                })

        # Create transaction
        ist_time = get_ist_datetime()
        is_credit = 1 if bill_type == "CREDIT" else 0
        is_replacement = 1 if bill_type == "REPLACEMENT" else 0
        received_amount = 0 if is_credit else total_amount
        credit_status = 'UNPAID' if is_credit else 'PAID'
        
        transaction_query = '''
            INSERT INTO transactions (customer_name, total_amount, payment_method, bill_number, cash_amount, upi_amount, bill_type, is_credit, is_replacement, received_amount, credit_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        if not self.db.execute_query(transaction_query, (customer_name, total_amount, payment_method, bill_number, cash_amount, upi_amount, bill_type, is_credit, is_replacement, received_amount, credit_status, ist_time)):
            print("✗ Failed to create transaction")
            return None

        # Get transaction ID
        transaction = self.db.fetch_one(
            'SELECT id FROM transactions WHERE bill_number = ?',
            (bill_number,)
        )
        
        if not transaction:
            print("✗ Failed to retrieve transaction ID")
            return None
            
        transaction_id = transaction[0]

        # Insert transaction items and update stock
        for item in transaction_items:
            item_query = '''
                INSERT INTO transaction_items (transaction_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.db.execute_query(item_query, (
                transaction_id,
                item['product_id'],
                item['product_name'],
                item['quantity'],
                item['unit_price'],
                item['total_price']
            ))

            # Update stock only for non-manual items
            if not item['is_manual'] and item['product_id'] > 0:
                stock_update = '''
                    UPDATE products SET quantity = quantity - ? WHERE id = ?
                '''
                self.db.execute_query(stock_update, (item['quantity'], item['product_id']))

                # Record stock movement
                movement_query = '''
                    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id)
                    VALUES (?, ?, ?, ?)
                '''
                self.db.execute_query(movement_query, (
                    item['product_id'],
                    'SALE',
                    item['quantity'],
                    transaction_id
                ))

        print(f"✓ Bill created successfully. Bill #: {bill_number}")
        return bill_number

    def _generate_bill_number(self):
        """Generate unique bill number"""
        ist_time = get_ist_datetime()
        timestamp = ist_time.replace("-", "").replace(":", "").replace(" ", "")[:14]
        return f"BILL-{timestamp}"

    def get_bill(self, bill_number):
        """Get bill details"""
        transaction = self.db.fetch_one(
            'SELECT * FROM transactions WHERE bill_number = ?',
            (bill_number,)
        )
        
        if not transaction:
            return None

        transaction_id = transaction[0]
        items = self.db.fetch_all(
            '''SELECT id, product_id, product_name, quantity, unit_price, total_price
               FROM transaction_items
               WHERE transaction_id = ?''',
            (transaction_id,)
        ) or []

        return {
            'bill_number': transaction[4],
            'customer_name': transaction[1],
            'total_amount': transaction[2],
            'payment_method': transaction[3],
            'created_at': transaction[5],
            'items': items
        }

    def display_bill(self, bill_number):
        """Display formatted bill"""
        bill = self.get_bill(bill_number)
        
        if not bill:
            print(f"Bill {bill_number} not found")
            return

        print("\n" + "="*70)
        print(" "*20 + "ELECTRICAL SHOP INVOICE")
        print("="*70)
        print(f"Bill #: {bill['bill_number']:<40} Date: {bill['created_at']}")
        print(f"Customer: {bill['customer_name']:<55}")
        print("-"*70)
        print(f"{'Item':<30} {'Qty':<8} {'Price':<12} {'Total':<15}")
        print("-"*70)

        for item in bill['items']:
            item_id, product_id, product_name, qty, unit_price, total_price = item
            print(f"{product_name:<30} {qty:<8} ₹{unit_price:<11.2f} ₹{total_price:<14.2f}")

        print("-"*70)
        print(f"{'Total Amount':<50} ₹{bill['total_amount']:.2f}")
        print(f"{'Payment Method':<50} {bill['payment_method']}")
        print("="*70 + "\n")

    def get_all_bills(self, limit=10):
        """Get recent bills"""
        query = '''
            SELECT bill_number, customer_name, total_amount, payment_method, created_at
            FROM transactions
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))

    def display_bill_history(self, limit=10):
        """Display bill history"""
        bills = self.get_all_bills(limit)
        
        if not bills:
            print("No bills found")
            return

        print("\n" + "="*100)
        print(f"{'Bill #':<20} {'Customer':<25} {'Amount':<15} {'Payment':<12} {'Date':<20}")
        print("="*100)

        total_sales = 0
        for bill in bills:
            bill_number, customer, amount, payment, created_at = bill
            total_sales += amount
            print(f"{bill_number:<20} {customer:<25} ₹{amount:<14.2f} {payment:<12} {created_at:<20}")

        print("="*100)
        print(f"Total Sales (Shown): ₹{total_sales:.2f}\n")

    def get_daily_sales(self, date=None):
        """Get sales for a specific date - excludes credit and replacement transactions"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        query = '''
            SELECT bill_number, customer_name, total_amount, created_at
            FROM transactions
            WHERE DATE(created_at) = ? 
            AND is_credit = 0 
            AND is_replacement = 0
            ORDER BY created_at DESC
        '''
        return self.db.fetch_all(query, (date,))

    def get_sales_summary(self):
        """Get sales summary statistics - excludes credit and replacement transactions"""
        query = '''
            SELECT 
                COUNT(*) as total_bills,
                SUM(total_amount) as total_sales,
                AVG(total_amount) as avg_bill_value,
                MAX(total_amount) as max_bill_value
            FROM transactions
            WHERE is_credit = 0 AND is_replacement = 0
        '''
        return self.db.fetch_one(query)
    
    # -------- CREDIT (WHOLESALE) MANAGEMENT ---------
    def get_credit_bills(self, status=None, limit=200):
        """Get credit customers aggregated (one row per customer)"""
        base = '''
            SELECT 
                customer_name,
                COUNT(*) as bill_count,
                SUM(total_amount) as total_amount,
                SUM(received_amount) as received_amount,
                SUM(total_amount - received_amount) as balance,
                MIN(created_at) as first_created,
                MAX(created_at) as last_created,
                SUM(CASE WHEN credit_status != 'PAID' THEN 1 ELSE 0 END) as open_bills,
                SUM(CASE WHEN credit_status = 'PARTIAL' THEN 1 ELSE 0 END) as partial_bills,
                SUM(CASE WHEN credit_status = 'UNPAID' THEN 1 ELSE 0 END) as unpaid_bills,
                (
                    SELECT bill_number 
                    FROM transactions t2 
                    WHERE t2.is_credit = 1 AND t2.customer_name = t.customer_name AND t2.credit_status != 'PAID'
                    ORDER BY t2.created_at ASC, t2.id ASC
                    LIMIT 1
                ) as primary_bill_number
            FROM transactions t
            WHERE is_credit = 1
            GROUP BY customer_name
        '''
        having = []
        params = []
        if status == 'PAID':
            having.append('open_bills = 0')
        elif status == 'PARTIAL':
            having.append('open_bills > 0 AND received_amount > 0')
        elif status == 'UNPAID':
            having.append('open_bills > 0 AND received_amount = 0')
        if having:
            base += " HAVING " + " AND ".join(having)
        base += " ORDER BY last_created DESC LIMIT ?"
        params.append(limit)
        return self.db.fetch_all(base, tuple(params))

    def get_credit_bill(self, bill_number):
        """Get single credit bill with payment history"""
        txn = self.db.fetch_one(
            '''SELECT id, bill_number, customer_name, total_amount, received_amount, credit_status, payment_method, created_at
               FROM transactions WHERE bill_number = ? AND is_credit = 1''',
            (bill_number,)
        )
        if not txn:
            return None
        txn_id = txn[0]
        payments = self.db.fetch_all(
            '''SELECT id, payment_amount, payment_date, notes, created_at
               FROM credit_bill_payments WHERE transaction_id = ? ORDER BY payment_date DESC, id DESC''',
            (txn_id,)
        ) or []
        return {
            'id': txn_id,
            'bill_number': txn[1],
            'customer_name': txn[2],
            'total_amount': txn[3],
            'received_amount': txn[4],
            'credit_status': txn[5],
            'payment_method': txn[6],
            'created_at': txn[7],
            'balance': float(txn[3]) - float(txn[4]),
            'payments': payments
        }

    def get_credit_bills_by_customer(self, customer_name):
        """Get all credit bills for a customer ordered FIFO, include last payment date"""
        bills = self.db.fetch_all(
            '''SELECT 
                   id, bill_number, total_amount, received_amount, credit_status, created_at,
                   (SELECT MAX(payment_date) FROM credit_bill_payments p WHERE p.transaction_id = transactions.id) as last_payment_date
               FROM transactions
               WHERE is_credit = 1 AND customer_name = ?
               ORDER BY created_at ASC, id ASC''',
            (customer_name,)
        ) or []
        result = []
        for b in bills:
            result.append({
                'id': b[0],
                'bill_number': b[1],
                'total_amount': b[2],
                'received_amount': b[3],
                'balance': float(b[2]) - float(b[3]),
                'credit_status': b[4],
                'created_at': b[5],
                'last_payment_date': b[6]
            })
        return result

    def _get_customer_credit_queue(self, customer_name):
        """Get unpaid/partial credit bills for a customer in FIFO order"""
        return self.db.fetch_all(
            '''SELECT id, bill_number, total_amount, received_amount, created_at
               FROM transactions
               WHERE is_credit = 1 AND credit_status != 'PAID' AND customer_name = ?
               ORDER BY created_at ASC, id ASC''',
            (customer_name,)
        ) or []

    def _apply_payment_to_bill(self, txn_id, bill_number, current_received, total_amount, apply_amount, payment_date, notes):
        """Apply payment to a single bill and persist rows"""
        new_received = float(current_received) + apply_amount
        new_status = 'PAID' if new_received + 0.01 >= float(total_amount) else 'PARTIAL'

        insert = '''
            INSERT INTO credit_bill_payments (transaction_id, payment_amount, payment_date, notes)
            VALUES (?, ?, ?, ?)
        '''
        if not self.db.execute_query(insert, (txn_id, apply_amount, payment_date, notes)):
            return False, "Failed to save payment"

        update = '''
            UPDATE transactions
            SET received_amount = ?, credit_status = ?
            WHERE id = ?
        '''
        if not self.db.execute_query(update, (new_received, new_status, txn_id)):
            return False, "Failed to update bill status"

        return True, new_status, new_received

    def add_credit_payment(self, bill_number, payment_amount, payment_date, notes=""):
        """Record a payment towards a credit bill; cascades to other unpaid bills of same customer"""
        bill = self.get_credit_bill(bill_number)
        if not bill:
            return False, "Bill not found", []
        try:
            payment_amount = float(payment_amount)
        except:
            return False, "Invalid amount", []
        if payment_amount <= 0:
            return False, "Payment amount must be positive", []

        queue = self._get_customer_credit_queue(bill['customer_name'])
        remaining = payment_amount
        allocations = []

        for txn in queue:
            txn_id, txn_bill_no, total_amt, received_amt, created_at = txn
            balance = float(total_amt) - float(received_amt)
            if balance <= 0:
                continue
            apply_amt = min(balance, remaining)
            success, new_status, new_received = self._apply_payment_to_bill(
                txn_id, txn_bill_no, received_amt, total_amt, apply_amt, payment_date, notes
            )
            if not success:
                return False, new_status, allocations
            allocations.append({
                'bill_number': txn_bill_no,
                'applied': apply_amt,
                'new_status': new_status,
                'new_balance': float(total_amt) - float(new_received)
            })
            remaining -= apply_amt
            if remaining <= 0:
                break

        if not allocations:
            return False, "No eligible bills to apply payment", []

        return True, allocations[-1]['new_status'], allocations

    def mark_credit_paid(self, bill_number, payment_date, notes="Settled"):
        """Mark credit bill fully paid (cascades if overpaid)"""
        bill = self.get_credit_bill(bill_number)
        if not bill:
            return False, "Bill not found"
        total_balance = 0
        queue = self._get_customer_credit_queue(bill['customer_name'])
        for txn in queue:
            _, _, total_amt, received_amt, _ = txn
            total_balance += float(total_amt) - float(received_amt)
        if total_balance <= 0:
            # already paid
            self.db.execute_query("UPDATE transactions SET credit_status='PAID' WHERE id=?", (bill['id'],))
            return True, 'PAID'

        success, _, allocations = self.add_credit_payment(bill_number, total_balance, payment_date, notes)
        return success, 'PAID' if success else 'UNPAID'

    def get_credit_summary(self):
        """Summary stats for credit bills"""
        summary = self.db.fetch_one(
            '''SELECT 
                   COUNT(*) FILTER (WHERE credit_status='UNPAID') as unpaid_count,
                   COUNT(*) FILTER (WHERE credit_status='PARTIAL') as partial_count,
                   COUNT(*) FILTER (WHERE credit_status='PAID') as paid_count,
                   SUM(total_amount - received_amount) as total_balance,
                   SUM(total_amount) as total_credit
               FROM transactions WHERE is_credit = 1'''
        )
        return summary
    def get_credit_transactions(self, limit=50):
        """Get credit transactions (Wholesale customers on credit)"""
        query = '''
            SELECT bill_number, customer_name, total_amount, payment_method, created_at
            FROM transactions
            WHERE is_credit = 1
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))
    
    def get_replacement_transactions(self, limit=50):
        """Get replacement transactions"""
        query = '''
            SELECT bill_number, customer_name, total_amount, created_at
            FROM transactions
            WHERE is_replacement = 1
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))

    def close(self):
        """Close database connection"""
        self.db.close()
