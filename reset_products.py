import sqlite3

# Connect to database
conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Delete all products
cursor.execute('DELETE FROM products')
# Reset the product ID sequence
cursor.execute('DELETE FROM sqlite_sequence WHERE name="products"')
conn.commit()

print('✓ All products deleted')
print('✓ Product ID sequence reset to 1')
print('✓ Next product will start with ID 1')

conn.close()
