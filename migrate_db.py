import sqlite3

conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

try:
    # Add cash_amount column
    cursor.execute('ALTER TABLE transactions ADD COLUMN cash_amount REAL')
    print('✓ Added cash_amount column')
except sqlite3.OperationalError as e:
    print(f'cash_amount: {e}')

try:
    # Add upi_amount column
    cursor.execute('ALTER TABLE transactions ADD COLUMN upi_amount REAL')
    print('✓ Added upi_amount column')
except sqlite3.OperationalError as e:
    print(f'upi_amount: {e}')

conn.commit()
conn.close()

print('✓ Database schema updated')
