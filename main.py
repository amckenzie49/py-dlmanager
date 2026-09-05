from fastapi import FastAPI
from storage import storage
from config import settings
from models import Download, DownloadCreate

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application for managing a list of downloads",
    version=settings.app_version,
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello, World!"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/downloads")
async def get_downloads():
    """Get all downloads"""
    downloads = storage.get_all_downloads()
    return {"downloads": list(downloads.values())}


@app.get("/downloads/{download_id}")
async def get_download(download_id: str):
    """Get a specific download by ID"""
    download = storage.get_download(download_id)
    if download is None:
        return {"error": "Download not found"}, 404
    return download


@app.post("/downloads")
async def create_download(download_data: DownloadCreate):
    """Create a new download"""
    # Convert to Download (auto-generates ID)
    download = Download(**download_data.model_dump())
    storage.set_download(download)
    return download


@app.delete("/downloads/{download_id}")
async def delete_download(download_id: str):
    """Delete a download by ID"""
    if storage.delete(download_id):
        return {"message": "Download deleted", "download_id": download_id}
    return {"error": "Download not found"}, 404
