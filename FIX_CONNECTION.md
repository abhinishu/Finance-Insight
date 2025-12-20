# Fix Database Connection Issue

## Current Problem
Connection is failing even though user was created. This could be:
1. Password mismatch
2. Authentication method issue (pg_hba.conf)
3. .env file has wrong credentials

## Quick Fix Options

### Option 1: Verify User Exists and Reset Password

Run this in **pgAdmin Query Tool**:

```sql
-- Check if user exists
SELECT usename FROM pg_user WHERE usename = 'finance_user';

-- If user exists, reset password to match expected value
ALTER USER finance_user WITH PASSWORD 'finance_pass';

-- Verify privileges
GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
\c finance_insight
GRANT ALL ON SCHEMA public TO finance_user;
```

### Option 2: Update .env with Actual Password

If you set a different password, update `.env` file:

1. **Open `.env` file** in project root
2. **Update the password** in DATABASE_URL:
   ```
   DATABASE_URL=postgresql://finance_user:YOUR_ACTUAL_PASSWORD@localhost:5432/finance_insight
   ```

### Option 3: Test with postgres Superuser (Temporary)

To test if it's a user issue, temporarily use postgres user:

1. **Create `.env` file** (or update existing):
   ```
   DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/finance_insight
   ```

2. **Run initialization:**
   ```powershell
   python scripts/init_db_simple.py
   ```

---

## Verify in pgAdmin

Run `verify_user.sql` in pgAdmin to check:
- User exists
- Database exists  
- Privileges are correct

---

## After Connection Works

Once connection succeeds, run:

```powershell
# Initialize schema
python scripts/init_db_simple.py

# Generate mock data
python scripts/generate_mock_data.py

# Test everything
python scripts/test_backend.py
```

