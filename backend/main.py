"""
FastAPI Backend for PE Portfolio Companies V2
Modular API structure with organized endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import API routers
from backend.api.auth import router as auth_router
from backend.api.stats import router as stats_router
from backend.api.pe_firms import router as pe_firms_router
from backend.api.metadata import router as metadata_router
from backend.api.investments import router as investments_router
from backend.api.companies import router as companies_router
from backend.api.similar_companies import router as similar_companies_router

# Import security middleware
from backend.middleware import RateLimitMiddleware

# Initialize FastAPI
app = FastAPI(
    title="PE Portfolio API V2",
    description="REST API for Private Equity Portfolio Companies",
    version="2.0.0"
)

# Enable CORS for frontend access
# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://pe-intelligence.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Add rate limiting middleware for security
# Protects against brute force attacks and DoS
app.add_middleware(RateLimitMiddleware)


@app.on_event("startup")
async def validate_environment():
    """Validate required environment variables on startup"""
    required_vars = ["DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print("   The application may not function correctly without these variables.")
    else:
        print("✅ All required environment variables are set")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PE Portfolio API V2",
        "version": "2.0.0"
    }


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "PE Portfolio API V2",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include API routers
app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(pe_firms_router)
app.include_router(metadata_router)
app.include_router(investments_router)
app.include_router(companies_router)
app.include_router(similar_companies_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)