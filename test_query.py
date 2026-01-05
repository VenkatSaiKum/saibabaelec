import json
import sqlite3

conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Simulate what get_bill does
bill_number = 'BILL-20260105170215'
cursor.execute('SELECT * FROM transactions WHERE bill_number = ?', (bill_number,))
transaction = cursor.fetchone()

if transaction:
    print(f"Transaction: {transaction}")
    print(f"Transaction ID: {transaction[0]}")
    
    transaction_id = transaction[0]
    cursor.execute('''SELECT id, product_id, product_name, quantity, unit_price, total_price
                      FROM transaction_items
                      WHERE transaction_id = ?''', (transaction_id,))
    items = cursor.fetchall()
    print(f"\nItems found: {len(items)}")
    for item in items:
        print(f"  Full item: {item}")
        if len(item) >= 6:
            print(f"    [2]=product_name: {item[2]}, [3]=qty: {item[3]}, [4]=price: {item[4]}, [5]=total: {item[5]}")
