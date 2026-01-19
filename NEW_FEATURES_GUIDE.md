# New Features Implementation Guide

## 🔐 Login Credentials

### Admin Access
- **Username**: `admin`
- **Password**: `saibaba99`
- **Access**: Full system access (Dashboard, Products, Stock, Billing, Expenses, Supplier Bills, Reports)

### Staff Access
- **Username**: `staff`
- **Password**: `staff123`
- **Access**: Limited to Billing and Expenses only

---

## 📋 Feature 1: Staff Login with Limited Access

### What's New:
- **Staff users** can now log in with separate credentials
- Staff automatically redirected to Billing page upon login
- Staff can only access:
  - ✅ Billing (Create bills, view bill history)
  - ✅ Expenses (Add and manage expenses)
- Staff **cannot** access:
  - ❌ Dashboard
  - ❌ Products Management
  - ❌ Stock Management
  - ❌ Supplier Bills
  - ❌ Reports

### How It Works:
1. Login with staff credentials
2. Automatically redirected to Billing page
3. Navigation menu shows only Billing and Expenses options
4. Username displayed in navbar with "(Staff)" badge

---

## 💳 Feature 2: Credit Option in Billing

### What's New:
- New **Bill Type** dropdown in billing form with three options:
  1. **Regular Sale** - Normal customer sales (counted in daily sales)
  2. **Credit (Wholesale)** - Wholesale customers on credit
  3. **Replacement** - Item replacements

### Credit Bill Behavior:
- ✅ Stock is reduced from inventory
- ✅ Bill is created and stored in "Wholesale customers on credit"
- ❌ **NOT** counted in today's sales reports
- ❌ **NOT** included in daily sales totals
- Bill is marked with `is_credit = 1` in database

### How to Create Credit Bill:
1. Go to Billing page
2. Fill customer name and other details
3. Select **Bill Type: Credit (Wholesale)**
4. Add items to bill
5. Click "Create Bill"
6. Confirmation message shows: "(Added to Wholesale Customers on Credit - Not counted in today's sales)"

### Viewing Credit Transactions:
- Credit transactions available via API: `/api/sales/credit`
- Can be viewed separately from regular sales

---

## 🔄 Feature 3: Replacement Option in Billing

### What's New:
- **Bill Type: Replacement** option for replacement items given to customers

### Replacement Bill Behavior:
- ✅ Stock is reduced from inventory
- ❌ **NOT** counted in today's sales
- ❌ **NOT** included in sales reports
- Bill is marked with `is_replacement = 1` in database

### How to Create Replacement Bill:
1. Go to Billing page
2. Fill customer name and other details
3. Select **Bill Type: Replacement**
4. Add items to bill
5. Click "Create Bill"
6. Confirmation message shows: "(Replacement - Stock reduced but not counted in today's sales)"

### Viewing Replacement Transactions:
- Replacement transactions available via API: `/api/sales/replacements`
- Can be viewed separately from regular sales

---

## 📊 Impact on Reports and Sales

### Sales Calculations (Updated):
- **Daily Sales Report**: Shows only REGULAR sales (excludes Credit & Replacement)
- **Sales Summary**: 
  - Total Bills: Counts only REGULAR sales
  - Total Sales: Sum of only REGULAR sales
  - Average Bill: Calculated from REGULAR sales only
  - Max Bill: Maximum from REGULAR sales only

### Stock Management:
- All three bill types (Regular, Credit, Replacement) reduce stock
- Stock movements recorded for all transaction types
- Stock tracking remains accurate across all bill types

---

## 🗄️ Database Changes

### New Columns in `transactions` Table:
- `bill_type` - TEXT: "REGULAR", "CREDIT", or "REPLACEMENT"
- `is_credit` - INTEGER: 1 if credit bill, 0 otherwise
- `is_replacement` - INTEGER: 1 if replacement bill, 0 otherwise

### Backward Compatibility:
- Existing transactions automatically default to:
  - `bill_type = 'REGULAR'`
  - `is_credit = 0`
  - `is_replacement = 0`
- Old bills continue to work without any issues

---

## 🔗 New API Endpoints

### Credit Transactions:
```
GET /api/sales/credit?limit=50
```
Returns list of all credit transactions (wholesale customers on credit)

### Replacement Transactions:
```
GET /api/sales/replacements?limit=50
```
Returns list of all replacement transactions

### Daily Sales (Updated):
```
GET /api/sales/daily?date=2026-01-10
```
Now automatically excludes credit and replacement transactions

---

## 🎯 Use Cases

### Scenario 1: Staff Member Creating Bills
1. Staff logs in with `staff/staff123`
2. Directed to Billing page
3. Creates regular customer bills
4. Can add expenses (shop supplies, electricity, etc.)
5. Cannot access product management or reports

### Scenario 2: Wholesale Credit Customer
1. Wholesale customer purchases items on credit
2. Create bill with **Bill Type: Credit (Wholesale)**
3. Customer name: "ABC Traders"
4. Stock is reduced immediately
5. Bill stored separately from daily sales
6. Can be tracked for payment collection later

### Scenario 3: Item Replacement
1. Customer returns defective item
2. Give replacement item
3. Create bill with **Bill Type: Replacement**
4. Stock is reduced for replacement item
5. No impact on daily sales figures
6. Proper inventory tracking maintained

---

## ✅ Testing Checklist

- [x] Staff login works and redirects to billing
- [x] Staff can access only Billing and Expenses
- [x] Admin can access all pages
- [x] Credit bill reduces stock but not counted in sales
- [x] Replacement bill reduces stock but not counted in sales
- [x] Regular bill counted in daily sales as before
- [x] Sales reports exclude credit and replacement
- [x] Navigation menu shows/hides based on role
- [x] Database schema updated with new columns
- [x] All existing bills continue to work

---

## 🚀 Getting Started

1. **Run the application**:
   ```powershell
   python app.py
   ```

2. **Login as Admin**:
   - Username: `admin`
   - Password: `saibaba99`
   - Access all features

3. **Login as Staff**:
   - Username: `staff`
   - Password: `staff123`
   - Access billing and expenses only

4. **Create Different Bill Types**:
   - Regular: Normal customer sales
   - Credit: Wholesale customers (on credit)
   - Replacement: Item replacements

---

## 📞 Support

For any issues or questions, refer to this guide or check the application logs for debugging information.

**Version**: 2.0 (January 2026)
**Last Updated**: January 10, 2026
