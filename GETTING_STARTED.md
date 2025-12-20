# Getting Started with Finance-Insight

## ✅ Setup Complete

Your repository has been cloned and dependencies are installed!

### What's Done:
- ✅ Repository cloned from GitHub
- ✅ Python dependencies installed (FastAPI, SQLAlchemy, Pandas, etc.)
- ✅ Node.js dependencies installed (React, AG-Grid, etc.)
- ✅ Project structure verified

---

## 📋 Next Steps to Get Running

### 1. Set Up PostgreSQL Database

**Option A: If you have PostgreSQL installed locally:**
- Default connection: `postgresql://finance_user:finance_pass@localhost:5432/finance_insight`
- Update `app/database.py` or create a `.env` file with your credentials

**Option B: Create a `.env` file:**
```env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/finance_insight
```

### 2. Initialize Database

Run the initialization script to create tables and run migrations:

```powershell
python scripts/init_db.py
```

This will:
- Create the database if it doesn't exist
- Run Alembic migrations to create all tables
- Verify the schema

### 3. Generate Mock Data

Load sample data for testing:

```powershell
python scripts/generate_mock_data.py
```

This generates:
- 1,000 P&L fact rows
- Ragged hierarchy with 50 leaf nodes
- Test data for all measures (Daily, MTD, YTD, PYTD)

### 4. Start Backend Server

```powershell
uvicorn app.main:app --reload
```

Backend will run on: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 5. Start Frontend Server

Open a new terminal:

```powershell
cd frontend
npm run dev
```

Frontend will run on: **http://localhost:3000**

---

## 🎯 Current Project Status

### Phase 1: ✅ COMPLETE
- Database schema and migrations
- Mock data generation
- Waterfall calculation engine
- Mathematical validation
- Discovery API endpoint

### Phase 2: ⏳ NEXT UP
- Complete REST API for use cases, rules, calculations
- GenAI rule builder integration (Google Gemini)
- Rule preview system
- Atlas integration mock

### Phase 3: ⏳ PLANNED
- React frontend with three-tab interface
- AG-Grid integration
- Full UI/UX implementation

---

## 🔍 Quick Verification

### Test Backend:
```powershell
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Test Discovery API:
```powershell
curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"
# Should return hierarchy JSON
```

### Test Frontend:
- Open http://localhost:3000
- Should see Finance-Insight Discovery screen
- Select "MOCK_ATLAS_v1" structure
- View hierarchy tree with natural values

---

## 📚 Key Documentation

- **Quick Start**: `QUICK_START.md` - Fastest way to get running
- **Phase 1 Status**: `docs/PHASE_1_COMPLETE.md` - What's been built
- **Phase 2 Requirements**: `docs/PHASE_2_REQUIREMENTS.md` - Next steps
- **Project Plan**: `docs/PHASED_PLAN.md` - Full roadmap
- **Technical Spec**: `docs/TECHNICAL_SPEC.md` - Architecture details

---

## 🐛 Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check credentials in `app/database.py` or `.env`
- Verify database exists: `psql -U finance_user -d finance_insight`

### Port Already in Use
- Backend (8000): Change in `uvicorn` command or kill existing process
- Frontend (3000): Change in `frontend/vite.config.ts`

### Missing Dependencies
- Python: `pip install -r requirements.txt`
- Node: `cd frontend && npm install`

---

## 🚀 Ready to Continue Development

You're all set! The foundation is complete. Next steps:

1. **Complete Phase 2**: Build out the full REST API
2. **Add GenAI Integration**: Implement natural language rule builder
3. **Build Frontend**: Create the React UI with three tabs

Check `docs/PHASE_2_REQUIREMENTS.md` for detailed next steps.

---

**Happy Coding!** 🎉

