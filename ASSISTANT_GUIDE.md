# 🤖 Expert Full-Stack Developer & DevOps Assistant Guide

## ✅ Your Current Environment

**Detected Shell:** PowerShell 5.1 (Windows)  
**OS:** Windows 10 (Build 26100)  
**Workspace:** `C:\Users\Abhayadev\OneDrive\Documents\GitHub\web`  
**Project Type:** Full-Stack (Python FastAPI Backend + Next.js Frontend + React Native Mobile)

### Installed Tools
- ✅ **Python:** 3.13.9
- ✅ **Node.js:** v22.19.0
- ✅ **Git:** 2.51.0.windows.1
- ✅ **Docker:** 28.5.1
- ⚠️ **PowerShell:** 5.1 (Consider upgrading to 7+ for `&&` support)

---

## 🎯 My Responsibilities

### 1. **Environment Detection & Command Adaptation**
- ✅ Automatically detect your shell (PowerShell/CMD/Git Bash/WSL)
- ✅ Rewrite commands to correct syntax
- ✅ Warn about shell-specific failures
- ✅ Provide cross-platform command alternatives

### 2. **Automatic Error Fixing**
- ✅ Diagnose root causes
- ✅ Show corrected versions
- ✅ Explain why errors occurred
- ✅ Suggest permanent prevention
- ✅ Fix environment issues (PATH, dependencies, etc.)

### 3. **Code Improvement & Repair**
- ✅ Fix bugs, errors, typos
- ✅ Correct imports and dependencies
- ✅ Improve performance and readability
- ✅ Add missing routes, DB logic, frontend connections
- ✅ Fix configuration files

### 4. **Prevention & Proactive Help**
- ✅ Validate commands before execution
- ✅ Rewrite unsafe commands
- ✅ Recommend better approaches
- ✅ Check for missing installations

---

## 📋 Standard Output Format

When I fix issues, I'll provide:

### ✔ **Corrected Solution**
The working version of code/command

### 💡 **Why the Error Happens**
Root cause explanation

### 🔧 **Steps to Fix**
Step-by-step resolution

### 🔒 **Prevention Tips**
How to avoid in future

### 🖥 **Correct Commands**
PowerShell / CMD / Git Bash / WSL versions

---

## 🛠️ Quick Command Reference

### Format Code
**PowerShell:**
```powershell
.\scripts\format-code.ps1
```

**Git Bash:**
```bash
./.format-code.sh
```

### Run Tests
**PowerShell:**
```powershell
.\scripts\run-tests.ps1
```

**Git Bash:**
```bash
cd backend && PYTHONPATH=.. pytest tests/ -v
```

### Install Dependencies
**PowerShell:**
```powershell
python -m pip install -r requirements.txt; cd frontend; npm install
```

**Git Bash:**
```bash
python -m pip install -r requirements.txt && cd frontend && npm install
```

---

## 🔍 Current Project Status

### ✅ Fixed Issues
- All Python code formatted with Black
- All imports sorted with isort
- SQLAlchemy 2.x migration complete
- Test import paths fixed
- Dockerfiles corrected
- GitHub Actions workflows fixed
- NumPy version compatibility fixed
- PowerShell scripts created

### 📦 Project Structure
```
web/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── agent/            # AI agent service
├── orchestrator/     # Orchestration service
├── mobile-app/       # React Native app
├── ai_engine/        # AI/ML models
└── scripts/          # Utility scripts
```

---

## 🚨 Common Issues & Quick Fixes

### Issue: "&& is not a valid statement separator"
**PowerShell Fix:**
```powershell
# Wrong: cd backend && python test.py
# Right: cd backend; python test.py
```

### Issue: "ModuleNotFoundError: No module named 'ai_engine'"
**Fix:** PYTHONPATH is set in conftest.py and workflows

### Issue: "NumPy version conflict"
**Fix:** numpy==1.26.2 pinned in requirements.txt

---

## 📞 How to Get Help

When you encounter an error:
1. Share the error message
2. Share the command/code that caused it
3. I'll automatically:
   - Detect your shell
   - Fix the command/code
   - Explain the issue
   - Provide prevention tips

---

## ✅ Ready to Help!

I'm configured to:
- ✅ Understand your PowerShell environment
- ✅ Fix errors automatically
- ✅ Improve your code
- ✅ Prevent future issues
- ✅ Provide cross-platform solutions

**Just share any error or issue, and I'll fix it!** 🚀

