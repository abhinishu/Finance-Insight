# Quick Fix: Database Connection Issue

## The Problem
Password authentication is failing for user `finance_user`.

## Solution Options

### Option 1: Use Default Credentials (Easiest)

If you haven't created the user yet, run this in **pgAdmin Query Tool** or **psql**:

```sql
-- Connect as postgres superuser first
CREATE USER finance_user WITH PASSWORD 'finance_pass';
GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
\c finance_insight
GRANT ALL ON SCHEMA public TO finance_user;
```

Then try again:
```powershell
python scripts/init_db.py
```

---

### Option 2: Use Your Custom Credentials

If you created the user with different credentials:

1. **Create or edit `.env` file** in the project root:
   ```
   DATABASE_URL=postgresql://your_username:your_password@localhost:5432/finance_insight
   ```

2. **Replace:**
   - `your_username` with your PostgreSQL username
   - `your_password` with your PostgreSQL password
   - `finance_insight` with your database name (if different)

3. **Then run:**
   ```powershell
   python scripts/init_db.py
   ```

---

### Option 3: Test with postgres Superuser (Temporary)

If you want to test quickly with the postgres superuser:

1. **Create `.env` file:**
   ```
   DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/finance_insight
   ```
   (Replace `YOUR_POSTGRES_PASSWORD` with the password you set during PostgreSQL installation)

2. **Make sure database exists:**
   ```sql
   CREATE DATABASE finance_insight;
   ```

3. **Then run:**
   ```powershell
   python scripts/init_db.py
   ```

---

## After Connection Works

Once `python scripts/init_db.py` succeeds, continue with:

```powershell
# Generate mock data
python scripts/generate_mock_data.py

# Test everything
python scripts/test_backend.py
```

---

## Verify Your Setup

To check what users/databases exist in PostgreSQL:

**In pgAdmin:**
- Right-click "Login/Group Roles" → Refresh → Check if `finance_user` exists
- Right-click "Databases" → Refresh → Check if `finance_insight` exists

**In psql:**
```sql
\du          -- List users
\l           -- List databases
```

