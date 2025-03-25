"""Root conftest file to set up the Python path for testing."""

import sys
from pathlib import Path

# Add the src directory to the Python path
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir / "src"))
