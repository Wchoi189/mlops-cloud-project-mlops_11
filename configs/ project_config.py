"""Project-wide path configuration"""

from pathlib import Path


# Automatically find project root (looks for .git, pyproject.toml, etc.)
def find_project_root(start_dir=None):
    start_dir = Path(start_dir or Path.cwd())

    # Common project root indicators
    root_indicators = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "docker-compose.yml",
    ]

    current = start_dir
    while current != current.parent:  # Stop at filesystem root
        for indicator in root_indicators:
            if (current / indicator).exists():
                return current
        current = current.parent

    # Fallback if no indicators found
    return start_dir


# Project paths
PROJECT_ROOT = find_project_root()
DOCKER_DIR = PROJECT_ROOT / "docker"
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
SRC_DIR = PROJECT_ROOT / "src"

# Ensure critical directories exist
for directory in [MODELS_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Add project root to Python path if needed
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
