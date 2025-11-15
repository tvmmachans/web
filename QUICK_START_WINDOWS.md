# 🚀 Quick Start Guide for Windows

## Step 1: Initial Setup (One-Time)

Run this PowerShell script to set up everything:

```powershell
.\scripts\start-dev.ps1
```

This will:
- ✅ Check Python and Node.js installation
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Install all Node.js dependencies
- ✅ Create `.env` file from template

## Step 2: Configure Environment

Edit `.env` file and add your API keys:

```env
# Required
OPENAI_API_KEY=your_openai_key_here
YOUTUBE_API_KEY=your_youtube_key_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_token_here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/social_media_manager
REDIS_URL=redis://localhost:6379/0
```

## Step 3: Start Services

### Option A: Use Individual Scripts (Recommended)

**Terminal 1 - Backend:**
```powershell
.\scripts\start-backend.ps1
```

**Terminal 2 - Frontend:**
```powershell
.\scripts\start-frontend.ps1
```

**Terminal 3 - Agent (Optional, for background tasks):**
```powershell
.\venv\Scripts\Activate.ps1
cd agent
python -m celery -A celery_app worker --loglevel=info
```

### Option B: Manual Commands

**Terminal 1 - Backend:**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Navigate to backend
cd backend

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

## Step 4: Access the System

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Automation Dashboard:** http://localhost:3000/automation

## Troubleshooting

### "uvicorn is not recognized"

**Solution:** Make sure you:
1. Activated the virtual environment: `.\venv\Scripts\Activate.ps1`
2. Installed dependencies: `pip install -r requirements.txt`
3. Are using `python -m uvicorn` instead of just `uvicorn`

### "Python is not recognized"

**Solution:**
1. Install Python 3.9+ from https://www.python.org/
2. Make sure "Add Python to PATH" is checked during installation
3. Restart PowerShell after installation

### "npm is not recognized"

**Solution:**
1. Install Node.js 18+ from https://nodejs.org/
2. Restart PowerShell after installation

### Virtual Environment Issues

If you get permission errors, run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use

If port 8000 or 3000 is already in use:
- Backend: Change port in `start-backend.ps1` or use `--port 8001`
- Frontend: Change port in `frontend/package.json` or use `PORT=3001 npm run dev`

## Next Steps

1. **Set up Database:**
   ```powershell
   .\scripts\init_local.ps1
   ```

2. **Start Automation:**
   - Go to http://localhost:3000/automation
   - Click "🚀 Start Automation"
   - Monitor progress in real-time

3. **View Analytics:**
   - Go to http://localhost:3000/analytics
   - See performance metrics

## Common Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
pip install -r agent/requirements-agent.txt

# Install Node.js dependencies
cd frontend
npm install

# Run database migrations
cd backend
python -m alembic upgrade head

# Run tests
.\scripts\run-tests.ps1
```

## Need Help?

- Check `AUTONOMOUS_SYSTEM_README.md` for full documentation
- Check `SYSTEM_SUMMARY.md` for system overview
- Check backend logs for errors
- Check frontend console for errors

