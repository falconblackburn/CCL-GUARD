import os
import sys

# Add root to sys.path to allow imports from parent_app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from parent_app import app
