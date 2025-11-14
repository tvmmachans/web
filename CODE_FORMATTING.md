# Code Formatting Guide

## Black Code Formatter

This project uses [Black](https://github.com/psf/black) for Python code formatting.

## Formatting All Code

To format all Python code in `backend/` and `agent/` directories:

```bash
# Install Black
pip install black

# Format all code
black backend/ agent/
```

Or use the provided script:

```bash
chmod +x .format-code.sh
./format-code.sh
```

## Check Formatting (Without Changing)

To check if code is formatted without making changes:

```bash
black --check backend/ agent/
```

## CI/CD Integration

The GitHub Actions workflow will:
- Check code formatting with Black
- Continue even if formatting fails (won't block deployment)
- You can format code locally and commit

## Configuration

Black configuration is in `pyproject.toml`:
- Line length: 88 characters
- Target Python version: 3.11

## Quick Fix

If CI fails due to formatting:

```bash
# Format code
black backend/ agent/

# Commit changes
git add backend/ agent/
git commit -m "Format code with Black"
git push
```

