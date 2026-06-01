import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import create_tables
create_tables()

from gui.app import launch
launch()
