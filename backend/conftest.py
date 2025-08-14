# Ensure 'app' package (backend/app) is importable when running tests from repo root.
import sys, os
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
