# Running Setup in Cursor IDE

## ✅ Yes, you can run commands in Cursor!

You can run Python scripts directly in Cursor's integrated terminal. Here's how:

## Current Issue

The database initialization is failing because the user `finance_user` doesn't exist or has wrong credentials.

## Solution: Create the User

### Option 1: Using pgAdmin (Easiest)

1. **Open pgAdmin** (Start Menu → PostgreSQL → pgAdmin 4)
2. **Connect to your PostgreSQL server** (use your postgres password)
3. **Right-click on your server → Query Tool**
4. **Open the file `create_db_user.sql`** in Cursor
5. **Copy the SQL commands** from `create_db_user.sql`
6. **Paste into pgAdmin Query Tool** and run (F5)

The SQL commands are:
```sql
CREATE USER finance_user WITH PASSWORD 'finance_pass';
GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
\c finance_insight
GRANT ALL ON SCHEMA public TO finance_user;
```

### Option 2: Using psql Command Line

If you have psql in your PATH:

```powershell
# Connect to PostgreSQL
psql -U postgres

# Then run:
CREATE USER finance_user WITH PASSWORD 'finance_pass';
GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
\c finance_insight
GRANT ALL ON SCHEMA public TO finance_user;
\q
```

---

## After Creating the User

Once the user is created, you can run these commands **directly in Cursor's terminal**:

### Step 1: Initialize Database Schema
```powershell
python scripts/init_db.py
```

**Expected output:**
```
Step 1: Checking database existence...
Database 'finance_insight' already exists.
Step 2: Running Alembic migrations...
Migrations completed successfully.
Step 3: Verifying schema...
  ✓ use_cases
  ✓ use_case_runs
  ✓ dim_hierarchy
  ✓ metadata_rules
  ✓ fact_pnl_gold
  ✓ fact_calculated_results
Database initialization completed successfully!
```

### Step 2: Generate Mock Data
```powershell
python scripts/generate_mock_data.py
```

**Expected output:**
```
Generating and loading mock data...
Data Generation Summary
Fact rows generated: 1000
Hierarchy nodes generated: 50+
...
```

### Step 3: Test Everything
```powershell
python scripts/test_backend.py
```

**Expected output:**
```
[OK] Database Connection: SUCCESS
[OK] Database Tables: SUCCESS
[OK] Mock Data: SUCCESS
[OK] Backend Health: SUCCESS
[OK] Discovery API: SUCCESS
```

---

## Quick Commands Summary

Run these in Cursor's terminal (in order):

```powershell
# 1. Initialize database (creates tables)
python scripts/init_db.py

# 2. Generate mock data
python scripts/generate_mock_data.py

# 3. Test everything
python scripts/test_backend.py
```

---

## If You Used Different Credentials

If you created the user with a different username/password:

1. **Edit `.env` file** in the project root
2. **Update the DATABASE_URL**:
   ```
   DATABASE_URL=postgresql://your_username:your_password@localhost:5432/finance_insight
   ```
3. **Then run the scripts above**

---

## Next Steps After Setup

Once all tests pass:
1. ✅ Backend should already be running (http://localhost:8000)
2. ✅ Frontend should already be running (http://localhost:3000)
3. ✅ Open http://localhost:3000 in browser
4. ✅ Select "MOCK_ATLAS_v1" from dropdown
5. ✅ Grid should populate with data!

**Phase 1 will be complete!** 🎉

