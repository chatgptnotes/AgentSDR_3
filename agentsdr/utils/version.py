"""
Version Management Utility
InboxAI - Lindy AI-like Email Automation Platform
"""

import json
import os
from datetime import datetime
from pathlib import Path


class VersionManager:
    """Manages application version tracking and auto-increment"""

    def __init__(self):
        self.version_file = Path(__file__).parent.parent.parent / "version.json"

    def get_version_info(self) -> dict:
        """Get current version information"""
        if not self.version_file.exists():
            return {
                "version": "1.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "repository": "chatgptnotes/AgentSDR_3",
                "repository_url": "https://github.com/chatgptnotes/AgentSDR_3",
                "app_name": "InboxAI"
            }

        with open(self.version_file, 'r') as f:
            return json.load(f)

    def increment_version(self) -> str:
        """
        Increment version number (1.0 -> 1.1 -> 1.2 -> ... -> 1.9 -> 2.0)
        Returns the new version string
        """
        version_info = self.get_version_info()
        current = version_info["version"]

        # Parse version (e.g., "1.2" -> major=1, minor=2)
        parts = current.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0

        # Increment minor version
        minor += 1

        # If minor reaches 10, increment major and reset minor
        if minor >= 10:
            major += 1
            minor = 0

        new_version = f"{major}.{minor}"

        # Update version info
        version_info["version"] = new_version
        version_info["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        # Save to file
        with open(self.version_file, 'w') as f:
            json.dump(version_info, f, indent=2)

        return new_version

    def get_version(self) -> str:
        """Get current version string"""
        return self.get_version_info()["version"]

    def get_last_updated(self) -> str:
        """Get last update date"""
        return self.get_version_info()["last_updated"]

    def get_repository(self) -> str:
        """Get repository name"""
        return self.get_version_info()["repository"]

    def get_repository_url(self) -> str:
        """Get repository URL"""
        return self.get_version_info()["repository_url"]

    def get_app_name(self) -> str:
        """Get application name"""
        return self.get_version_info()["app_name"]


# Singleton instance
_version_manager = None


def get_version_manager() -> VersionManager:
    """Get singleton version manager instance"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


# Convenience functions
def get_version() -> str:
    """Get current version"""
    return get_version_manager().get_version()


def get_version_info() -> dict:
    """Get full version information"""
    return get_version_manager().get_version_info()


def increment_version() -> str:
    """Increment version and return new version"""
    return get_version_manager().increment_version()
