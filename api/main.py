"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

from config import settings
from routers import query, search, admin, translation

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
if settings.rate_limit_enabled:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(translation.router)  # Primary translation service
app.include_router(query.router)
app.include_router(search.router)
app.include_router(admin.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the test website"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>IYP Query API</h1><p>Test website not found. <a href='/docs'>View API Documentation</a></p>")

# API documentation endpoint
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "IYP Query API",
        "version": settings.api_version,
        "docs": "/docs",
        "test_ui": "/"
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )