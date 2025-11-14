"""
Pytest configuration file for backend tests.
Adds parent directory to Python path so imports work correctly.
"""
import sys
from pathlib import Path

# Add parent directory to Python path so we can import ai_engine, orchestrator, etc.
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

