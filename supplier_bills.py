from database import Database
from datetime import datetime

class SupplierBillManager:
    def __init__(self):
        self.db = Database()
    
    def close(self):
        """Close database connection"""
        self.db.close()
    
    def add_bill(self, supplier_name, bill_number, bill_date, total_amount, description='', due_date=None):
        """Add a new supplier bill"""
        cursor = self.db.cursor
        cursor.execute('''
            INSERT INTO supplier_bills (supplier_name, bill_number, bill_date, total_amount, description, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'UNPAID')
        ''', (supplier_name, bill_number, bill_date, total_amount, description, due_date))
        self.db.connection.commit()
        return cursor.lastrowid
    
    def get_all_bills(self, status=None):
        """Get all supplier bills, optionally filtered by status"""
        cursor = self.db.cursor
        if status:
            cursor.execute('''
                SELECT id, supplier_name, bill_number, bill_date, total_amount, paid_amount, 
                       status, description, due_date, created_at, paid_at,
                       (SELECT MAX(payment_date) FROM supplier_bill_payments p WHERE p.bill_id = supplier_bills.id) as last_payment_date
                FROM supplier_bills
                WHERE status = ?
                ORDER BY bill_date DESC, created_at DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT id, supplier_name, bill_number, bill_date, total_amount, paid_amount, 
                       status, description, due_date, created_at, paid_at,
                       (SELECT MAX(payment_date) FROM supplier_bill_payments p WHERE p.bill_id = supplier_bills.id) as last_payment_date
                FROM supplier_bills
                ORDER BY bill_date DESC, created_at DESC
            ''')
        
        bills = []
        for row in cursor.fetchall():
            bills.append({
                'id': row[0],
                'supplier_name': row[1],
                'bill_number': row[2],
                'bill_date': row[3],
                'total_amount': row[4],
                'paid_amount': row[5],
                'status': row[6],
                'description': row[7],
                'due_date': row[8],
                'created_at': row[9],
                'paid_at': row[10],
                'last_payment_date': row[11]
            })
        return bills
    
    def get_bill(self, bill_id):
        """Get a single supplier bill by ID"""
        cursor = self.db.cursor
        cursor.execute('''
            SELECT id, supplier_name, bill_number, bill_date, total_amount, paid_amount, 
                   status, description, due_date, created_at, paid_at
            FROM supplier_bills
            WHERE id = ?
        ''', (bill_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'supplier_name': row[1],
                'bill_number': row[2],
                'bill_date': row[3],
                'total_amount': row[4],
                'paid_amount': row[5],
                'status': row[6],
                'description': row[7],
                'due_date': row[8],
                'created_at': row[9],
                'paid_at': row[10]
            }
        return None

    def get_supplier_groups(self, status=None):
        """Return aggregated rows per supplier with totals and last payment date"""
        cursor = self.db.cursor
        
        if status:
            query = '''
                SELECT 
                    supplier_name,
                    COUNT(*) as bill_count,
                    SUM(total_amount) as total_amount,
                    SUM(paid_amount) as paid_amount,
                    SUM(total_amount - paid_amount) as balance,
                    MIN(bill_date) as first_bill_date,
                    MAX(bill_date) as last_bill_date,
                    SUM(CASE WHEN status != 'PAID' THEN 1 ELSE 0 END) as open_bills,
                    MAX((SELECT MAX(p.payment_date) FROM supplier_bill_payments p WHERE p.bill_id IN (
                        SELECT id FROM supplier_bills sb2 WHERE sb2.supplier_name = supplier_bills.supplier_name
                    ))) as last_payment_date
                FROM supplier_bills
                WHERE status = ?
                GROUP BY supplier_name
                ORDER BY last_bill_date DESC, supplier_name ASC
            '''
            cursor.execute(query, (status,))
        else:
            query = '''
                SELECT 
                    supplier_name,
                    COUNT(*) as bill_count,
                    SUM(total_amount) as total_amount,
                    SUM(paid_amount) as paid_amount,
                    SUM(total_amount - paid_amount) as balance,
                    MIN(bill_date) as first_bill_date,
                    MAX(bill_date) as last_bill_date,
                    SUM(CASE WHEN status != 'PAID' THEN 1 ELSE 0 END) as open_bills,
                    MAX((SELECT MAX(p.payment_date) FROM supplier_bill_payments p WHERE p.bill_id IN (
                        SELECT id FROM supplier_bills sb2 WHERE sb2.supplier_name = supplier_bills.supplier_name
                    ))) as last_payment_date
                FROM supplier_bills
                GROUP BY supplier_name
                ORDER BY last_bill_date DESC, supplier_name ASC
            '''
            cursor.execute(query)

        groups = []
        for row in cursor.fetchall():
            supplier, bill_count, total_amount, paid_amount, balance, first_bill_date, last_bill_date, open_bills, last_payment_date = row
            groups.append({
                'supplier_name': supplier,
                'bill_count': bill_count,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'balance': balance,
                'first_bill_date': first_bill_date,
                'last_bill_date': last_bill_date,
                'open_bills': open_bills,
                'last_payment_date': last_payment_date
            })
        return groups

    def get_bills_by_supplier(self, supplier_name):
        """Get all bills for a supplier with last payment date and history"""
        cursor = self.db.cursor
        cursor.execute('''
            SELECT 
                id, bill_number, bill_date, due_date, total_amount, paid_amount,
                status, description, created_at, paid_at,
                (SELECT MAX(payment_date) FROM supplier_bill_payments p WHERE p.bill_id = sb.id) as last_payment_date
            FROM supplier_bills sb
            WHERE supplier_name = ?
            ORDER BY bill_date DESC, created_at DESC
        ''', (supplier_name,))

        bills = []
        for row in cursor.fetchall():
            bill_info = {
                'id': row[0],
                'bill_number': row[1],
                'bill_date': row[2],
                'due_date': row[3],
                'total_amount': row[4],
                'paid_amount': row[5],
                'status': row[6],
                'description': row[7],
                'created_at': row[8],
                'paid_at': row[9],
                'last_payment_date': row[10]
            }
            bill_info['payment_history'] = self.get_payment_history(row[0])
            bills.append(bill_info)
        return bills
    
    def make_payment(self, bill_id, payment_amount, payment_date=None, notes=''):
        """Make a payment towards a bill"""
        cursor = self.db.cursor
        
        # Get current bill details
        bill = self.get_bill(bill_id)
        if not bill:
            return False
        
        new_paid_amount = bill['paid_amount'] + payment_amount
        
        # Use provided payment date or current date
        if payment_date:
            paid_at = payment_date + ' 00:00:00'
        else:
            paid_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine new status
        if new_paid_amount >= bill['total_amount']:
            new_status = 'PAID'
            new_paid_amount = bill['total_amount']  # Cap at total amount
        else:
            new_status = 'PARTIAL'
        
        # Record the payment transaction
        cursor.execute('''
            INSERT INTO supplier_bill_payments (bill_id, payment_amount, payment_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (bill_id, payment_amount, payment_date or datetime.now().strftime('%Y-%m-%d'), notes))
        
        # Update the bill
        cursor.execute('''
            UPDATE supplier_bills
            SET paid_amount = ?, status = ?, paid_at = ?
            WHERE id = ?
        ''', (new_paid_amount, new_status, paid_at, bill_id))
        
        self.db.connection.commit()
        return True
    
    def _get_supplier_bill_queue(self, supplier_name):
        """Get unpaid/partial bills for a supplier in FIFO order"""
        cursor = self.db.cursor
        cursor.execute('''
            SELECT id, bill_number, total_amount, paid_amount, bill_date
            FROM supplier_bills
            WHERE status != 'PAID' AND supplier_name = ?
            ORDER BY bill_date ASC, id ASC
        ''', (supplier_name,))
        return cursor.fetchall() or []

    def _apply_payment_to_supplier_bill(self, bill_id, total_amount, current_paid, apply_amount, payment_date, notes):
        """Apply payment to a single supplier bill"""
        cursor = self.db.cursor
        new_paid_amount = float(current_paid) + apply_amount
        new_status = 'PAID' if new_paid_amount + 0.01 >= float(total_amount) else 'PARTIAL'
        
        # Record payment
        cursor.execute('''
            INSERT INTO supplier_bill_payments (bill_id, payment_amount, payment_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (bill_id, apply_amount, payment_date, notes))
        
        # Update bill
        cursor.execute('''
            UPDATE supplier_bills
            SET paid_amount = ?, status = ?
            WHERE id = ?
        ''', (new_paid_amount, new_status, bill_id))
        
        self.db.connection.commit()
        return True, new_status, new_paid_amount

    def add_supplier_payment(self, supplier_name, payment_amount, payment_date, notes=""):
        """Record payment towards supplier; cascades to unpaid bills FIFO"""
        try:
            payment_amount = float(payment_amount)
        except:
            return False, "Invalid amount", []
        if payment_amount <= 0:
            return False, "Payment amount must be positive", []
        
        queue = self._get_supplier_bill_queue(supplier_name)
        remaining = payment_amount
        allocations = []
        
        for bill in queue:
            bill_id, bill_no, total_amt, paid_amt, bill_date = bill
            balance = float(total_amt) - float(paid_amt)
            if balance <= 0:
                continue
            apply_amt = min(balance, remaining)
            success, new_status, new_paid = self._apply_payment_to_supplier_bill(
                bill_id, total_amt, paid_amt, apply_amt, payment_date, notes
            )
            if not success:
                return False, "Payment failed", allocations
            allocations.append({
                'bill_number': bill_no,
                'applied': apply_amt,
                'new_status': new_status,
                'new_balance': float(total_amt) - float(new_paid)
            })
            remaining -= apply_amt
            if remaining <= 0:
                break
        
        if not allocations:
            return False, "No eligible bills to apply payment", []
        
        return True, allocations[-1]['new_status'], allocations

    def mark_as_paid(self, bill_id, payment_date=None, notes=''):
        """Mark a bill as fully paid"""
        cursor = self.db.cursor
        bill = self.get_bill(bill_id)
        if not bill:
            return False
        
        # Calculate remaining amount to pay
        remaining_amount = bill['total_amount'] - bill['paid_amount']
        
        # Use provided payment date or current date
        if payment_date:
            paid_at = payment_date + ' 00:00:00'
        else:
            paid_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Record the payment transaction for the remaining amount
        if remaining_amount > 0:
            cursor.execute('''
                INSERT INTO supplier_bill_payments (bill_id, payment_amount, payment_date, notes)
                VALUES (?, ?, ?, ?)
            ''', (bill_id, remaining_amount, payment_date or datetime.now().strftime('%Y-%m-%d'), notes))
        
        # Update the bill
        cursor.execute('''
            UPDATE supplier_bills
            SET paid_amount = total_amount, status = 'PAID', paid_at = ?
            WHERE id = ?
        ''', (paid_at, bill_id))
        
        self.db.connection.commit()
        return True
    
    def delete_bill(self, bill_id):
        """Delete a supplier bill"""
        cursor = self.db.cursor
        cursor.execute('DELETE FROM supplier_bills WHERE id = ?', (bill_id,))
        self.db.connection.commit()
        return cursor.rowcount > 0
    
    def get_payment_history(self, bill_id):
        """Get payment history for a specific bill"""
        cursor = self.db.cursor
        cursor.execute('''
            SELECT id, payment_amount, payment_date, notes, created_at
            FROM supplier_bill_payments
            WHERE bill_id = ?
            ORDER BY payment_date DESC, created_at DESC
        ''', (bill_id,))
        
        payments = []
        for row in cursor.fetchall():
            payments.append({
                'id': row[0],
                'payment_amount': row[1],
                'payment_date': row[2],
                'notes': row[3],
                'created_at': row[4]
            })
        return payments
    
    def get_summary(self):
        """Get summary statistics for supplier bills"""
        cursor = self.db.cursor
        
        # Total unpaid amount
        cursor.execute('SELECT SUM(total_amount - paid_amount) FROM supplier_bills WHERE status != "PAID"')
        total_unpaid = cursor.fetchone()[0] or 0
        
        # Count of unpaid bills
        cursor.execute('SELECT COUNT(*) FROM supplier_bills WHERE status = "UNPAID"')
        unpaid_count = cursor.fetchone()[0]
        
        # Count of partial paid bills
        cursor.execute('SELECT COUNT(*) FROM supplier_bills WHERE status = "PARTIAL"')
        partial_count = cursor.fetchone()[0]
        
        # Total paid this month
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT SUM(paid_amount) FROM supplier_bills 
            WHERE paid_at LIKE ? || '%'
        ''', (current_month,))
        paid_this_month = cursor.fetchone()[0] or 0
        
        return {
            'total_unpaid': total_unpaid,
            'unpaid_count': unpaid_count,
            'partial_count': partial_count,
            'paid_this_month': paid_this_month
        }
