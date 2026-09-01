from fastapi import FastAPI
from contextlib import asynccontextmanager
from storage import storage
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application startup")
    storage.open()
    yield
    # Shutdown logic
    print("Application shutdown")
    storage.close()


app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application for managing a list of downloads",
    version=settings.app_version,
    lifespan=lifespan,
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
    downloads = storage.get_all()
    return {"downloads": downloads}


@app.get("/downloads/{download_id}")
async def get_download(download_id: str):
    """Get a specific download by ID"""
    download = storage.get(download_id)
    if download is None:
        return {"error": "Download not found"}, 404
    return {"download_id": download_id, "data": download}


@app.post("/downloads")
async def create_download(download: dict):
    """Create a new download"""
    # Assume 'id' is provided in the download dict
    download_id = download.get("id")
    if not download_id:
        return {"error": "Download must include 'id' field"}, 400

    storage.set(download_id, download)
    return {"download_id": download_id, "download": download}


@app.delete("/downloads/{download_id}")
async def delete_download(download_id: str):
    """Delete a download by ID"""
    if storage.delete(download_id):
        return {"message": "Download deleted", "download_id": download_id}
    return {"error": "Download not found"}, 404
