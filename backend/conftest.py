"""Root conftest.py – ensures backend/ is on sys.path for all pytest sessions.

Pytest discovers this file first (it's at the rootdir), adds the backend
directory to sys.path, then finds tests/conftest.py which registers all
third-party stubs. This means `pytest` works correctly whether invoked:
  - from inside backend/           →  pytest
  - from inside stockIntel-main/   →  pytest backend/tests/
  - from the repo root             →  pytest backend/tests/
"""
import os
import sys

# Add backend/ to sys.path so `from app.xxx import yyy` always resolves
_backend_dir = os.path.dirname(__file__)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
