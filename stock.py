from database import Database
from datetime import datetime

class StockManager:
    def __init__(self):
        self.db = Database()

    def add_stock(self, product_id, quantity, notes=""):
        """Add stock for a product"""
        # Update product quantity
        product = self.db.fetch_one('SELECT quantity FROM products WHERE id = ?', (product_id,))
        
        if not product:
            print("Product not found")
            return False

        new_quantity = product[0] + quantity
        
        # Update product
        update_query = 'UPDATE products SET quantity = ? WHERE id = ?'
        self.db.execute_query(update_query, (new_quantity, product_id))

        # Record movement
        movement_query = '''
            INSERT INTO stock_movements (product_id, movement_type, quantity, notes)
            VALUES (?, ?, ?, ?)
        '''
        self.db.execute_query(movement_query, (product_id, 'ADD', quantity, notes))
        
        print(f"✓ Added {quantity} units. New stock: {new_quantity}")
        return True

    def remove_stock(self, product_id, quantity, notes=""):
        """Remove stock for a product"""
        product = self.db.fetch_one('SELECT quantity, name FROM products WHERE id = ?', (product_id,))
        
        if not product:
            print("Product not found")
            return False

        current_qty, product_name = product[0], product[1]

        if current_qty < quantity:
            print(f"✗ Insufficient stock. Available: {current_qty}, Requested: {quantity}")
            return False

        new_quantity = current_qty - quantity
        
        # Update product
        update_query = 'UPDATE products SET quantity = ? WHERE id = ?'
        self.db.execute_query(update_query, (new_quantity, product_id))

        # Record movement
        movement_query = '''
            INSERT INTO stock_movements (product_id, movement_type, quantity, notes)
            VALUES (?, ?, ?, ?)
        '''
        self.db.execute_query(movement_query, (product_id, 'REMOVE', quantity, notes))
        
        print(f"✓ Removed {quantity} units from '{product_name}'. New stock: {new_quantity}")
        return True

    def get_stock_history(self, product_id, limit=10):
        """Get stock movement history"""
        query = '''
            SELECT id, product_id, movement_type, quantity, notes, created_at
            FROM stock_movements
            WHERE product_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (product_id, limit))

    def get_stock_report(self):
        """Generate stock report"""
        query = '''
            SELECT id, name, category, quantity, unit_price, minimum_stock,
                   (quantity * unit_price) as total_value
            FROM products
            ORDER BY category
        '''
        return self.db.fetch_all(query)

    def display_stock_report(self):
        """Display stock report in formatted table"""
        report = self.get_stock_report()
        if not report:
            print("No products in inventory")
            return

        total_inventory_value = 0
        print("\n" + "="*120)
        print(f"{'ID':<5} {'Name':<20} {'Category':<15} {'Qty':<8} {'Unit Price':<12} {'Stock Value':<15} {'Min Stock':<10}")
        print("="*120)
        
        for item in report:
            product_id, name, category, qty, unit_price, min_stock, total_value = item
            total_inventory_value += total_value
            status = "⚠️" if qty <= min_stock else "✓"
            print(f"{product_id:<5} {name:<20} {category:<15} {qty:<8} ₹{unit_price:<11.2f} ₹{total_value:<14.2f} {min_stock:<10} {status}")
        
        print("="*120)
        print(f"Total Inventory Value: ₹{total_inventory_value:.2f}\n")

    def display_stock_history(self, product_id):
        """Display stock movement history"""
        product = self.db.fetch_one('SELECT name FROM products WHERE id = ?', (product_id,))
        if not product:
            print("Product not found")
            return

        history = self.get_stock_history(product_id, limit=20)
        if not history:
            print(f"No stock history for product ID {product_id}")
            return

        print(f"\n{'='*100}")
        print(f"Stock History for: {product[0]}")
        print(f"{'='*100}")
        print(f"{'ID':<5} {'Type':<10} {'Quantity':<10} {'Notes':<30} {'Date':<20}")
        print(f"{'-'*100}")

        for record in history:
            record_id, _, movement_type, qty, notes, created_at = record
            notes = notes if notes else "N/A"
            print(f"{record_id:<5} {movement_type:<10} {qty:<10} {notes:<30} {created_at:<20}")

        print(f"{'='*100}\n")

    def close(self):
        """Close database connection"""
        self.db.close()
