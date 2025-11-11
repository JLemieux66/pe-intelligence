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
from backend.api.ml_predictions import router as ml_predictions_router

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
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://pe-intelligence.vercel.app"
)

# Parse allowed origins, stripping whitespace
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# Determine if we're in production or development
is_production = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL"))

# In development, add localhost and 127.0.0.1 variants
if not is_production:
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ])

# Always ensure Vercel frontend is allowed (in case env detection fails)
if "https://pe-intelligence.vercel.app" not in allowed_origins:
    allowed_origins.append("https://pe-intelligence.vercel.app")

# Remove duplicates while preserving order
allowed_origins = list(dict.fromkeys(allowed_origins))

# Allow origin regex for development environments (all-hands.dev)
allow_origin_regex = None
if not is_production:
    allow_origin_regex = r"https://.*\.all-hands\.dev"

print(f"🌐 CORS enabled for origins: {allowed_origins}")
print(f"🌐 Production mode: {is_production}")
if allow_origin_regex:
    print(f"🌐 CORS regex pattern: {allow_origin_regex}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,
)

# Add rate limiting middleware for security (disabled in development)
# Protects against brute force attacks and DoS
if is_production:
    app.add_middleware(RateLimitMiddleware)
    print("🔒 Rate limiting enabled (production mode)")
else:
    print("⚠️  Rate limiting disabled (development mode)")


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


@app.on_event("startup")
async def enrich_companies_on_startup():
    """
    Optionally enrich companies with ML predictions on startup
    Set ML_ENRICH_ON_STARTUP=true in environment to enable
    """
    if os.getenv("ML_ENRICH_ON_STARTUP", "false").lower() == "true":
        print("🤖 ML enrichment enabled - enriching companies with revenue predictions...")
        try:
            from backend.database_pool import SessionLocal
            from backend.services.ml_enrichment_service import MLEnrichmentService

            db = SessionLocal()
            try:
                enrichment_service = MLEnrichmentService()
                count = enrichment_service.enrich_all_companies(db, force_update=False, batch_size=50)
                print(f"✅ Successfully enriched {count} companies with ML predictions")
            finally:
                db.close()
        except Exception as e:
            print(f"⚠️  ML enrichment failed: {e}")
            print("   Application will continue without ML enrichment")
    else:
        print("ℹ️  ML enrichment on startup is disabled (set ML_ENRICH_ON_STARTUP=true to enable)")


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
app.include_router(ml_predictions_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)