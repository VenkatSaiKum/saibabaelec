# Electrical Shop Stock Management System

A comprehensive stock management system designed for electrical shops with features for product management, stock tracking, and billing.

## Features

### 1. **Product Management**
- Add new products with name, category, unit price, and minimum stock level
- View all products in organized table format
- Update product details (name, category, price, minimum stock)
- Delete products from inventory
- View low stock products that need reordering

### 2. **Stock Management**
- Add stock to products
- Remove stock with validation
- Track stock movements with timestamps
- View complete stock history for each product
- Generate comprehensive stock reports with inventory valuation
- Automatic low-stock alerts

### 3. **Billing & Sales**
- Create bills/invoices for customers
- Automatic stock deduction on bill creation
- Automatic tracking of sales transactions
- View previous bills with all transaction details
- Generate daily sales reports
- Sales summary statistics
- Save bills to text files for printing

### 4. **Database**
- SQLite database for reliable data storage
- Organized tables for products, stock movements, and transactions
- Transaction records with item-level details
- Automatic timestamps for all operations

## Project Structure

```
electrical_shop_system/
├── database.py          # Database connection and initialization
├── products.py          # Product management module
├── stock.py            # Stock management module
├── billing.py          # Billing and transaction module
├── main.py             # Main application with CLI interface
├── data/               # Database storage directory
│   └── electrical_shop.db
└── README.md           # This file
```

## Installation

### Requirements
- Python 3.6+
- No external dependencies (uses built-in sqlite3)

### Setup

1. Navigate to the project directory:
```bash
cd electrical_shop_system
```

2. Run the application:
```bash
python main.py
```

## Usage

### Running the Application

```bash
python main.py
```

This will launch an interactive menu with the following options:

### Menu Structure

```
1. PRODUCT MANAGEMENT
   1.1 - Add Product
   1.2 - View All Products
   1.3 - Update Product
   1.4 - Delete Product
   1.5 - View Low Stock Products

2. STOCK MANAGEMENT
   2.1 - Add Stock
   2.2 - Remove Stock
   2.3 - View Stock Report
   2.4 - View Stock History

3. BILLING & SALES
   3.1 - Create Bill
   3.2 - View Bill
   3.3 - View Recent Bills
   3.4 - View Daily Sales
   3.5 - Sales Summary

0. Exit
```

## Example Workflow

### 1. Add Products
```
Menu: 1.1 (Add Product)
Input:
  - Product Name: LED Bulb 10W
  - Category: Bulbs
  - Unit Price: 150.00
  - Initial Quantity: 50
  - Minimum Stock Level: 10
```

### 2. Add Stock
```
Menu: 2.1 (Add Stock)
Input:
  - Product ID: 1
  - Quantity to Add: 20
```

### 3. Create a Bill
```
Menu: 3.1 (Create Bill)
Input:
  - Customer Name: John Doe
  - Product ID: 1 (LED Bulb)
  - Quantity: 5
  - Payment Method: CASH
```

### 4. View Reports
```
Menu: 2.3 (View Stock Report) - See all products with inventory value
Menu: 3.3 (View Recent Bills) - See transaction history
Menu: 3.5 (Sales Summary) - Get sales statistics
```

## Database Schema

### Products Table
```sql
- id: Primary key
- name: Product name (unique)
- category: Product category
- unit_price: Price per unit
- quantity: Current stock quantity
- minimum_stock: Reorder level
- created_at: Creation timestamp
```

### Stock Movements Table
```sql
- id: Primary key
- product_id: Reference to products
- movement_type: ADD, REMOVE, or SALE
- quantity: Movement quantity
- reference_id: Transaction ID for sales
- notes: Additional information
- created_at: Timestamp
```

### Transactions Table
```sql
- id: Primary key
- customer_name: Customer name
- total_amount: Total bill amount
- payment_method: CASH, CARD, CHEQUE
- bill_number: Unique bill identifier
- created_at: Transaction timestamp
```

### Transaction Items Table
```sql
- id: Primary key
- transaction_id: Reference to transactions
- product_id: Product sold
- quantity: Quantity sold
- unit_price: Price at time of sale
- total_price: Item total
```

## Features in Detail

### Low Stock Alerts
Products below minimum stock level are automatically marked with ⚠️ LOW indicator in all product lists.

### Stock History
Track every stock movement with:
- Movement type (ADD, REMOVE, SALE)
- Quantity
- Timestamp
- Notes/reason

### Bill Management
- Automatic bill numbering (BILL-YYYYMMDDHHMMSS)
- Customer name tracking
- Itemized billing
- Stock automatic deduction
- Payment method recording
- Bill saved to text files

### Reports
- **Stock Report**: Current inventory with valuations
- **Daily Sales**: Sales for specific date
- **Sales Summary**: Total bills, revenue, average bill value
- **Stock History**: Track movements per product

## Tips & Best Practices

1. **Inventory Management**
   - Set appropriate minimum stock levels
   - Check low stock products regularly (Option 1.5)
   - Monitor stock reports (Option 2.3)

2. **Billing**
   - Always verify customer name before creating bill
   - Check product availability before billing
   - Save important bills

3. **Stock Tracking**
   - Add notes when adding stock (supplier info)
   - Use stock history to analyze patterns
   - Regular stock audits using reports

## Troubleshooting

### Database Not Found
- Ensure the `data/` directory exists
- Database will auto-create on first run

### Bill Creation Fails
- Check if product exists
- Verify sufficient stock available
- Ensure product ID is correct

### Missing Product
- Use Option 1.2 to verify product exists
- Check spelling of product name
- Use correct product ID from the table

## Future Enhancements

- Supplier management
- Purchase orders
- Customer credit system
- Inventory analytics
- Multi-user support
- Backup/restore functionality
- Export to Excel reports
- GST calculations

## License

This project is open-source and available for use in electrical shops.

## Support

For issues or feature requests, please contact the development team.
