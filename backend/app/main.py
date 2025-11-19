"""
OriginStack - Open Origin JSON ERP System
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import actors, items, batches, events
from app.db.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OriginStack",
    description="Open Origin JSON ERP for small producers",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(actors.router)
app.include_router(items.router)
app.include_router(batches.router)
app.include_router(events.router)


@app.get("/")
def root():
    return {
        "name": "OriginStack",
        "version": "0.1.0",
        "schema": "open-origin-json/0.5",
        "description": "Open Origin JSON ERP for small producers"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
