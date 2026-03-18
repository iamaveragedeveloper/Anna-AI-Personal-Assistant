#!/usr/bin/env python3
"""
Anna — GUI Mode

Launches Anna with web-based graphical interface.

Usage:
    cd anna
    python main_gui.py

Then open: http://localhost:8080
"""

import os
import sys

# Add project root so imports resolve correctly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.server import run_server

if __name__ == "__main__":
    run_server()
