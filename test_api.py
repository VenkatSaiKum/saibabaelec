#!/usr/bin/env python
import sqlite3
from billing import BillingManager
from database import Database

# Test get_bill function
billing = BillingManager()

# Get a bill number
c = sqlite3.connect('data/electrical_shop.db')
cursor = c.cursor()
cursor.execute('SELECT bill_number FROM transactions LIMIT 1')
result = cursor.fetchone()

if result:
    bill_number = result[0]
    print(f"Testing bill: {bill_number}")
    bill = billing.get_bill(bill_number)
    print(f"Bill data: {bill}")
    print(f"Items count: {len(bill['items']) if bill and bill.get('items') else 0}")
    if bill and bill.get('items'):
        print("Items:")
        for item in bill['items']:
            print(f"  {item}")
else:
    print("No bills found")
