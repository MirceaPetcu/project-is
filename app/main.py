"""
Main FastAPI Application
OSINT Intelligence Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Startup
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Working directory: {settings.WORKING_DIR}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    # OSINT Intelligence Platform
    
    Multi-Source Intelligence Analysis Platform with:
    
    ## Core Features
    - **Multi-source ingestion**: News, social media, public records, forums
    - **Entity resolution**: Resolve entities across sources
    - **Misinformation detection**: Cross-reference and detect contradictions
    - **Temporal analysis**: Event reconstruction and pattern detection
    
    ## Advanced Features
    - **Source credibility scoring**: Dynamic reliability weighting
    - **Narrative detection**: Identify coordinated information campaigns
    - **Gap analysis**: Find information voids
    - **Predictive alerts**: Detect emerging patterns
    - **Geographic clustering**: Spatial analysis of entity relations
    
    ## Technology
    - Built on LightRAG methodology for knowledge graph management
    - FastAPI for high-performance async API
    - Advanced NLP and ML for entity extraction and analysis
    """,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Multi-Source OSINT Intelligence Platform",
        "docs_url": "/docs",
        "api_base": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connectivity"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        reload_excludes=["volumes/*", "*.pyc", "__pycache__"]
    )
