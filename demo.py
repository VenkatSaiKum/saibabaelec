#!/usr/bin/env python3
"""
Demo script to populate the electrical shop system with sample data
and demonstrate its functionality
"""

from products import ProductManager
from stock import StockManager
from billing import BillingManager

def demo():
    print("\n" + "="*70)
    print("ELECTRICAL SHOP MANAGEMENT SYSTEM - DEMO")
    print("="*70)
    
    products = ProductManager()
    stock = StockManager()
    billing = BillingManager()

    # Sample products data
    sample_products = [
        ("LED Bulb 10W", "Bulbs", 150.00, 50, 10),
        ("LED Bulb 20W", "Bulbs", 250.00, 30, 8),
        ("Switch Single Pole", "Switches", 80.00, 100, 15),
        ("Switch Two Pole", "Switches", 120.00, 75, 12),
        ("Electrical Wire (per meter)", "Wiring", 15.00, 500, 50),
        ("Socket 15A", "Sockets", 60.00, 60, 10),
        ("Socket 20A", "Sockets", 90.00, 40, 8),
        ("Breaker MCB 20A", "Breakers", 200.00, 25, 5),
        ("Cable Gland M20", "Accessories", 45.00, 80, 10),
        ("Conduit Pipe (per meter)", "Conduit", 25.00, 200, 30),
    ]

    print("\n✓ Adding sample products...")
    for name, category, price, qty, min_stock in sample_products:
        products.add_product(name, category, price, qty, min_stock)

    print("\n" + "="*70)
    print("ALL PRODUCTS IN INVENTORY")
    print("="*70)
    products.display_all_products()

    print("\n✓ Adding additional stock for selected items...")
    stock.add_stock(1, 20, "Restock from supplier ABC")
    stock.add_stock(3, 30, "Restock from supplier XYZ")

    print("\n" + "="*70)
    print("STOCK REPORT")
    print("="*70)
    stock.display_stock_report()

    print("\n✓ Creating sample bills...")
    
    # Bill 1
    bill1 = billing.create_bill(
        "Rajesh Kumar",
        [(1, 5), (3, 2), (5, 10)],
        "CASH"
    )
    
    # Bill 2
    bill2 = billing.create_bill(
        "Priya Singh",
        [(2, 3), (4, 1), (7, 2)],
        "CARD"
    )
    
    # Bill 3
    bill3 = billing.create_bill(
        "Arjun Verma",
        [(6, 4), (8, 1), (9, 5)],
        "CASH"
    )

    if bill1:
        print("\n" + "="*70)
        print("BILL #1 DETAILS")
        print("="*70)
        billing.display_bill(bill1)

    if bill2:
        print("\n" + "="*70)
        print("BILL #2 DETAILS")
        print("="*70)
        billing.display_bill(bill2)

    print("\n" + "="*70)
    print("RECENT BILLS (Last 5)")
    print("="*70)
    billing.display_bill_history(5)

    print("\n" + "="*70)
    print("SALES SUMMARY")
    print("="*70)
    summary = billing.get_sales_summary()
    if summary and summary[0] > 0:
        total_bills, total_sales, avg_bill, max_bill = summary
        print(f"Total Bills Created: {total_bills}")
        print(f"Total Sales Amount: ₹{total_sales:.2f}")
        print(f"Average Bill Value: ₹{avg_bill:.2f}")
        print(f"Highest Bill Value: ₹{max_bill:.2f}")

    print("\n" + "="*70)
    print("UPDATED STOCK REPORT (After Sales)")
    print("="*70)
    stock.display_stock_report()

    print("\n" + "="*70)
    print("LOW STOCK PRODUCTS")
    print("="*70)
    low_stock = products.get_low_stock_products()
    if low_stock:
        print(f"{'ID':<5} {'Name':<25} {'Current':<10} {'Min Stock':<10}")
        print("-"*50)
        for product in low_stock:
            product_id, name, _, _, qty, min_stock_level, _ = product
            print(f"{product_id:<5} {name:<25} {qty:<10} {min_stock_level:<10}")
    else:
        print("No low stock products at the moment")

    print("\n" + "="*70)
    print("STOCK HISTORY FOR LED BULB 10W (Product ID: 1)")
    print("="*70)
    stock.display_stock_history(1)

    print("\n" + "="*70)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nYou can now run 'python main.py' to use the interactive menu system")
    print("\nNote: Demo data has been saved to the database and will persist")
    print("between sessions.\n")

    products.close()
    stock.close()
    billing.close()

if __name__ == "__main__":
    demo()
