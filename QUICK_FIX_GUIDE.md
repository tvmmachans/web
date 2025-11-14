# ⚡ Quick Fix Guide - Common Errors & Solutions

## 🔥 Most Common Errors

### Error 1: "The token '&&' is not a valid statement separator"

**💡 Why the Error Happens:**
PowerShell 5.1 doesn't support bash's `&&` operator. It's a bash-specific feature.

**✔ Corrected Solution:**

**PowerShell:**
```powershell
cd backend; python -m pytest tests/
```

**Git Bash/WSL:**
```bash
cd backend && python -m pytest tests/
```

**🔧 Steps to Fix:**
1. Replace `&&` with `;` in PowerShell
2. Or use separate lines
3. Or upgrade to PowerShell 7+

**🔒 Prevention Tips:**
- Use provided PowerShell scripts (`.ps1` files)
- Or switch to Git Bash for development
- Or upgrade to PowerShell 7+

---

### Error 2: "ModuleNotFoundError: No module named 'ai_engine'"

**💡 Why the Error Happens:**
Python can't find the `ai_engine` module because it's in the parent directory, not in `sys.path`.

**✔ Corrected Solution:**
- ✅ Fixed in `backend/tests/conftest.py` - automatically adds root to path
- ✅ Fixed in GitHub Actions - PYTHONPATH set to workspace root

**🔧 Steps to Fix:**
```powershell
# Set PYTHONPATH before running tests
$env:PYTHONPATH = ".."
python -m pytest tests/
```

**🔒 Prevention Tips:**
- Always use `conftest.py` (already fixed)
- Or set PYTHONPATH in workflows (already fixed)

---

### Error 3: "NumPy version conflict"

**💡 Why the Error Happens:**
NumPy 2.x is incompatible with torch 2.1.0 (compiled with NumPy 1.x).

**✔ Corrected Solution:**
- ✅ Fixed: `numpy==1.26.2` pinned in requirements.txt

**🔧 Steps to Fix:**
```powershell
pip install numpy==1.26.2
```

**🔒 Prevention Tips:**
- Always pin NumPy version when using torch
- Check torch compatibility before upgrading NumPy

---

### Error 4: "ImportError: No module named 'transformers'"

**💡 Why the Error Happens:**
Missing dependency in requirements.txt.

**✔ Corrected Solution:**
- ✅ Fixed: Added `transformers==4.35.0` and `torch==2.1.0` to requirements.txt

**🔧 Steps to Fix:**
```powershell
pip install transformers torch
```

**🔒 Prevention Tips:**
- Always add new dependencies to requirements.txt
- Run `pip freeze > requirements.txt` after installing

---

### Error 5: "SQLAlchemy query syntax error"

**💡 Why the Error Happens:**
Using SQLAlchemy 1.x syntax with SQLAlchemy 2.x installed.

**✔ Corrected Solution:**
- ✅ Fixed: All queries migrated to SQLAlchemy 2.x syntax

**Before (1.x):**
```python
user = session.query(User).filter(User.username == username).first()
```

**After (2.x):**
```python
result = session.execute(select(User).where(User.username == username))
user = result.scalar_one_or_none()
```

**🔒 Prevention Tips:**
- Always use SQLAlchemy 2.x syntax
- Use `select()` instead of `query()`
- Use `.where()` instead of `.filter()`

---

## 🛠️ Command Conversion Table

| Operation | PowerShell 5.1 | PowerShell 7+ | Git Bash | CMD |
|-----------|---------------|---------------|----------|-----|
| Sequential | `;` | `;` or `&&` | `;` | `&` |
| Conditional AND | `if ($?) { }` | `&&` | `&&` | `&&` |
| Conditional OR | `if (!$?) { }` | `\|\|` | `\|\|` | `\|\|` |
| Change dir + run | `cd dir; cmd` | `cd dir && cmd` | `cd dir && cmd` | `cd dir & cmd` |
| Check + run | `if (Test-Path file) { cmd }` | `[ -f file ] && cmd` | `[ -f file ] && cmd` | `if exist file cmd` |

---

## 🚀 Quick Commands

### Format Code
```powershell
.\scripts\format-code.ps1
```

### Run Tests
```powershell
.\scripts\run-tests.ps1
```

### Install Dependencies
```powershell
python -m pip install -r requirements.txt; cd frontend; npm install
```

### Check Environment
```powershell
python --version; node --version; git --version; docker --version
```

---

## 📞 Need Help?

Just share any error message, and I'll:
1. ✅ Detect your shell automatically
2. ✅ Fix the command/code
3. ✅ Explain why it failed
4. ✅ Provide prevention tips
5. ✅ Show all shell versions

**I'm ready to help!** 🚀

