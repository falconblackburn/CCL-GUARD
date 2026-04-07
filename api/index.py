import os
import sys

# Add root to sys.path to allow imports from app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import app
