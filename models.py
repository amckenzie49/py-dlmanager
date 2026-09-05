from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import uuid4


class Download(BaseModel):
    """Schema for a download object"""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique download identifier"
    )
    url: Optional[str] = Field(
        default=None, description="URL to track the download from"
    )
    info_hash: Optional[str] = Field(
        default=None, description="Hash for the download (e.g., SHA256)"
    )
    magnet_link: Optional[str] = Field(
        default=None, description="Magnet link for torrent downloads"
    )
    filename: Optional[str] = Field(default=None, description="Target filename")
    status: str = Field(
        default="pending",
        description="Download status (pending, debridding, completed, failed)",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if status is failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When download was created"
    )
    file_url: Optional[str] = Field(
        default=None,
        description="File share URL for the downloaded file if it is completed",
    )


class DownloadCreate(BaseModel):
    """Schema for creating a download"""

    url: Optional[str] = Field(
        default=None, description="URL to track the download from"
    )
    info_hash: Optional[str] = Field(
        default=None, description="Hash for the download (e.g., SHA256)"
    )
    magnet_link: Optional[str] = Field(
        default=None, description="Magnet link for torrent downloads"
    )
