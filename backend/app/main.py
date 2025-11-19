"""
OriginStack - Open Origin JSON ERP System
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import actors, items, batches, events, processes, locations, operations, traceability
from app.db.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OriginStack",
    description="Open Origin JSON ERP for small producers - Levels 1, 2 & 3",
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

# Level 1 routers
app.include_router(actors.router)
app.include_router(items.router)
app.include_router(batches.router)
app.include_router(events.router)

# Level 2 routers
app.include_router(processes.router)
app.include_router(operations.router)
app.include_router(traceability.router)

# Level 3 routers
app.include_router(locations.router)


@app.get("/")
def root():
    return {
        "name": "OriginStack",
        "version": "0.2.0",
        "schema": "open-origin-json/0.5",
        "description": "Open Origin JSON ERP for small producers",
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
