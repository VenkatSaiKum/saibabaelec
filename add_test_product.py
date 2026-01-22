import sqlite3

# Connect to database
conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Add a test product
cursor.execute('''
    INSERT INTO products (name, category, unit_price, quantity, minimum_stock)
    VALUES ('LED Bulb', 'Lighting', 50.00, 100, 5)
''')
conn.commit()

print('✓ Test product added')

# Verify it was added
cursor.execute('SELECT id, name, unit_price FROM products ORDER BY id DESC LIMIT 1')
product = cursor.fetchone()
if product:
    print(f'Product ID: {product[0]}, Name: {product[1]}, Price: ₹{product[2]}')

conn.close()
