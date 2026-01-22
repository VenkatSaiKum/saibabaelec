# PostgreSQL Migration Guide for Render

## Overview
The app has been migrated to support PostgreSQL for persistent data storage. When deployed on Render with a PostgreSQL database, your data will **never be lost**.

## Local Development (SQLite - Unchanged)
When running locally without a `DATABASE_URL` environment variable, the app will automatically use SQLite as before. No changes needed for local testing.

## Deployment to Render with PostgreSQL

### Step 1: Create a PostgreSQL Database on Render
1. Go to https://dashboard.render.com/
2. Click "New +" → Select "PostgreSQL"
3. Enter a name (e.g., `electrical-shop-db`)
4. Select the free tier
5. Click "Create Database"
6. Wait for the database to be created (2-3 minutes)

### Step 2: Copy the Database URL
1. In Render dashboard, find your PostgreSQL database
2. Go to "Info" tab
3. Copy the "External Database URL" (starts with `postgresql://`)
4. Keep this URL safe - you'll need it in the next step

### Step 3: Add Environment Variable to Your Web Service
1. Go to your Web Service on Render (your Flask app)
2. Go to "Environment" settings
3. Click "Add Environment Variable"
4. Set the variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL URL you copied
5. Click "Save Changes"
6. Your app will automatically redeploy

### Step 4: Verify Migration
1. Wait for the app to redeploy (takes ~1-2 minutes)
2. Check the deployment logs for any errors
3. Access your app - all tables will be automatically created on first run
4. Test by adding a product or bill

## What Happens on First Run?
When the app starts with `DATABASE_URL` set:
1. It connects to PostgreSQL on Render
2. Automatically creates all tables (if they don't exist)
3. No data migration needed - fresh start on Render
4. Your local SQLite database remains unchanged

## Switching Between Local and Render
- **Local development**: Remove `DATABASE_URL` environment variable → uses SQLite
- **On Render**: `DATABASE_URL` is set → uses PostgreSQL

## Backup & Data Persistence
PostgreSQL on Render provides:
- ✅ Automatic daily backups
- ✅ Data persists even if the app spins down
- ✅ 90-day backup retention
- ✅ No ephemeral file system issues

## Troubleshooting

### "DATABASE_URL not set" error
- Make sure you added the environment variable to Render
- Check the variable name is exactly `DATABASE_URL`
- Redeploy the app

### Connection errors
- Verify the PostgreSQL database URL is correct
- Check the database is active in Render dashboard
- Review app logs in Render for connection errors

### Existing data on Render?
- If you already have data in the free tier SQLite, you'll need to manually migrate it
- Or start fresh with PostgreSQL (recommended for reliability)

## Database Size Limits
Render's free PostgreSQL:
- 256MB storage included
- Good for up to 100,000+ records depending on usage
- Sufficient for a small electrical shop system

If you outgrow limits, simply upgrade to a paid plan.

## Support
For detailed Render PostgreSQL docs, visit:
https://render.com/docs/databases
