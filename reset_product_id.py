import sqlite3

# Connect to database
conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Reset the product ID sequence
cursor.execute('DELETE FROM sqlite_sequence WHERE name="products"')
conn.commit()

print('Product ID sequence has been reset. Next product will have ID 1.')

conn.close()
