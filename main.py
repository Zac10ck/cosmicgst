#!/usr/bin/env python3
"""
GST Billing Software
A lightweight billing application for Kerala-based retail shops
with GST compliance and Google Drive backup.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point"""
    from ui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
