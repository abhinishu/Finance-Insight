# PostgreSQL Setup Steps - Finance-Insight

## Step 1: Create Database and User

### Using pgAdmin (Easiest):

1. **Open pgAdmin** (installed with PostgreSQL)
   - Usually in Start Menu → PostgreSQL → pgAdmin 4

2. **Connect to PostgreSQL Server**
   - Enter the password you set during PostgreSQL installation
   - (Usually for the `postgres` user)

3. **Right-click on "Databases" → Create → Database**
   - Name: `finance_insight`
   - Click "Save"

4. **Right-click on "Login/Group Roles" → Create → Login/Group Role**
   - General tab:
     - Name: `finance_user`
   - Definition tab:
     - Password: `finance_pass`
   - Privileges tab:
     - Check "Can login?"
     - Check "Create databases?" (optional)
   - Click "Save"

5. **Right-click on `finance_insight` database → Query Tool**
   - Run this SQL:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
   \c finance_insight
   GRANT ALL ON SCHEMA public TO finance_user;
   ```

---

### Using Command Line (psql):

1. **Open Command Prompt or PowerShell**

2. **Add PostgreSQL to PATH** (if needed):
   ```powershell
   $env:Path += ';C:\Program Files\PostgreSQL\15\bin'
   # Or try version 16: C:\Program Files\PostgreSQL\16\bin
   ```

3. **Connect to PostgreSQL**:
   ```powershell
   psql -U postgres
   # Enter your PostgreSQL password when prompted
   ```

4. **Run these SQL commands**:
   ```sql
   CREATE DATABASE finance_insight;
   CREATE USER finance_user WITH PASSWORD 'finance_pass';
   GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
   \c finance_insight
   GRANT ALL ON SCHEMA public TO finance_user;
   \q
   ```

---

## Step 2: Initialize Database Schema

After creating the database and user, run:

```powershell
python scripts/init_db.py
```

**Expected Output:**
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

---

## Step 3: Generate Mock Data

```powershell
python scripts/generate_mock_data.py
```

**Expected Output:**
```
Generating and loading mock data...
Data Generation Summary
Fact rows generated: 1000
Hierarchy nodes generated: 50+
Leaf nodes: 50
...
```

---

## Step 4: Test Everything

```powershell
python scripts/test_backend.py
```

**Expected Output:**
```
[OK] Database Connection: SUCCESS
[OK] Database Tables: SUCCESS
[OK] Mock Data: SUCCESS
[OK] Backend Health: SUCCESS
[OK] Discovery API: SUCCESS
```

---

## Step 5: Verify Frontend

1. **Make sure backend is running:**
   ```powershell
   uvicorn app.main:app --reload
   ```

2. **Open browser:** http://localhost:3000

3. **Select "MOCK_ATLAS_v1"** from dropdown

4. **Expected:** Grid should populate with hierarchy data!

---

## Troubleshooting

### "password authentication failed"
- **Solution:** User doesn't exist or wrong password
- Create the user first (see Step 1)

### "database does not exist"
- **Solution:** Create the database first (see Step 1)

### "permission denied"
- **Solution:** Grant privileges (see Step 1, SQL commands)

### "connection refused"
- **Solution:** PostgreSQL service not running
- Start it: `net start postgresql-x64-15` (or your version)

