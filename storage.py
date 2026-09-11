import shelve
from pathlib import Path
from typing import Any, Dict, Optional
from config import settings
from models import Download


class DownloadStorage:
    """Manages persistent key-value storage for downloads using shelve"""

    def __init__(self, db_path: str = None):
        """Initialize storage with a path to the shelve database"""
        if db_path is None:
            db_path = settings.shelve_db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

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

    def set_download(self, download: Download):
        """Save or update a download with validation"""
        # Store as dict for shelve compatibility, use _id as key
        with shelve.open(self.db_path) as db:
            db[download.id] = download.model_dump()
            db.sync()

    def get_download(self, download_id: str) -> Optional[Download]:
        """Get a download by ID and return as Download object"""
        if not self.db:
            return None
        data = self.db.get(download_id)
        if data is None:
            return None
        return Download(**data)

    def get_all_downloads(self) -> Dict[str, Download]:
        """Get all downloads as Download objects"""
        with shelve.open(self.db_path) as db:
            return {k: Download(**v) for k, v in db.items()}


# Global storage instance
storage = DownloadStorage()
