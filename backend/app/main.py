"""
VeriBatch - Open Origin JSON ERP System
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import actors, items, batches, events, processes, locations, operations, traceability, export, frontend, auth, compliance, search
from app.db.database import engine, Base
from app.services import search_service

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Search Index
search_service.setup_index()

app = FastAPI(
    title="VeriBatch",
    description="From the Berry Patch to VeriBatch. Simple, accessible compliance for small producers.",
    version="0.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (prefixed with /api)
app.include_router(actors.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(batches.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(processes.router, prefix="/api")
app.include_router(operations.router, prefix="/api")
app.include_router(traceability.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(search.router, prefix="/api")

# Auth routes (no prefix as they are specific endpoints like /login, /register)
app.include_router(auth.router)

# Frontend routes (no prefix - these are the default)
app.include_router(frontend.router)


@app.get("/api")
def api_info():
    return {
        "name": "VeriBatch API",
        "version": "0.2.0",
        "schema": "open-origin-json/0.5",
        "description": "From the Berry Patch to VeriBatch. Simple compliance for small producers.",
        "levels": {
            "1": "Minimal Traceability (Actors, Items, Batches)",
            "2": "Process & Event Tracking (Processes, Operations, Traceability)",
            "3": "Full Provenance (Locations, Advanced Features)"
        },
        "features": [
            "Actor, Item, Batch, Event management",
            "Process/Recipe tracking",
            "Production run operations",
            "Batch split/merge operations",
            "Disposal tracking",
            "Upstream/downstream traceability",
            "Location management with coordinates",
            "Full OOJ v0.5 compliance"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
