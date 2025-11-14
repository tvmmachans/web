#!/bin/bash
# Script to format code with Black
# Usage: ./format-code.sh

echo "Formatting code with Black..."
black backend/ agent/
echo "✅ Code formatting complete!"

