#!/bin/bash
# Script to format code with Black and isort
# Usage: ./format-code.sh

set -e

echo "Formatting code with Black and isort..."

# Format with Black
echo "Running Black..."
black backend/ agent/

# Sort imports with isort
echo "Running isort..."
isort backend/ agent/

# Run Black again to ensure compatibility
echo "Running Black again for compatibility..."
black backend/ agent/

echo "✅ Code formatting complete!"

