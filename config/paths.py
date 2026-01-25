# config/paths.py
import os
from pathlib import Path

# Get the directory containing this config file
CONFIG_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CONFIG_DIR.parent

# Browser assets (read-only)
BROWSER_CSS_PATH = PROJECT_ROOT / "browser.css"

# User data directory
if os.name == 'nt':  # Windows
    USER_DATA_DIR = Path(os.environ.get('APPDATA', Path.home())) / 'WebBrowser'
elif os.name == 'posix':  # Linux/Mac
    USER_DATA_DIR = Path.home() / '.webbrowser'
else:
    USER_DATA_DIR = Path.home() / '.webbrowser'

# Create user data directory if it doesn't exist
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# User data files
BOOKMARKS_PATH = USER_DATA_DIR / "bookmarks.txt"

def get_user_data_path(filename):
    """Get path for user data files."""
    return USER_DATA_DIR / filename