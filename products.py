from database import Database

class ProductManager:
    def __init__(self):
        self.db = Database()

    def add_product(self, name, category, unit_price, quantity=0, minimum_stock=5):
        """Add a new product"""
        query = '''
            INSERT INTO products (name, category, unit_price, quantity, minimum_stock)
            VALUES (?, ?, ?, ?, ?)
        '''
        params = (name, category, unit_price, quantity, minimum_stock)
        
        if self.db.execute_query(query, params):
            print(f"✓ Product '{name}' added successfully")
            return True
        else:
            print(f"✗ Failed to add product '{name}'")
            return False

    def get_all_products(self):
        """Get all products"""
        query = 'SELECT * FROM products ORDER BY name'
        return self.db.fetch_all(query)

    def get_product_by_id(self, product_id):
        """Get product by ID"""
        query = 'SELECT * FROM products WHERE id = ?'
        return self.db.fetch_one(query, (product_id,))

    def get_product_by_name(self, name):
        """Get product by name"""
        query = 'SELECT * FROM products WHERE name = ?'
        return self.db.fetch_one(query, (name,))

    def update_product(self, product_id, name=None, category=None, unit_price=None, minimum_stock=None):
        """Update product details"""
        updates = []
        params = []

        if name:
            updates.append('name = ?')
            params.append(name)
        if category:
            updates.append('category = ?')
            params.append(category)
        if unit_price:
            updates.append('unit_price = ?')
            params.append(unit_price)
        if minimum_stock:
            updates.append('minimum_stock = ?')
            params.append(minimum_stock)

        if not updates:
            return False

        params.append(product_id)
        query = f'UPDATE products SET {", ".join(updates)} WHERE id = ?'
        
        return self.db.execute_query(query, params)

    def delete_product(self, product_id):
        """Delete a product"""
        query = 'DELETE FROM products WHERE id = ?'
        return self.db.execute_query(query, (product_id,))

    def get_low_stock_products(self):
        """Get products with stock below minimum"""
        query = '''
            SELECT * FROM products 
            WHERE quantity <= minimum_stock 
            ORDER BY quantity ASC
        '''
        return self.db.fetch_all(query)

    def display_all_products(self):
        """Display all products in formatted table"""
        products = self.get_all_products()
        if not products:
            print("No products in inventory")
            return

        print("\n" + "="*100)
        print(f"{'ID':<5} {'Name':<25} {'Category':<15} {'Unit Price':<12} {'Quantity':<10} {'Min Stock':<10}")
        print("="*100)
        
        for product in products:
            product_id, name, category, unit_price, quantity, minimum_stock, _ = product
            status = "⚠️ LOW" if quantity <= minimum_stock else "✓"
            print(f"{product_id:<5} {name:<25} {category:<15} ₹{unit_price:<11.2f} {quantity:<10} {minimum_stock:<10} {status}")
        
        print("="*100 + "\n")

    def close(self):
        """Close database connection"""
        self.db.close()
