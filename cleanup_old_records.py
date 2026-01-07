"""
Database Cleanup Script
Deletes old records to free up storage space on Render
- Billing records older than 45 days
- Supplier bills older than 60 days
- Expense records older than 7 days
- Keeps only active products
"""

import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'electrical_shop.db')

class DatabaseCleaner:
    def __init__(self):
        self.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.deleted_records = {
            'billing': 0,
            'supplier_bills': 0,
            'expenses': 0,
            'inactive_products': 0,
            'orphaned_transaction_items': 0,
            'orphaned_stock_movements': 0
        }

    def delete_old_billing_records(self, days=45):
        """Delete billing records (transactions) older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # First, get the transaction IDs to delete
            self.cursor.execute('''
                SELECT id FROM transactions 
                WHERE created_at < ?
            ''', (cutoff_str,))
            
            transaction_ids = [row[0] for row in self.cursor.fetchall()]
            
            if transaction_ids:
                # Delete transaction items first (foreign key constraint)
                placeholders = ','.join('?' * len(transaction_ids))
                self.cursor.execute(f'''
                    DELETE FROM transaction_items 
                    WHERE transaction_id IN ({placeholders})
                ''', transaction_ids)
                
                self.deleted_records['orphaned_transaction_items'] += self.cursor.rowcount
                
                # Delete transactions
                self.cursor.execute(f'''
                    DELETE FROM transactions 
                    WHERE id IN ({placeholders})
                ''', transaction_ids)
                
                self.deleted_records['billing'] = self.cursor.rowcount
                self.connection.commit()
                
                print(f"✓ Deleted {self.deleted_records['billing']} billing records older than {days} days")
                print(f"  (Also deleted {self.deleted_records['orphaned_transaction_items']} related transaction items)")
                return True
            else:
                print(f"✓ No billing records older than {days} days found")
                return True
                
        except Exception as e:
            print(f"✗ Error deleting billing records: {e}")
            self.connection.rollback()
            return False

    def delete_old_supplier_bills(self, days=60):
        """Delete supplier bill records older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        try:
            self.cursor.execute('''
                DELETE FROM supplier_bills 
                WHERE bill_date < ?
            ''', (cutoff_str,))
            
            self.deleted_records['supplier_bills'] = self.cursor.rowcount
            self.connection.commit()
            
            print(f"✓ Deleted {self.deleted_records['supplier_bills']} supplier bills older than {days} days")
            return True
            
        except Exception as e:
            print(f"✗ Error deleting supplier bills: {e}")
            self.connection.rollback()
            return False

    def delete_old_expenses(self, days=7):
        """Delete expense records older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        try:
            self.cursor.execute('''
                DELETE FROM expenses 
                WHERE expense_date < ?
            ''', (cutoff_str,))
            
            self.deleted_records['expenses'] = self.cursor.rowcount
            self.connection.commit()
            
            print(f"✓ Deleted {self.deleted_records['expenses']} expense records older than {days} days")
            return True
            
        except Exception as e:
            print(f"✗ Error deleting expenses: {e}")
            self.connection.rollback()
            return False

    def keep_only_active_products(self):
        """Delete products with zero quantity (inactive products)"""
        try:
            # Get inactive product IDs
            self.cursor.execute('''
                SELECT id FROM products 
                WHERE quantity = 0
            ''')
            
            product_ids = [row[0] for row in self.cursor.fetchall()]
            
            if product_ids:
                # Delete related stock movements first
                placeholders = ','.join('?' * len(product_ids))
                self.cursor.execute(f'''
                    DELETE FROM stock_movements 
                    WHERE product_id IN ({placeholders})
                ''', product_ids)
                
                self.deleted_records['orphaned_stock_movements'] = self.cursor.rowcount
                
                # Delete inactive products
                self.cursor.execute(f'''
                    DELETE FROM products 
                    WHERE id IN ({placeholders})
                ''', product_ids)
                
                self.deleted_records['inactive_products'] = self.cursor.rowcount
                self.connection.commit()
                
                print(f"✓ Deleted {self.deleted_records['inactive_products']} inactive products (zero quantity)")
                print(f"  (Also deleted {self.deleted_records['orphaned_stock_movements']} related stock movements)")
                return True
            else:
                print(f"✓ No inactive products found")
                return True
                
        except Exception as e:
            print(f"✗ Error deleting inactive products: {e}")
            self.connection.rollback()
            return False

    def get_storage_summary(self):
        """Get summary of records in database"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM transactions')
            billing_count = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM supplier_bills')
            supplier_count = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM expenses')
            expense_count = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM products')
            product_count = self.cursor.fetchone()[0]
            
            print("\n" + "="*50)
            print("DATABASE SUMMARY BEFORE CLEANUP:")
            print("="*50)
            print(f"Billing Records: {billing_count}")
            print(f"Supplier Bills: {supplier_count}")
            print(f"Expenses: {expense_count}")
            print(f"Products: {product_count}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"✗ Error getting storage summary: {e}")

    def cleanup(self):
        """Run all cleanup operations"""
        print("\n" + "="*50)
        print("STARTING DATABASE CLEANUP")
        print("="*50 + "\n")
        
        self.get_storage_summary()
        
        # Run cleanup operations
        self.delete_old_billing_records(days=45)
        self.delete_old_supplier_bills(days=60)
        self.delete_old_expenses(days=7)
        self.keep_only_active_products()
        
        self.get_storage_summary()
        
        # Print summary
        print("="*50)
        print("CLEANUP SUMMARY:")
        print("="*50)
        print(f"Billing Records Deleted: {self.deleted_records['billing']}")
        print(f"Supplier Bills Deleted: {self.deleted_records['supplier_bills']}")
        print(f"Expense Records Deleted: {self.deleted_records['expenses']}")
        print(f"Inactive Products Deleted: {self.deleted_records['inactive_products']}")
        print(f"Total Records Deleted: {sum(self.deleted_records.values())}")
        print("="*50)
        print("\n✓ Cleanup completed successfully!")
        print("✓ Storage space has been freed up\n")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


def main():
    """Run the cleanup script"""
    cleaner = DatabaseCleaner()
    try:
        cleaner.cleanup()
    except Exception as e:
        print(f"✗ Fatal error during cleanup: {e}")
    finally:
        cleaner.close()


if __name__ == "__main__":
    main()
