#!/usr/bin/env python3
"""
Electrical Shop Stock Management System
"""

from products import ProductManager
from stock import StockManager
from billing import BillingManager
import sys

class ElectricalShopSystem:
    def __init__(self):
        self.products = ProductManager()
        self.stock = StockManager()
        self.billing = BillingManager()

    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print(" "*15 + "ELECTRICAL SHOP MANAGEMENT SYSTEM")
        print("="*60)
        print("\n1. PRODUCT MANAGEMENT")
        print("   1.1 - Add Product")
        print("   1.2 - View All Products")
        print("   1.3 - Update Product")
        print("   1.4 - Delete Product")
        print("   1.5 - View Low Stock Products")
        
        print("\n2. STOCK MANAGEMENT")
        print("   2.1 - Add Stock")
        print("   2.2 - Remove Stock")
        print("   2.3 - View Stock Report")
        print("   2.4 - View Stock History")
        
        print("\n3. BILLING & SALES")
        print("   3.1 - Create Bill")
        print("   3.2 - View Bill")
        print("   3.3 - View Recent Bills")
        print("   3.4 - View Daily Sales")
        print("   3.5 - Sales Summary")
        
        print("\n0. Exit")
        print("="*60)

    def handle_products(self, option):
        """Handle product management options"""
        if option == "1.1":
            name = input("Product Name: ").strip()
            category = input("Category (e.g., Wiring, Switches, Bulbs): ").strip()
            try:
                unit_price = float(input("Unit Price (₹): "))
                quantity = int(input("Initial Quantity: "))
                min_stock = int(input("Minimum Stock Level (default 5): ") or "5")
                self.products.add_product(name, category, unit_price, quantity, min_stock)
            except ValueError:
                print("✗ Invalid input. Please enter valid numbers.")

        elif option == "1.2":
            self.products.display_all_products()

        elif option == "1.3":
            self.products.display_all_products()
            try:
                product_id = int(input("Enter Product ID to update: "))
                print("\nLeave blank to skip a field:")
                name = input("New Name: ").strip() or None
                category = input("New Category: ").strip() or None
                unit_price = input("New Unit Price: ").strip()
                unit_price = float(unit_price) if unit_price else None
                min_stock = input("New Minimum Stock: ").strip()
                min_stock = int(min_stock) if min_stock else None

                if self.products.update_product(product_id, name, category, unit_price, min_stock):
                    print("✓ Product updated successfully")
                else:
                    print("✗ Failed to update product")
            except ValueError:
                print("✗ Invalid input")

        elif option == "1.4":
            self.products.display_all_products()
            try:
                product_id = int(input("Enter Product ID to delete: "))
                confirm = input("Are you sure? (yes/no): ").lower()
                if confirm == "yes":
                    if self.products.delete_product(product_id):
                        print("✓ Product deleted successfully")
                    else:
                        print("✗ Failed to delete product")
            except ValueError:
                print("✗ Invalid input")

        elif option == "1.5":
            low_stock = self.products.get_low_stock_products()
            if low_stock:
                print("\n" + "="*100)
                print("LOW STOCK PRODUCTS - REQUIRE REORDERING")
                print("="*100)
                print(f"{'ID':<5} {'Name':<25} {'Category':<15} {'Current':<10} {'Min Stock':<10}")
                print("-"*100)
                for product in low_stock:
                    product_id, name, category, _, qty, min_stock, _ = product
                    print(f"{product_id:<5} {name:<25} {category:<15} {qty:<10} {min_stock:<10}")
                print("="*100 + "\n")
            else:
                print("✓ No low stock products")

    def handle_stock(self, option):
        """Handle stock management options"""
        if option == "2.1":
            self.products.display_all_products()
            try:
                product_id = int(input("Enter Product ID: "))
                quantity = int(input("Quantity to Add: "))
                notes = input("Notes (optional): ").strip() or ""
                self.stock.add_stock(product_id, quantity, notes)
            except ValueError:
                print("✗ Invalid input")

        elif option == "2.2":
            self.products.display_all_products()
            try:
                product_id = int(input("Enter Product ID: "))
                quantity = int(input("Quantity to Remove: "))
                notes = input("Notes (optional): ").strip() or ""
                self.stock.remove_stock(product_id, quantity, notes)
            except ValueError:
                print("✗ Invalid input")

        elif option == "2.3":
            self.stock.display_stock_report()

        elif option == "2.4":
            self.products.display_all_products()
            try:
                product_id = int(input("Enter Product ID: "))
                self.stock.display_stock_history(product_id)
            except ValueError:
                print("✗ Invalid input")

    def handle_billing(self, option):
        """Handle billing options"""
        if option == "3.1":
            customer_name = input("Customer Name: ").strip()
            if not customer_name:
                print("✗ Customer name cannot be empty")
                return

            items_list = []
            self.products.display_all_products()

            while True:
                try:
                    product_id = input("\nEnter Product ID (or 'done' to finish): ").strip()
                    if product_id.lower() == 'done':
                        break

                    product_id = int(product_id)
                    quantity = int(input("Quantity: "))

                    if quantity <= 0:
                        print("✗ Quantity must be positive")
                        continue

                    items_list.append((product_id, quantity))
                    print(f"✓ Added to bill")

                except ValueError:
                    print("✗ Invalid input")

            if items_list:
                payment = input("Payment Method (CASH/CARD/CHEQUE) [default: CASH]: ").strip().upper() or "CASH"
                bill_number = self.billing.create_bill(customer_name, items_list, payment)
                
                if bill_number:
                    self.billing.display_bill(bill_number)
                    filename = f"data/bill_{bill_number}.txt"
                    self._save_bill_to_file(bill_number, filename)

        elif option == "3.2":
            bill_number = input("Enter Bill Number: ").strip()
            self.billing.display_bill(bill_number)

        elif option == "3.3":
            try:
                limit = int(input("Number of recent bills to display (default 10): ") or "10")
                self.billing.display_bill_history(limit)
            except ValueError:
                self.billing.display_bill_history()

        elif option == "3.4":
            date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip() or None
            bills = self.billing.get_daily_sales(date)
            
            if bills:
                print("\n" + "="*80)
                if date:
                    print(f"Daily Sales for {date}")
                else:
                    from datetime import datetime
                    print(f"Daily Sales for {datetime.now().strftime('%Y-%m-%d')}")
                print("="*80)
                print(f"{'Bill #':<20} {'Customer':<25} {'Amount':<15} {'Time':<20}")
                print("-"*80)
                
                total = 0
                for bill in bills:
                    bill_num, customer, amount, created_at = bill
                    total += amount
                    print(f"{bill_num:<20} {customer:<25} ₹{amount:<14.2f} {created_at:<20}")
                
                print("="*80)
                print(f"Total Sales: ₹{total:.2f}\n")
            else:
                print("No sales found for the specified date")

        elif option == "3.5":
            summary = self.billing.get_sales_summary()
            if summary[0] > 0:
                total_bills, total_sales, avg_bill, max_bill = summary
                print("\n" + "="*50)
                print("SALES SUMMARY")
                print("="*50)
                print(f"Total Bills: {total_bills}")
                print(f"Total Sales: ₹{total_sales:.2f}")
                print(f"Average Bill Value: ₹{avg_bill:.2f}")
                print(f"Highest Bill Value: ₹{max_bill:.2f}")
                print("="*50 + "\n")
            else:
                print("No sales data available")

    def _save_bill_to_file(self, bill_number, filename):
        """Save bill to text file"""
        bill = self.billing.get_bill(bill_number)
        if not bill:
            return

        try:
            with open(filename, 'w') as f:
                f.write("="*70 + "\n")
                f.write(" "*20 + "ELECTRICAL SHOP INVOICE\n")
                f.write("="*70 + "\n")
                f.write(f"Bill #: {bill['bill_number']:<40} Date: {bill['created_at']}\n")
                f.write(f"Customer: {bill['customer_name']:<55}\n")
                f.write("-"*70 + "\n")
                f.write(f"{'Item':<30} {'Qty':<8} {'Price':<12} {'Total':<15}\n")
                f.write("-"*70 + "\n")

                for item in bill['items']:
                    item_id, product_id, product_name, qty, unit_price, total_price = item
                    f.write(f"{product_name:<30} {qty:<8} ₹{unit_price:<11.2f} ₹{total_price:<14.2f}\n")

                f.write("-"*70 + "\n")
                f.write(f"{'Total Amount':<50} ₹{bill['total_amount']:.2f}\n")
                f.write(f"{'Payment Method':<50} {bill['payment_method']}\n")
                f.write("="*70 + "\n")
                
            print(f"✓ Bill saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving bill: {e}")

    def run(self):
        """Main application loop"""
        print("\nWelcome to Electrical Shop Management System!")
        
        while True:
            self.display_menu()
            option = input("Select option: ").strip()

            if option == "0":
                print("\nThank you for using Electrical Shop Management System!")
                self.products.close()
                self.stock.close()
                self.billing.close()
                sys.exit(0)

            elif option.startswith("1"):
                self.handle_products(option)

            elif option.startswith("2"):
                self.handle_stock(option)

            elif option.startswith("3"):
                self.handle_billing(option)

            else:
                print("✗ Invalid option. Please try again.")

            input("\nPress Enter to continue...")

def main():
    system = ElectricalShopSystem()
    system.run()

if __name__ == "__main__":
    main()
