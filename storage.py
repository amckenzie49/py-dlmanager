import shelve
from pathlib import Path
from typing import Any, Dict, Optional
from config import settings


class DownloadStorage:
    """Manages persistent key-value storage for downloads using shelve"""

    def __init__(self, db_path: str = None):
        """Initialize storage with a path to the shelve database"""
        if db_path is None:
            db_path = settings.shelve_db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.db = None

    def open(self):
        """Open the shelve database"""
        self.db = shelve.open(self.db_path)

    def close(self):
        """Close the shelve database"""
        if self.db:
            self.db.close()

    def get_all(self) -> Dict[str, Any]:
        """Get all downloads"""
        if not self.db:
            return {}
        return dict(self.db)

    def get(self, key: str) -> Optional[Any]:
        """Get a download by key"""
        if not self.db:
            return None
        return self.db.get(key)

    def set(self, key: str, value: Any):
        """Save or update a download"""
        if not self.db:
            raise RuntimeError("Database not initialized. Call open() first.")
        self.db[key] = value
        self.db.sync()  # Ensure data is written to disk

    def delete(self, key: str) -> bool:
        """Delete a download by key"""
        if not self.db:
            return False
        if key in self.db:
            del self.db[key]
            self.db.sync()
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        if not self.db:
            return False
        return key in self.db


# Global storage instance
storage = DownloadStorage()
