#!/usr/bin/env python3
"""
Version Increment Script
Auto-increments version on git commit
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentsdr.utils.version import increment_version, get_version_info

def main():
    """Increment version and display info"""
    try:
        old_info = get_version_info()
        old_version = old_info["version"]

        new_version = increment_version()

        print(f"Version incremented: {old_version} -> {new_version}")
        print(f"Date: {get_version_info()['last_updated']}")
        print(f"Repository: {get_version_info()['repository']}")

        return 0
    except Exception as e:
        print(f"Error incrementing version: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
