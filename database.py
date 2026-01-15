import os
from datetime import datetime, timedelta
import sqlite3

# Check if running on Render with PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

# Lazy import psycopg2 only when needed
psycopg2 = None
sql = None

if not DATABASE_URL:
    # Use SQLite for local development
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'electrical_shop.db')

def get_ist_datetime():
    """Get current datetime in IST (GMT +5:30)"""
    utc_now = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = utc_now + ist_offset
    return ist_now.strftime("%Y-%m-%d %H:%M:%S")

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.is_postgres = bool(DATABASE_URL)
        self.init_database()

    def init_database(self):
        """Initialize database and create tables"""
        if self.is_postgres:
            # Lazy import psycopg2 only when needed
            global psycopg2, sql
            import psycopg2
            from psycopg2 import sql
            
            try:
                self.connection = psycopg2.connect(DATABASE_URL)
                self.cursor = self.connection.cursor()
            except Exception as e:
                print(f"PostgreSQL connection error: {e}")
                raise
        else:
            self.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.cursor = self.connection.cursor()
        
        try:
            # Products table
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        category TEXT NOT NULL,
                        unit_price REAL NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        minimum_stock INTEGER DEFAULT 5,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        category TEXT NOT NULL,
                        unit_price REAL NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        minimum_stock INTEGER DEFAULT 5,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            self.connection.commit()
            print("✓ Products table created")
        except Exception as e:
            print(f"Error creating products table: {e}")
            self.connection.rollback()

        # Stock movements table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stock_movements (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL,
                        movement_type TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        reference_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stock_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        movement_type TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        reference_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                ''')
            self.connection.commit()
            print("✓ Stock movements table created")
        except Exception as e:
            print(f"Stock movements table: {e}")

        # Transactions/Bills table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        customer_name TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        payment_method TEXT DEFAULT 'CASH',
                        cash_amount REAL,
                        upi_amount REAL,
                        bill_number TEXT UNIQUE NOT NULL,
                        bill_type TEXT DEFAULT 'REGULAR',
                        is_credit INTEGER DEFAULT 0,
                        is_replacement INTEGER DEFAULT 0,
                        received_amount REAL DEFAULT 0,
                        credit_status TEXT DEFAULT 'UNPAID',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        payment_method TEXT DEFAULT 'CASH',
                        cash_amount REAL,
                        upi_amount REAL,
                        bill_number TEXT UNIQUE NOT NULL,
                        bill_type TEXT DEFAULT 'REGULAR',
                        is_credit INTEGER DEFAULT 0,
                        is_replacement INTEGER DEFAULT 0,
                        received_amount REAL DEFAULT 0,
                        credit_status TEXT DEFAULT 'UNPAID',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            self.connection.commit()
            print("✓ Transactions table created")
        except Exception as e:
            print(f"Transactions table: {e}")

        # Transaction items table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_items (
                        id SERIAL PRIMARY KEY,
                        transaction_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        product_name TEXT,
                        quantity INTEGER NOT NULL,
                        unit_price REAL NOT NULL,
                        total_price REAL NOT NULL,
                        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        product_name TEXT,
                        quantity INTEGER NOT NULL,
                        unit_price REAL NOT NULL,
                        total_price REAL NOT NULL,
                        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                    )
                ''')
            self.connection.commit()
            print("✓ Transaction items table created")
        except Exception as e:
            print(f"Transaction items table: {e}")

        # Expenses table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL NOT NULL,
                        expense_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL NOT NULL,
                        expense_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            self.connection.commit()
            print("✓ Expenses table created")
        except Exception as e:
            print(f"Expenses table: {e}")

        # Supplier Bills table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supplier_bills (
                        id SERIAL PRIMARY KEY,
                        supplier_name TEXT NOT NULL,
                        bill_number TEXT NOT NULL,
                        bill_date TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        paid_amount REAL DEFAULT 0,
                        status TEXT DEFAULT 'UNPAID',
                        description TEXT,
                        due_date TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        paid_at TIMESTAMP
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supplier_bills (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_name TEXT NOT NULL,
                        bill_number TEXT NOT NULL,
                        bill_date TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        paid_amount REAL DEFAULT 0,
                        status TEXT DEFAULT 'UNPAID',
                        description TEXT,
                        due_date TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        paid_at DATETIME
                    )
                ''')
            self.connection.commit()
            print("✓ Supplier bills table created")
        except Exception as e:
            print(f"Supplier bills table: {e}")

        # Supplier Bill Payments table
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supplier_bill_payments (
                        id SERIAL PRIMARY KEY,
                        bill_id INTEGER NOT NULL,
                        payment_amount REAL NOT NULL,
                        payment_date TEXT NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (bill_id) REFERENCES supplier_bills(id)
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supplier_bill_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bill_id INTEGER NOT NULL,
                        payment_amount REAL NOT NULL,
                        payment_date TEXT NOT NULL,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (bill_id) REFERENCES supplier_bills(id)
                    )
                ''')
            self.connection.commit()
            print("✓ Supplier bill payments table created")
        except Exception as e:
            print(f"Supplier bill payments table: {e}")

        # Credit Bill Payments table (for wholesale credit customers)
        try:
            if self.is_postgres:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_bill_payments (
                        id SERIAL PRIMARY KEY,
                        transaction_id INTEGER NOT NULL,
                        payment_amount REAL NOT NULL,
                        payment_date TEXT NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
                    )
                ''')
            else:
                self.cursor.execute('''
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
            self.connection.commit()
            print("✓ Credit bill payments table created")
        except Exception as e:
            print(f"Credit bill payments table: {e}")

        # Add columns to existing transactions table if they don't exist
        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN bill_type TEXT DEFAULT 'REGULAR'")
        except:
            pass  # Column already exists
        
        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN is_credit INTEGER DEFAULT 0")
        except:
            pass  # Column already exists
        
        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN is_replacement INTEGER DEFAULT 0")
        except:
            pass  # Column already exists

        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN received_amount REAL DEFAULT 0")
        except:
            pass  # Column already exists

        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN credit_status TEXT DEFAULT 'UNPAID'")
        except:
            pass  # Column already exists

        self.connection.commit()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        """Execute a query"""
        try:
            # Convert SQLite placeholders to PostgreSQL placeholders if needed
            if self.is_postgres and params:
                query = query.replace('?', '%s')
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error executing query: {e}")
            return False

    def fetch_all(self, query, params=None):
        """Fetch all results"""
        try:
            # Convert SQLite placeholders to PostgreSQL placeholders if needed
            if self.is_postgres and params:
                query = query.replace('?', '%s')
                
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Fetch single result"""
        try:
            # Convert SQLite placeholders to PostgreSQL placeholders if needed
            if self.is_postgres and params:
                query = query.replace('?', '%s')
                
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
