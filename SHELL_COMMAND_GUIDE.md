# 🔧 Shell Command Guide - Cross-Platform Compatibility

## 🎯 Your Current Setup

**Detected Shell:** PowerShell (Windows)  
**Path:** `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe`  
**Issue:** PowerShell doesn't support `&&` operator (bash syntax)

---

## ❌ Why The Error Happened

PowerShell uses different operators than bash:
- ❌ `&&` - NOT supported in PowerShell
- ❌ `||` - NOT supported in PowerShell  
- ✅ `;` - Works in PowerShell (sequential execution)
- ✅ `-and` / `-or` - PowerShell logical operators
- ✅ `if (condition) { }` - PowerShell conditional syntax

---

## ✅ Fixed Commands for Each Shell

### Example: Running multiple commands

**❌ This FAILS in PowerShell:**
```bash
cd backend && python -m pytest tests/
```

**✅ PowerShell (Windows):**
```powershell
cd backend; python -m pytest tests/
# OR use separate lines:
cd backend
python -m pytest tests/
# OR use -and operator:
cd backend -and python -m pytest tests/
```

**✅ CMD (Windows):**
```cmd
cd backend & python -m pytest tests/
REM For conditional execution:
cd backend && python -m pytest tests/
```

**✅ Git Bash / WSL / Linux:**
```bash
cd backend && python -m pytest tests/
```

---

### Example: Conditional execution

**❌ This FAILS in PowerShell:**
```bash
npm test || echo "Tests failed"
```

**✅ PowerShell:**
```powershell
npm test; if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" }
# OR:
try { npm test } catch { Write-Host "Tests failed" }
```

**✅ CMD:**
```cmd
npm test || echo Tests failed
```

**✅ Git Bash / WSL / Linux:**
```bash
npm test || echo "Tests failed"
```

---

### Example: Chaining with error handling

**❌ This FAILS in PowerShell:**
```bash
python -m black --check backend/ && python -m isort --check-only backend/
```

**✅ PowerShell:**
```powershell
python -m black --check backend/; if ($LASTEXITCODE -eq 0) { python -m isort --check-only backend/ }
# OR use separate lines:
python -m black --check backend/
if ($LASTEXITCODE -eq 0) {
    python -m isort --check-only backend/
}
```

**✅ CMD:**
```cmd
python -m black --check backend/ && python -m isort --check-only backend/
```

**✅ Git Bash / WSL / Linux:**
```bash
python -m black --check backend/ && python -m isort --check-only backend/
```

---

## 🛠️ Common Command Patterns

### 1. Install and Run
**PowerShell:**
```powershell
python -m pip install black; python -m black backend/
```

**Bash:**
```bash
python -m pip install black && python -m black backend/
```

### 2. Check and Format
**PowerShell:**
```powershell
python -m black --check backend/; if ($LASTEXITCODE -ne 0) { python -m black backend/ }
```

**Bash:**
```bash
python -m black --check backend/ || python -m black backend/
```

### 3. Change Directory and Run
**PowerShell:**
```powershell
cd frontend; npm install
```

**Bash:**
```bash
cd frontend && npm install
```

---

## 🔧 Permanent Prevention Steps

### Option 1: Use Git Bash as Default Terminal (Recommended)

**In VS Code:**
1. Open Settings (Ctrl+,)
2. Search for "terminal.integrated.defaultProfile.windows"
3. Set to: `"Git Bash"`

**Or edit settings.json:**
```json
{
  "terminal.integrated.defaultProfile.windows": "Git Bash",
  "terminal.integrated.profiles.windows": {
    "Git Bash": {
      "path": "C:\\Program Files\\Git\\bin\\bash.exe"
    }
  }
}
```

### Option 2: Upgrade to PowerShell 7+ (Supports &&)

**Check your PowerShell version:**
```powershell
$PSVersionTable.PSVersion
```

**If version < 7.0, install PowerShell 7:**
```powershell
# Using winget
winget install --id Microsoft.PowerShell --source winget

# Or download from: https://github.com/PowerShell/PowerShell/releases
```

**PowerShell 7+ supports:**
- `&&` operator ✅
- `||` operator ✅
- Better cross-platform compatibility

### Option 3: Use WSL (Windows Subsystem for Linux)

**Install WSL:**
```powershell
wsl --install
```

**Then use bash commands directly:**
```bash
cd backend && python -m pytest tests/
```

### Option 4: Create PowerShell Aliases

Add to your PowerShell profile (`$PROFILE`):
```powershell
# Edit profile
notepad $PROFILE

# Add these aliases:
function Run-IfSuccess {
    param($Command1, $Command2)
    & $Command1
    if ($LASTEXITCODE -eq 0) { & $Command2 }
}

Set-Alias -Name 'and' -Value Run-IfSuccess
```

---

## 📝 Quick Reference Table

| Operation | PowerShell | CMD | Bash/WSL |
|-----------|-----------|-----|----------|
| Sequential | `;` | `&` | `;` |
| Conditional (AND) | `if ($?) { }` | `&&` | `&&` |
| Conditional (OR) | `if (!$?) { }` | `\|\|` | `\|\|` |
| Pipe | `\|` | `\|` | `\|` |
| Background | `Start-Job` | `start` | `&` |
| Variable | `$var` | `%var%` | `$var` |

---

## 🚀 Recommended Solution for Your Project

**Best Option:** Use Git Bash for local development

1. **Install Git Bash** (if not installed):
   - Download from: https://git-scm.com/download/win
   - Or use: `winget install Git.Git`

2. **Set as default in VS Code:**
   - Ctrl+Shift+P → "Terminal: Select Default Profile"
   - Choose "Git Bash"

3. **All your bash commands will work:**
   ```bash
   cd backend && python -m pytest tests/
   python -m black --check backend/ && python -m isort --check-only backend/
   ```

---

## ✅ Validation Checklist

Before running commands, check:
- [ ] Are you in PowerShell? → Use `;` instead of `&&`
- [ ] Are you in Git Bash? → Use `&&` (bash syntax)
- [ ] Are you in CMD? → Use `&` or `&&`
- [ ] Are you in WSL? → Use `&&` (bash syntax)

---

## 🔍 Quick Detection Commands

**Check your shell:**
```powershell
# PowerShell
$PSVersionTable.PSVersion

# Bash
echo $SHELL

# CMD
echo %COMSPEC%
```

---

## 📚 Additional Resources

- [PowerShell Operators](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_operators)
- [Git Bash Documentation](https://git-scm.com/docs)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)

