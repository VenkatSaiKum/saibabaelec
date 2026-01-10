#!/usr/bin/env python3
"""
Database Migration Script
Adds new columns for bill_type, is_credit, and is_replacement to existing database
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'electrical_shop.db')

def migrate_database():
    """Add new columns to transactions table"""
    print("Starting database migration...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
        if not cursor.fetchone():
            print("✗ Transactions table not found. Please run the application first to create tables.")
            conn.close()
            return False
        
        # Add bill_type column
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN bill_type TEXT DEFAULT 'REGULAR'")
            print("✓ Added bill_type column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - bill_type column already exists")
            else:
                raise
        
        # Add is_credit column
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_credit INTEGER DEFAULT 0")
            print("✓ Added is_credit column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - is_credit column already exists")
            else:
                raise
        
        # Add is_replacement column
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_replacement INTEGER DEFAULT 0")
            print("✓ Added is_replacement column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - is_replacement column already exists")
            else:
                raise

        # Add received_amount column
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN received_amount REAL DEFAULT 0")
            print("✓ Added received_amount column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - received_amount column already exists")
            else:
                raise

        # Add credit_status column
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN credit_status TEXT DEFAULT 'UNPAID'")
            print("✓ Added credit_status column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  - credit_status column already exists")
            else:
                raise
        
        # Update existing records to have default values
        cursor.execute("""
            UPDATE transactions 
            SET bill_type = 'REGULAR', 
                is_credit = 0, 
                is_replacement = 0 
            WHERE bill_type IS NULL OR is_credit IS NULL OR is_replacement IS NULL OR received_amount IS NULL OR credit_status IS NULL
        """)
        updated_rows = cursor.rowcount
        
        conn.commit()
        print(f"✓ Updated {updated_rows} existing transaction(s) with default values")
        
        # Create credit_bill_payments table if missing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_bill_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                payment_amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        ''')

        # Verify the changes
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = ['bill_type', 'is_credit', 'is_replacement', 'received_amount', 'credit_status']
        all_present = all(col in column_names for col in required_columns)

        if all_present:
            print("\n✓ Migration completed successfully!")
            print(f"  - bill_type column: Present")
            print(f"  - is_credit column: Present")
            print(f"  - is_replacement column: Present")
            print(f"  - received_amount column: Present")
            print(f"  - credit_status column: Present")
            
            # Show column structure
            print("\nTransactions table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            conn.close()
            return True
        else:
            print("\n✗ Migration incomplete. Some columns are missing.")
            conn.close()
            return False
            
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Database Migration for New Features")
    print("="*60)
    print("\nThis script will add the following columns to transactions table:")
    print("  1. bill_type (TEXT) - REGULAR, CREDIT, or REPLACEMENT")
    print("  2. is_credit (INTEGER) - 1 for credit bills, 0 otherwise")
    print("  3. is_replacement (INTEGER) - 1 for replacement bills, 0 otherwise")
    print("\nExisting data will NOT be deleted or modified (except defaults added)")
    print("="*60)
    
    response = input("\nDo you want to proceed? (yes/no): ").lower()
    
    if response == 'yes':
        if migrate_database():
            print("\n" + "="*60)
            print("Migration successful! You can now use the new features.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("Migration failed. Please check the errors above.")
            print("="*60)
    else:
        print("\nMigration cancelled.")
