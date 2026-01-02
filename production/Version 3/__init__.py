"""PROVES Library Curator Agent - Version 3

This version includes:
- Lineage verification refactor (validator verifies, storage receives results)
- Epistemic defaults + overrides pattern
"""
import sys
import os
from pathlib import Path

# Add neon-database scripts to path for graph_manager and other utilities
# This must happen before any subagents are imported
version3_folder = Path(__file__).parent
project_root = version3_folder.parent.parent
neon_db_path = project_root / 'neon-database' / 'scripts'

if str(neon_db_path) not in sys.path:
    sys.path.insert(0, str(neon_db_path))

# Add production/core for graph_manager
core_path = project_root / 'production' / 'core'
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))
