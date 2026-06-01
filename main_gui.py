import sys
import os
import glob

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_HERE, "backend")

# If PyQt6 is not already importable, search for the Poetry venv and add its
# site-packages so the app works when launched with the system Python directly.
try:
    import PyQt6
except ImportError:
    _cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "pypoetry", "Cache", "virtualenvs")
    for _sp in glob.glob(os.path.join(_cache, "eval-tool-*", "Lib", "site-packages")):
        if _sp not in sys.path:
            sys.path.insert(0, _sp)
            break

sys.path.insert(0, _BACKEND)

from database import create_tables
create_tables()

from gui.app import launch
launch()
