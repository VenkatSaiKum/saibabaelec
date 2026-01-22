from database import Database
from datetime import datetime

class ExpenseManager:
    def __init__(self):
        self.db = Database()

    def add_expense(self, category, description, amount, expense_date=None):
        """Add a new expense"""
        if expense_date is None:
            expense_date = datetime.now().strftime("%Y-%m-%d")
        
        query = '''
            INSERT INTO expenses (category, description, amount, expense_date)
            VALUES (?, ?, ?, ?)
        '''
        params = (category, description, amount, expense_date)
        
        if self.db.execute_query(query, params):
            print(f"✓ Expense added: {description} - ₹{amount}")
            return True
        else:
            print(f"✗ Failed to add expense")
            return False

    def get_all_expenses(self):
        """Get all expenses"""
        query = 'SELECT * FROM expenses ORDER BY expense_date DESC'
        return self.db.fetch_all(query)

    def get_expenses_by_date(self, date):
        """Get expenses for a specific date"""
        query = '''
            SELECT id, category, description, amount, expense_date
            FROM expenses
            WHERE DATE(expense_date) = ?
            ORDER BY expense_date DESC
        '''
        return self.db.fetch_all(query, (date,))

    def get_expenses_by_category(self, category):
        """Get expenses by category"""
        query = '''
            SELECT id, category, description, amount, expense_date
            FROM expenses
            WHERE category = ?
            ORDER BY expense_date DESC
        '''
        return self.db.fetch_all(query, (category,))

    def get_daily_expenses_summary(self, date=None):
        """Get daily expenses summary"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        query = '''
            SELECT 
                category,
                COUNT(*) as count,
                SUM(amount) as total
            FROM expenses
            WHERE DATE(expense_date) = ?
            GROUP BY category
            ORDER BY total DESC
        '''
        return self.db.fetch_all(query, (date,))

    def get_total_expenses_today(self, date=None):
        """Get total expenses for today"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        query = '''
            SELECT SUM(amount) FROM expenses
            WHERE DATE(expense_date) = ?
        '''
        result = self.db.fetch_one(query, (date,))
        return result[0] if result and result[0] else 0

    def delete_expense(self, expense_id):
        """Delete an expense"""
        query = 'DELETE FROM expenses WHERE id = ?'
        return self.db.execute_query(query, (expense_id,))

    def update_expense(self, expense_id, category=None, description=None, amount=None):
        """Update expense"""
        updates = []
        params = []

        if category:
            updates.append('category = ?')
            params.append(category)
        if description:
            updates.append('description = ?')
            params.append(description)
        if amount:
            updates.append('amount = ?')
            params.append(amount)

        if not updates:
            return False

        params.append(expense_id)
        query = f'UPDATE expenses SET {", ".join(updates)} WHERE id = ?'
        
        return self.db.execute_query(query, params)

    def display_daily_expenses(self, date=None):
        """Display expenses for a day"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        expenses = self.get_expenses_by_date(date)
        summary = self.get_daily_expenses_summary(date)
        total = self.get_total_expenses_today(date)

        print(f"\n{'='*80}")
        print(f"Expenses for {date}")
        print(f"{'='*80}")
        print(f"{'ID':<5} {'Category':<15} {'Description':<30} {'Amount':<12}")
        print(f"{'-'*80}")

        if expenses:
            for expense in expenses:
                expense_id, category, description, amount, _ = expense
                print(f"{expense_id:<5} {category:<15} {description:<30} ₹{amount:<11.2f}")
        else:
            print("No expenses for this date")

        print(f"{'-'*80}")
        print(f"\nExpense Summary by Category:")
        if summary:
            for cat_summary in summary:
                category, count, total_amount = cat_summary
                print(f"  {category:<20} x{count:<3} = ₹{total_amount:.2f}")
        
        print(f"\nTotal Expenses: ₹{total:.2f}")
        print(f"{'='*80}\n")

    def close(self):
        """Close database connection"""
        self.db.close()
