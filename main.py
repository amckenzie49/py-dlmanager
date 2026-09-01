from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application startup")
    yield
    # Shutdown logic
    print("Application shutdown")


app = FastAPI(
    title="py-dlmanager",
    description="A barebones FastAPI application",
    version="0.1.0",
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
    return {"downloads": []}

@app.post("/downloads")
async def create_download(download: dict):
    """Create a new download"""
    return {"download": download}