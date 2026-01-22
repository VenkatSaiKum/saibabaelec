import sqlite3

conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Check if there are any bills
cursor.execute('SELECT COUNT(*) FROM transactions')
count = cursor.fetchone()[0]
print(f'Total bills in database: {count}')

if count > 0:
    # Show latest bills
    cursor.execute('''
        SELECT bill_number, customer_name, total_amount, payment_method, created_at
        FROM transactions
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    
    print('\nLatest bills:')
    for row in cursor.fetchall():
        print(f'  Bill: {row[0]}, Customer: {row[1]}, Amount: ₹{row[2]}, Method: {row[3]}, Date: {row[4]}')
else:
    print('No bills found in database')

conn.close()
