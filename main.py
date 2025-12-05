"""
KALASAG - Barangay Information System with Predictive Crime Analytics

Main entry point for the application.

Usage:
    python main.py

Author: KALASAG Development Team
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.main_app import run_application


def main():
    """Main entry point."""
    print("=" * 50)
    print("  KALASAG - Barangay Information System")
    print("  Starting application...")
    print("=" * 50)
    
    try:
        run_application()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
