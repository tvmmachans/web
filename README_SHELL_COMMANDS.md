# 🚀 Quick Command Reference

## For PowerShell Users (Windows)

### Format Code
```powershell
.\scripts\format-code.ps1
```

### Run Tests
```powershell
.\scripts\run-tests.ps1
.\scripts\run-tests.ps1 -Coverage
```

### Initialize Local Environment
```powershell
.\scripts\init_local.ps1
```

### Install Dependencies
```powershell
python -m pip install -r requirements.txt
cd frontend; npm install
```

---

## For Git Bash / WSL / Linux Users

### Format Code
```bash
chmod +x .format-code.sh
./.format-code.sh
```

### Run Tests
```bash
cd backend && PYTHONPATH=.. pytest tests/ -v
```

### Initialize Local Environment
```bash
chmod +x scripts/init_local.sh
./scripts/init_local.sh
```

---

## ⚠️ Important Notes

- **PowerShell**: Use `;` instead of `&&`
- **Git Bash/WSL**: Use `&&` (bash syntax)
- **GitHub Actions**: Always uses bash (Linux runners)

