# PostgreSQL Setup Guide for Finance-Insight

## Quick Setup for Windows

### Option 1: Install PostgreSQL Locally (Recommended)

1. **Download PostgreSQL**
   - Go to: https://www.postgresql.org/download/windows/
   - Download the installer (e.g., PostgreSQL 15 or 16)
   - Run the installer

2. **During Installation:**
   - Choose installation directory (default is fine)
   - **Remember the password you set for the `postgres` user**
   - Port: 5432 (default)
   - Locale: Default

3. **After Installation:**
   - PostgreSQL service should start automatically
   - Verify it's running: Open Services (Win+R → `services.msc`) and look for "postgresql-x64-XX"

4. **Create Database and User:**
   
   Open **pgAdmin** (installed with PostgreSQL) or use **psql** command line:
   
   ```sql
   -- Connect as postgres superuser
   -- In pgAdmin: Right-click "PostgreSQL" → Query Tool
   -- Or use psql: psql -U postgres
   
   -- Create database
   CREATE DATABASE finance_insight;
   
   -- Create user
   CREATE USER finance_user WITH PASSWORD 'finance_pass';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
   
   -- Connect to the new database
   \c finance_insight
   
   -- Grant schema privileges
   GRANT ALL ON SCHEMA public TO finance_user;
   ```

5. **Update Connection (if needed):**
   
   The default connection in `app/database.py` is:
   ```
   postgresql://finance_user:finance_pass@localhost:5432/finance_insight
   ```
   
   If you used different credentials, create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://your_user:your_password@localhost:5432/finance_insight
   ```

---

### Option 2: Use Docker (Alternative)

If you have Docker installed:

```powershell
# Run PostgreSQL in Docker
docker run --name finance-postgres `
  -e POSTGRES_USER=finance_user `
  -e POSTGRES_PASSWORD=finance_pass `
  -e POSTGRES_DB=finance_insight `
  -p 5432:5432 `
  -d postgres:15

# Verify it's running
docker ps
```

---

### Option 3: Use Existing PostgreSQL

If you already have PostgreSQL installed:

1. **Find your PostgreSQL connection details:**
   - Host: Usually `localhost`
   - Port: Usually `5432`
   - Username: Your PostgreSQL username
   - Password: Your PostgreSQL password

2. **Create database and user:**
   ```sql
   CREATE DATABASE finance_insight;
   CREATE USER finance_user WITH PASSWORD 'finance_pass';
   GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
   ```

3. **Update connection in `.env` file:**
   ```env
   DATABASE_URL=postgresql://finance_user:finance_pass@localhost:5432/finance_insight
   ```

---

## Verify PostgreSQL is Running

### Check Service (Windows):
```powershell
Get-Service -Name "*postgresql*"
```

### Test Connection:
```powershell
# If psql is in PATH
psql -U finance_user -d finance_insight -h localhost

# Or test with Python
python -c "from app.database import get_database_url; from sqlalchemy import create_engine; engine = create_engine(get_database_url()); print('Connected!' if engine.connect() else 'Failed')"
```

---

## After PostgreSQL is Set Up

1. **Initialize Database:**
   ```powershell
   python scripts/init_db.py
   ```

2. **Generate Mock Data:**
   ```powershell
   python scripts/generate_mock_data.py
   ```

3. **Test Backend:**
   ```powershell
   python scripts/test_backend.py
   ```

---

## Troubleshooting

### "Connection refused" Error
- **Solution**: PostgreSQL service is not running
  - Start it: `net start postgresql-x64-XX` (replace XX with version)
  - Or use Services app to start it

### "Authentication failed" Error
- **Solution**: Wrong username/password
  - Check `.env` file or `app/database.py`
  - Verify user exists: `SELECT * FROM pg_user WHERE usename = 'finance_user';`

### "Database does not exist" Error
- **Solution**: Create the database (see SQL commands above)

### Port 5432 Already in Use
- **Solution**: Another PostgreSQL instance is running
  - Find and stop it, or use a different port
  - Update `DATABASE_URL` with new port

---

## Next Steps

Once PostgreSQL is set up and running:

1. ✅ Initialize database: `python scripts/init_db.py`
2. ✅ Generate mock data: `python scripts/generate_mock_data.py`
3. ✅ Test backend: `python scripts/test_backend.py`
4. ✅ Restart backend server (if it was running)
5. ✅ Test frontend: Open http://localhost:3000

---

**Need Help?** Check the test script output for specific error messages.

