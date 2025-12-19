# Frontend Setup Guide

## Prerequisites

1. **Node.js installed** (version 16+ recommended)
   - Check: `node --version`
   - Download: https://nodejs.org/

2. **npm installed** (comes with Node.js)
   - Check: `npm --version`

## Setup Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- React 18
- TypeScript
- Vite
- AG-Grid
- Axios

### 2. Start Development Server

```bash
npm run dev
```

Server will start at: `http://localhost:3000`

### 3. Verify Backend is Running

Make sure the FastAPI backend is running:
```bash
# In another terminal
uvicorn app.main:app --reload
```

Backend should be at: `http://localhost:8000`

## Troubleshooting

### Error: "npm is not recognized"
- Install Node.js from https://nodejs.org/
- Restart terminal after installation

### Error: "Port 3000 already in use"
- Change port in `vite.config.ts`:
  ```typescript
  server: {
    port: 3001,  // Change to different port
  }
  ```

### Error: "Cannot find module"
- Run `npm install` again
- Delete `node_modules` and `package-lock.json`, then run `npm install`

### API Connection Error
- Verify backend is running on port 8000
- Check `VITE_API_BASE_URL` in `.env` file (optional)
- Default: `http://localhost:8000`

## Quick Start

```bash
# Terminal 1: Backend
cd C:\Finance-Insight
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd C:\Finance-Insight\frontend
npm install
npm run dev
```

Then open: `http://localhost:3000`

