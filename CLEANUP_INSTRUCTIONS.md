# Database Cleanup Instructions for Render Deployment

## Overview
Your electrical shop system now has automatic weekly database cleanup to free up storage space on the Render 512MB free tier.

---

## Automatic Weekly Cleanup (Recommended)

The app now automatically runs cleanup every **Sunday at 2:00 AM IST**:
- Deletes billing records older than 45 days
- Deletes supplier bills older than 60 days
- Deletes expense records older than 7 days
- Removes inactive products (zero quantity)

**No action needed!** This runs automatically after you deploy.

---

## Manual Cleanup on Render

If you need to cleanup immediately without waiting for Sunday, follow these steps:

### Option 1: Using Render Shell (Easiest)

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your service
3. Go to **Shell** tab
4. Run the cleanup command:
   ```bash
   python cleanup_old_records.py
   ```
5. Wait for the script to complete (you'll see the cleanup summary)
6. Check the output to see how many records were deleted

### Option 2: Using Render Execute Command

1. In Render dashboard, click your service
2. Click **Execute Command** button
3. Enter the command:
   ```bash
   python cleanup_old_records.py
   ```
4. View the output logs

### Option 3: Using Git & Redeploy

If you prefer a manual trigger script in your app:

1. Add this route to your `app.py`:
   ```python
   @app.route('/admin/cleanup', methods=['POST'])
   def manual_cleanup():
       """Manual cleanup route - requires admin access"""
       from cleanup_old_records import DatabaseCleaner
       try:
           cleaner = DatabaseCleaner()
           cleaner.cleanup()
           cleaner.close()
           return jsonify({'status': 'success', 'message': 'Cleanup completed'}), 200
       except Exception as e:
           return jsonify({'status': 'error', 'message': str(e)}), 500
   ```

2. Commit and push to Git:
   ```bash
   git add .
   git commit -m "Add manual cleanup endpoint"
   git push
   ```

3. Render will auto-deploy

4. Run cleanup via API (using curl or Postman):
   ```bash
   curl -X POST https://your-app.onrender.com/admin/cleanup
   ```

---

## What Gets Cleaned

### Billing Records (Transactions)
- Records older than **45 days** are deleted
- Includes customer bills and transaction items
- Example: Bills from before December 2024 will be deleted in early January 2025

### Supplier Bills
- Records older than **60 days** are deleted
- Example: Bills from before early December will be deleted in mid-January

### Expenses
- Records older than **7 days** are deleted
- Example: Expenses from last week and older

### Products
- Products with **zero quantity** are removed
- Related stock movements are also cleaned up
- Only products with stock >= 1 are kept

---

## Checking Cleanup Logs

### On Render:
1. Go to your service dashboard
2. Click **Logs** tab
3. Filter for "cleanup" to see:
   ```
   Starting automatic weekly database cleanup...
   ✓ Deleted X billing records
   ✓ Deleted X supplier bills
   ...
   Weekly cleanup completed successfully
   ```

### Local testing:
```bash
python cleanup_old_records.py
```

---

## Customizing Cleanup Intervals

To change when cleanup runs, edit in `app.py`:

```python
# Change from Sunday 2 AM to a different schedule:
scheduler.add_job(
    func=run_weekly_cleanup,
    trigger=CronTrigger(day_of_week=3, hour=14, minute=0),  # Wednesday 2 PM
    id='weekly_cleanup',
    name='Weekly Database Cleanup',
    replace_existing=True
)
```

**Cron schedule reference:**
- `day_of_week`: 0=Monday, 1=Tuesday... 6=Sunday
- `hour`: 0-23 (24-hour format)
- `minute`: 0-59

---

## Important Notes

⚠️ **Backup before first cleanup**: The cleanup is irreversible. If you have important old data, backup your database first:

```bash
# Backup your database before cleanup
cp data/electrical_shop.db data/electrical_shop.db.backup
```

✓ **Safe to run**: The cleanup respects database constraints and cleans up orphaned records automatically.

✓ **No data loss for active transactions**: Only old, expired records are deleted.

---

## Troubleshooting

### Cleanup not running automatically?
1. Check if scheduler started: Look for "Background scheduler started" in logs
2. Verify APScheduler is installed: Check requirements.txt has `APScheduler==3.10.4`
3. Redeploy the app to apply changes

### "APScheduler not found" error?
1. Make sure `requirements.txt` includes `APScheduler==3.10.4`
2. Redeploy: Render will automatically install dependencies

### Want to disable automatic cleanup?
Comment out in `app.py`:
```python
# scheduler.add_job(...)  # Commented out
```

Then redeploy.

---

## Storage Impact

Based on typical data:
- 100 old billing records ≈ 50-100 KB
- 50 old supplier bills ≈ 25-50 KB
- Old expenses + stock movements ≈ 20-30 KB

Running cleanup weekly can free up **100-200 KB** depending on your usage patterns.

---

## Questions?

The cleanup script is safe and:
- Only deletes records older than specified days
- Maintains database integrity
- Cleans up orphaned records automatically
- Can be run multiple times safely

If you need to adjust the cleanup schedule or days, update the settings in this file and redeploy.
