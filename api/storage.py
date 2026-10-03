import shelve
from pathlib import Path
from typing import Any, Dict, Optional
from api.config import settings
from api.models import Download


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
        with shelve.open(self.db_path) as db:
            return db.get(key)

    def set(self, key: str, value: Any):
        """Save or update a download"""
        with shelve.open(self.db_path) as db:
            db[key] = value
            db.sync()

    def delete(self, key: str) -> bool:
        """Delete a download by key"""
        with shelve.open(self.db_path) as db:
            if key not in db:
                return False
            del db[key]
            db.sync()
            return True

    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        with shelve.open(self.db_path) as db:
            return key in db

    def set_download(self, download: Download):
        """Save or update a download with validation"""
        # Store as dict for shelve compatibility, use _id as key
        with shelve.open(self.db_path) as db:
            db[download.id] = download.model_dump()
            db.sync()

    def get_download(self, download_id: str) -> Optional[Download]:
        """Get a download by ID and return as Download object"""
        with shelve.open(self.db_path) as db:
            data = db.get(download_id)
            if data is None:
                return None
            return Download(**data)

    def get_all_downloads(self) -> Dict[str, Download]:
        """Get all downloads as Download objects"""
        with shelve.open(self.db_path) as db:
            return {k: Download(**v) for k, v in db.items()}


# Global storage instance
storage = DownloadStorage()
