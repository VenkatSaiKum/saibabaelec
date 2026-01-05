import sqlite3

conn = sqlite3.connect('data/electrical_shop.db')
cursor = conn.cursor()

# Check the schema of the transactions table
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()

print("Transactions table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
