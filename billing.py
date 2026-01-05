from database import Database, get_ist_datetime
from datetime import datetime
import os

class BillingManager:
    def __init__(self):
        self.db = Database()

    def create_bill(self, customer_name, items_list, payment_method="CASH", cash_amount=None, upi_amount=None):
        """
        Create a bill/transaction
        items_list: [(product_id, quantity, unit_price, product_name), ...]
        product_id can be 0 for manual items (no stock tracking)
        """
        if not items_list:
            print("✗ Bill must have at least one item")
            return None

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
        transaction_query = '''
            INSERT INTO transactions (customer_name, total_amount, payment_method, bill_number, cash_amount, upi_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        if not self.db.execute_query(transaction_query, (customer_name, total_amount, payment_method, bill_number, cash_amount, upi_amount, ist_time)):
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
        """Get sales for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        query = '''
            SELECT bill_number, customer_name, total_amount, created_at
            FROM transactions
            WHERE DATE(created_at) = ?
            ORDER BY created_at DESC
        '''
        return self.db.fetch_all(query, (date,))

    def get_sales_summary(self):
        """Get sales summary statistics"""
        query = '''
            SELECT 
                COUNT(*) as total_bills,
                SUM(total_amount) as total_sales,
                AVG(total_amount) as avg_bill_value,
                MAX(total_amount) as max_bill_value
            FROM transactions
        '''
        return self.db.fetch_one(query)

    def close(self):
        """Close database connection"""
        self.db.close()
