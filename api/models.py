from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4


DownloadStatus = Literal[
    "pending", "debridding", "ready", "transferring", "completed", "failed"
]


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
    status: DownloadStatus = Field(
        default="pending",
        description="Current debrid and transfer state",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if status is failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When download was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="When the download state last changed"
    )
    progress: float = Field(default=0, ge=0, le=100)
    provider_id: Optional[str] = None
    provider_type: Optional[Literal["torrent", "webdl"]] = None
    destination_path: Optional[str] = None
    transferred_files: list[str] = Field(default_factory=list)
    file_url: Optional[str] = Field(
        default=None,
        description="WebDAV URL for the transferred file when completed",
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
