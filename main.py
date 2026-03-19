import os
import logging

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import API routers
from app.api.v1 import brand_kits, campaigns, posts, social_accounts, payments, users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Scale66 API",
    version="2.0.0",
    description="AI-powered carousel content generation platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    logger.error(f"ValueError: {str(exc)} - {request.method} {request.url}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)} - {request.method} {request.url}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Root endpoints

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Scale66 API",
        "version": "2.0.0",
        "description": "AI-powered carousel content generation platform",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register API v1 routers

app.include_router(
    brand_kits.router,
    prefix="/api/v1",
    tags=["Brand Kits"]
)

app.include_router(
    campaigns.router,
    prefix="/api/v1",
    tags=["Campaigns"]
)

app.include_router(
    posts.router,
    prefix="/api/v1",
    tags=["Posts"]
)

app.include_router(
    social_accounts.router,
    prefix="/api/v1",
    tags=["Social Accounts"]
)

app.include_router(
    payments.router,
    prefix="/api/v1",
    tags=["Payments"]
)

app.include_router(
    users.router,
    prefix="/api/v1",
    tags=["Users"]
)

logger.info("Scale66 API initialized with all routes")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
