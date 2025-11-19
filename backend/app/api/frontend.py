"""
Frontend routes - HTMX-powered UI
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from app.db.database import get_db
from app.models import database as db_models
from app.services import traceability_service
from app.schemas import ooj_schemas

router = APIRouter(tags=["frontend"])

# Get absolute path to templates directory
# Go up from backend/app/api to OriginStack root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard"""
    # Get all actors
    actors = db.query(db_models.Actor).all()
    
    stats = {}
    if actors:
        actor = actors[0]  # Default to first actor for now
        stats = {
            "actor": actor.jsonb_doc,
            "items_count": db.query(db_models.Item).filter(db_models.Item.actor_id == actor.id).count(),
            "batches_count": db.query(db_models.Batch).filter(db_models.Batch.actor_id == actor.id).count(),
            "active_batches": db.query(db_models.Batch).filter(
                db_models.Batch.actor_id == actor.id,
                db_models.Batch.status == "active"
            ).count(),
            "events_count": db.query(db_models.Event).filter(db_models.Event.actor_id == actor.id).count(),
            "processes_count": db.query(db_models.Process).filter(db_models.Process.actor_id == actor.id).count(),
            "locations_count": db.query(db_models.Location).filter(db_models.Location.actor_id == actor.id).count(),
        }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "actors": [a.jsonb_doc for a in actors],
        "stats": stats
    })


@router.get("/actors", response_class=HTMLResponse)
def list_actors_page(request: Request, db: Session = Depends(get_db)):
    """Actors list page"""
    actors = db.query(db_models.Actor).all()
    
    return templates.TemplateResponse("actors.html", {
        "request": request,
        "actors": [actor.jsonb_doc for actor in actors]
    })


@router.get("/actors/{actor_id}/items", response_class=HTMLResponse)
def list_items_page(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Items list page"""
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    return templates.TemplateResponse("items.html", {
        "request": request,
        "actor_id": actor_id,
        "items": [item.jsonb_doc for item in items]
    })


@router.get("/actors/{actor_id}/batches", response_class=HTMLResponse)
def list_batches_page(
    request: Request, 
    actor_id: str, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Batches list page"""
    query = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id
    )
    
    if status:
        query = query.filter(db_models.Batch.status == status)
    
    batches = query.order_by(db_models.Batch.production_date.desc()).all()
    
    return templates.TemplateResponse("batches.html", {
        "request": request,
        "actor_id": actor_id,
        "batches": [batch.jsonb_doc for batch in batches],
        "filter_status": status
    })


# --- BATCH CRUD (forms must come before detail routes) ---

@router.get("/actors/{actor_id}/batches/new", response_class=HTMLResponse)
def new_batch_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to create a new batch"""
    # Get items for dropdown
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    return templates.TemplateResponse("batch_form.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": None,
        "items": [item.jsonb_doc for item in items],
        "mode": "create"
    })


@router.get("/actors/{actor_id}/batches/{batch_id}", response_class=HTMLResponse)
def batch_detail_page(request: Request, actor_id: str, batch_id: str, db: Session = Depends(get_db)):
    """Batch detail page with traceability"""
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        return HTMLResponse("Batch not found", status_code=404)
    
    # Get traceability info
    trace = traceability_service.get_batch_traceability(db, actor_id, batch_id, direction="both")
    
    return templates.TemplateResponse("batch_detail.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": batch.jsonb_doc,
        "upstream": trace.get("upstream", []),
        "downstream": trace.get("downstream", []),
        "events": trace.get("events", [])
    })


# --- PROCESS CRUD (forms must come before detail routes) ---

@router.get("/actors/{actor_id}/processes/new", response_class=HTMLResponse)
def new_process_form(request: Request, actor_id: str):
    """Form to create a new process"""
    return templates.TemplateResponse("process_form.html", {
        "request": request,
        "actor_id": actor_id,
        "process": None,
        "mode": "create"
    })


@router.get("/actors/{actor_id}/processes", response_class=HTMLResponse)
def list_processes_page(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Processes list page"""
    processes = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id
    ).all()
    
    return templates.TemplateResponse("processes.html", {
        "request": request,
        "actor_id": actor_id,
        "processes": [process.jsonb_doc for process in processes]
    })


@router.get("/actors/{actor_id}/processes/{process_id}", response_class=HTMLResponse)
def process_detail_page(request: Request, actor_id: str, process_id: str, db: Session = Depends(get_db)):
    """Process detail page"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        return HTMLResponse("Process not found", status_code=404)
    
    # Get events using this process
    events = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id
    ).all()
    
    process_events = [
        e.jsonb_doc for e in events 
        if e.jsonb_doc.get("process_id") == process_id
    ]
    
    return templates.TemplateResponse("process_detail.html", {
        "request": request,
        "actor_id": actor_id,
        "process": process.jsonb_doc,
        "events": process_events
    })


@router.get("/actors/{actor_id}/locations", response_class=HTMLResponse)
def list_locations_page(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Locations list page"""
    locations = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id
    ).all()
    
    return templates.TemplateResponse("locations.html", {
        "request": request,
        "actor_id": actor_id,
        "locations": [location.jsonb_doc for location in locations]
    })


@router.get("/actors/{actor_id}/events", response_class=HTMLResponse)
def list_events_page(
    request: Request, 
    actor_id: str,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Events list page"""
    query = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id
    )
    
    if event_type:
        query = query.filter(db_models.Event.event_type == event_type)
    
    events = query.order_by(db_models.Event.timestamp.desc()).all()
    
    return templates.TemplateResponse("events.html", {
        "request": request,
        "actor_id": actor_id,
        "events": [event.jsonb_doc for event in events],
        "filter_type": event_type
    })


@router.get("/actors/{actor_id}/traceability", response_class=HTMLResponse)
def traceability_page(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Traceability explorer page"""
    # Get all batches for selection
    batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id
    ).order_by(db_models.Batch.production_date.desc()).limit(50).all()
    
    return templates.TemplateResponse("traceability.html", {
        "request": request,
        "actor_id": actor_id,
        "batches": [batch.jsonb_doc for batch in batches]
    })


@router.get("/actors/{actor_id}/traceability/batch/{batch_id}", response_class=HTMLResponse)
def traceability_graph_page(request: Request, actor_id: str, batch_id: str, db: Session = Depends(get_db)):
    """Traceability graph visualization"""
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        return HTMLResponse("Batch not found", status_code=404)
    
    # Get full graph
    graph = traceability_service.get_full_traceability_graph(db, actor_id, batch_id)
    
    return templates.TemplateResponse("traceability_graph.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": batch.jsonb_doc,
        "graph": graph
    })


# ============================================================================
# CRUD Operations (Create, Update, Delete)
# ============================================================================

# --- ACTOR CRUD ---

@router.get("/actors/new", response_class=HTMLResponse)
def new_actor_form(request: Request):
    """Form to create a new actor"""
    return templates.TemplateResponse("actor_form.html", {
        "request": request,
        "actor": None,
        "mode": "create"
    })


@router.post("/actors/create")
async def create_actor(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new actor"""
    form_data = await request.form()
    
    actor_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "id": form_data.get("id"),
        "name": form_data.get("name"),
        "kind": form_data.get("kind", "producer"),
        "contacts": {}
    }
    
    if form_data.get("email"):
        actor_data["contacts"]["email"] = form_data.get("email")
    if form_data.get("phone"):
        actor_data["contacts"]["phone"] = form_data.get("phone")
    if form_data.get("website"):
        actor_data["contacts"]["website"] = form_data.get("website")
    
    # Add address if provided
    if form_data.get("street") or form_data.get("city"):
        actor_data["address"] = {}
        if form_data.get("street"):
            actor_data["address"]["street"] = form_data.get("street")
        if form_data.get("city"):
            actor_data["address"]["city"] = form_data.get("city")
        if form_data.get("region"):
            actor_data["address"]["region"] = form_data.get("region")
        if form_data.get("postal_code"):
            actor_data["address"]["postal_code"] = form_data.get("postal_code")
        if form_data.get("country"):
            actor_data["address"]["country"] = form_data.get("country")
    
    # Add OOJ required fields
    now = datetime.utcnow().isoformat() + "Z"
    actor_data["type"] = "actor"
    actor_data["created_at"] = now
    actor_data["updated_at"] = now

    # Save to database
    db_actor = db_models.Actor(
        id=actor_data["id"],
        name=actor_data["name"],
        kind=actor_data.get("kind"),
        jsonb_doc=actor_data
    )
    db.add(db_actor)
    db.commit()
    
    return RedirectResponse(url="/actors", status_code=303)


@router.get("/actors/{actor_id}/edit", response_class=HTMLResponse)
def edit_actor_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to edit an actor"""
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    
    if not actor:
        return HTMLResponse("Actor not found", status_code=404)
    
    return templates.TemplateResponse("actor_form.html", {
        "request": request,
        "actor": actor.jsonb_doc,
        "mode": "edit"
    })


@router.post("/actors/{actor_id}/update")
async def update_actor(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Update an existing actor"""
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    form_data = await request.form()
    
    actor_data = actor.jsonb_doc.copy()
    actor_data["name"] = form_data.get("name")
    actor_data["kind"] = form_data.get("kind", "producer")
    
    # Update contacts
    actor_data["contacts"] = {}
    if form_data.get("email"):
        actor_data["contacts"]["email"] = form_data.get("email")
    if form_data.get("phone"):
        actor_data["contacts"]["phone"] = form_data.get("phone")
    if form_data.get("website"):
        actor_data["contacts"]["website"] = form_data.get("website")
    
    # Update address
    if form_data.get("street") or form_data.get("city"):
        actor_data["address"] = {}
        if form_data.get("street"):
            actor_data["address"]["street"] = form_data.get("street")
        if form_data.get("city"):
            actor_data["address"]["city"] = form_data.get("city")
        if form_data.get("region"):
            actor_data["address"]["region"] = form_data.get("region")
        if form_data.get("postal_code"):
            actor_data["address"]["postal_code"] = form_data.get("postal_code")
        if form_data.get("country"):
            actor_data["address"]["country"] = form_data.get("country")
    
    actor.name = actor_data["name"]
    actor.jsonb_doc = actor_data
    db.commit()
    
    return RedirectResponse(url="/actors", status_code=303)


@router.post("/actors/{actor_id}/delete")
def delete_actor(actor_id: str, db: Session = Depends(get_db)):
    """Delete an actor"""
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    db.delete(actor)
    db.commit()
    
    return RedirectResponse(url="/actors", status_code=303)


# --- ITEM CRUD ---

@router.get("/actors/{actor_id}/items/new", response_class=HTMLResponse)
def new_item_form(request: Request, actor_id: str):
    """Form to create a new item"""
    return templates.TemplateResponse("item_form.html", {
        "request": request,
        "actor_id": actor_id,
        "item": None,
        "mode": "create"
    })


@router.post("/actors/{actor_id}/items/create")
async def create_item(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a new item"""
    form_data = await request.form()
    
    now = datetime.utcnow().isoformat() + "Z"
    item_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "type": "item",
        "id": form_data.get("id"),
        "actor_id": actor_id,
        "name": form_data.get("name"),
        "category": form_data.get("category", "raw_material"),
        "created_at": now,
        "updated_at": now
    }
    
    if form_data.get("unit"):
        item_data["unit"] = form_data.get("unit")
    if form_data.get("description"):
        item_data["description"] = form_data.get("description")
    if form_data.get("variety"):
        item_data["variety"] = form_data.get("variety")
    
    db_item = db_models.Item(
        id=item_data["id"],
        actor_id=actor_id,
        name=item_data["name"],
        category=item_data["category"],
        jsonb_doc=item_data
    )
    db.add(db_item)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/items", status_code=303)


@router.get("/actors/{actor_id}/items/{item_id}/edit", response_class=HTMLResponse)
def edit_item_form(request: Request, actor_id: str, item_id: str, db: Session = Depends(get_db)):
    """Form to edit an item"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor_id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        return HTMLResponse("Item not found", status_code=404)
    
    return templates.TemplateResponse("item_form.html", {
        "request": request,
        "actor_id": actor_id,
        "item": item.jsonb_doc,
        "mode": "edit"
    })


@router.post("/actors/{actor_id}/items/{item_id}/update")
async def update_item(
    request: Request,
    actor_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """Update an existing item"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor_id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    form_data = await request.form()
    
    item_data = item.jsonb_doc.copy()
    item_data["name"] = form_data.get("name")
    item_data["kind"] = form_data.get("kind", "ingredient")
    
    if form_data.get("description"):
        item_data["description"] = form_data.get("description")
    else:
        item_data.pop("description", None)
        
    if form_data.get("variety"):
        item_data["variety"] = form_data.get("variety")
    else:
        item_data.pop("variety", None)
    
    item.name = item_data["name"]
    item.jsonb_doc = item_data
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/items", status_code=303)


@router.post("/actors/{actor_id}/items/{item_id}/delete")
def delete_item(actor_id: str, item_id: str, db: Session = Depends(get_db)):
    """Delete an item"""
    item = db.query(db_models.Item).filter(
        db_models.Item.actor_id == actor_id,
        db_models.Item.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/items", status_code=303)


@router.post("/actors/{actor_id}/batches/create")
async def create_batch(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a new batch"""
    try:
        form_data = await request.form()
        
        now = datetime.utcnow().isoformat() + "Z"
        batch_data = {
            "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
            "type": "batch",
            "id": form_data.get("id"),
            "actor_id": actor_id,
            "item_id": form_data.get("item_id"),
            "production_date": form_data.get("production_date"),
            "status": form_data.get("status", "active"),
            "created_at": now,
            "updated_at": now
        }
        
        # Add quantity if provided
        if form_data.get("quantity_amount") and form_data.get("quantity_unit"):
            batch_data["quantity"] = {
                "amount": float(form_data.get("quantity_amount")),
                "unit": form_data.get("quantity_unit")
            }
        
        if form_data.get("expiration_date"):
            batch_data["expiration_date"] = form_data.get("expiration_date")
        if form_data.get("origin_kind"):
            batch_data["origin_kind"] = form_data.get("origin_kind")
        if form_data.get("notes"):
            batch_data["notes"] = form_data.get("notes")
        
        db_batch = db_models.Batch(
            id=batch_data["id"],
            actor_id=actor_id,
            item_id=batch_data["item_id"],
            production_date=batch_data["production_date"],
            expiration_date=batch_data.get("expiration_date"),
            status=batch_data["status"],
            jsonb_doc=batch_data
        )
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating batch: {str(e)}")


@router.post("/actors/{actor_id}/batches/{batch_id}/delete")
def delete_batch(actor_id: str, batch_id: str, db: Session = Depends(get_db)):
    """Delete a batch"""
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    db.delete(batch)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)


@router.post("/actors/{actor_id}/processes/create")
async def create_process(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a new process"""
    form_data = await request.form()
    
    now = datetime.utcnow().isoformat() + "Z"
    process_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "type": "process",
        "id": form_data.get("id"),
        "actor_id": actor_id,
        "name": form_data.get("name"),
        "kind": form_data.get("kind", "processing"),
        "created_at": now,
        "updated_at": now
    }
    
    if form_data.get("description"):
        process_data["description"] = form_data.get("description")
    if form_data.get("version"):
        process_data["version"] = form_data.get("version")
    
    # Handle steps (comma-separated or line-separated)
    steps_raw = form_data.get("steps", "")
    if steps_raw:
        steps = [s.strip() for s in steps_raw.replace("\n", ",").split(",") if s.strip()]
        if steps:
            process_data["steps"] = steps
    
    db_process = db_models.Process(
        id=process_data["id"],
        actor_id=actor_id,
        name=process_data["name"],
        kind=process_data["kind"],
        version=process_data.get("version"),
        jsonb_doc=process_data
    )
    db.add(db_process)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/processes", status_code=303)


@router.post("/actors/{actor_id}/processes/{process_id}/delete")
def delete_process(actor_id: str, process_id: str, db: Session = Depends(get_db)):
    """Delete a process"""
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    db.delete(process)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/processes", status_code=303)


# --- LOCATION CRUD ---

@router.get("/actors/{actor_id}/locations/new", response_class=HTMLResponse)
def new_location_form(request: Request, actor_id: str):
    """Form to create a new location"""
    return templates.TemplateResponse("location_form.html", {
        "request": request,
        "actor_id": actor_id,
        "location": None,
        "mode": "create"
    })


@router.post("/actors/{actor_id}/locations/create")
async def create_location(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a new location"""
    form_data = await request.form()
    
    now = datetime.utcnow().isoformat() + "Z"
    location_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "type": "location",
        "id": form_data.get("id"),
        "actor_id": actor_id,
        "name": form_data.get("name"),
        "kind": form_data.get("kind", "field"),
        "created_at": now,
        "updated_at": now
    }
    
    if form_data.get("description"):
        location_data["description"] = form_data.get("description")
    
    # Add address
    if form_data.get("street") or form_data.get("city"):
        location_data["address"] = {}
        if form_data.get("street"):
            location_data["address"]["street"] = form_data.get("street")
        if form_data.get("city"):
            location_data["address"]["city"] = form_data.get("city")
        if form_data.get("region"):
            location_data["address"]["region"] = form_data.get("region")
        if form_data.get("postal_code"):
            location_data["address"]["postal_code"] = form_data.get("postal_code")
        if form_data.get("country"):
            location_data["address"]["country"] = form_data.get("country")
    
    # Add coordinates
    if form_data.get("lat") and form_data.get("lon"):
        location_data["coordinates"] = {
            "lat": float(form_data.get("lat")),
            "lon": float(form_data.get("lon"))
        }
    
    db_location = db_models.Location(
        id=location_data["id"],
        actor_id=actor_id,
        name=location_data["name"],
        kind=location_data["kind"],
        jsonb_doc=location_data
    )
    db.add(db_location)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/locations", status_code=303)


@router.post("/actors/{actor_id}/locations/{location_id}/delete")
def delete_location(actor_id: str, location_id: str, db: Session = Depends(get_db)):
    """Delete a location"""
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/locations", status_code=303)


# --- EVENT CRUD ---

@router.get("/actors/{actor_id}/production-run/new", response_class=HTMLResponse)
def new_production_run_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to create a production run"""
    # Get available inputs and products for dropdowns
    available_batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.status == "active"
    ).all()
    
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    processes = db.query(db_models.Process).filter(db_models.Process.actor_id == actor_id).all()
    locations = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id).all()
    
    return templates.TemplateResponse("production_run_form.html", {
        "request": request,
        "actor_id": actor_id,
        "available_batches": [b.jsonb_doc for b in available_batches],
        "items": [i.jsonb_doc for i in items],
        "processes": [p.jsonb_doc for p in processes],
        "locations": [l.jsonb_doc for l in locations]
    })


@router.get("/actors/{actor_id}/split-batch/new", response_class=HTMLResponse)
def new_split_batch_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to split a batch"""
    # Get available batches to split
    available_batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.status == "active"
    ).all()
    
    locations = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id).all()
    
    return templates.TemplateResponse("split_batch_form.html", {
        "request": request,
        "actor_id": actor_id,
        "available_batches": [b.jsonb_doc for b in available_batches],
        "locations": [l.jsonb_doc for l in locations]
    })


@router.get("/actors/{actor_id}/merge-batch/new", response_class=HTMLResponse)
def new_merge_batch_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to merge batches"""
    # Get available batches to merge
    available_batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.status == "active"
    ).all()
    
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    locations = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id).all()
    
    return templates.TemplateResponse("merge_batch_form.html", {
        "request": request,
        "actor_id": actor_id,
        "available_batches": [b.jsonb_doc for b in available_batches],
        "items": [i.jsonb_doc for i in items],
        "locations": [l.jsonb_doc for l in locations]
    })


@router.get("/actors/{actor_id}/events/new", response_class=HTMLResponse)
def new_event_form(request: Request, actor_id: str, db: Session = Depends(get_db)):
    """Form to create a new event"""
    # Get batches and processes for dropdowns
    batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.status == "active"
    ).all()
    processes = db.query(db_models.Process).filter(db_models.Process.actor_id == actor_id).all()
    locations = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id).all()
    
    return templates.TemplateResponse("event_form.html", {
        "request": request,
        "actor_id": actor_id,
        "event": None,
        "batches": [b.jsonb_doc for b in batches],
        "processes": [p.jsonb_doc for p in processes],
        "locations": [l.jsonb_doc for l in locations],
        "mode": "create"
    })


@router.post("/actors/{actor_id}/events/create")
async def create_event(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a new event"""
    form_data = await request.form()
    
    now = datetime.utcnow().isoformat() + "Z"
    event_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "type": "event",
        "id": form_data.get("id"),
        "actor_id": actor_id,
        "event_type": form_data.get("event_type"),
        "timestamp": form_data.get("timestamp") or now,
        "created_at": now,
        "updated_at": now
    }
    
    if form_data.get("performed_by"):
        event_data["performed_by"] = form_data.get("performed_by")
    if form_data.get("process_id"):
        event_data["process_id"] = form_data.get("process_id")
    if form_data.get("location_id"):
        event_data["location_id"] = form_data.get("location_id")
    if form_data.get("notes"):
        event_data["notes"] = form_data.get("notes")
    
    # Handle inputs and outputs (simplified - batch IDs only)
    inputs_raw = form_data.get("inputs", "")
    if inputs_raw:
        input_ids = [i.strip() for i in inputs_raw.split(",") if i.strip()]
        event_data["inputs"] = [{"batch_id": bid} for bid in input_ids]
    
    outputs_raw = form_data.get("outputs", "")
    if outputs_raw:
        output_ids = [o.strip() for o in outputs_raw.split(",") if o.strip()]
        event_data["outputs"] = [{"batch_id": bid} for bid in output_ids]
    
    db_event = db_models.Event(
        id=event_data["id"],
        actor_id=actor_id,
        event_type=event_data["event_type"],
        timestamp=event_data["timestamp"],
        jsonb_doc=event_data
    )
    db.add(db_event)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/events", status_code=303)


@router.post("/actors/{actor_id}/production-run/create")
async def create_production_run(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Create a production run via form submission"""
    try:
        form_data = await request.form()
        
        # Parse inputs
        inputs = []
        i = 0
        while f"inputs[{i}][batch_id]" in form_data:
            if form_data.get(f"inputs[{i}][batch_id]"):
                inputs.append({
                    "batch_id": form_data.get(f"inputs[{i}][batch_id]"),
                    "amount": {
                        "amount": float(form_data.get(f"inputs[{i}][amount][amount]", 0)),
                        "unit": form_data.get(f"inputs[{i}][amount][unit]")
                    }
                })
            i += 1
        
        # Parse outputs
        outputs = []
        i = 0
        while f"outputs[{i}][batch_id]" in form_data:
            if form_data.get(f"outputs[{i}][batch_id]"):
                outputs.append({
                    "batch_id": form_data.get(f"outputs[{i}][batch_id]"),
                    "item_id": form_data.get(f"outputs[{i}][item_id]"),
                    "amount": {
                        "amount": float(form_data.get(f"outputs[{i}][amount][amount]", 0)),
                        "unit": form_data.get(f"outputs[{i}][amount][unit]")
                    }
                })
            i += 1
        
        # Call the event service directly
        from app.services import event_service
        from app.services.validation import ValidationError
        
        event = event_service.record_processing_event(
            db=db,
            event_id=form_data.get("event_id"),
            actor_id=actor_id,
            process_id=form_data.get("process_id") if form_data.get("process_id") else None,
            inputs=inputs,
            outputs=outputs,
            location_id=form_data.get("location_id") if form_data.get("location_id") else None,
            packaging_materials=None,  # Not handled in form yet
            performed_by=form_data.get("performed_by") if form_data.get("performed_by") else None,
            notes=form_data.get("notes") if form_data.get("notes") else None,
            timestamp=None  # Use current time
        )
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating production run: {str(e)}")


@router.post("/actors/{actor_id}/split-batch/create")
async def create_split_batch(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Split a batch via form submission"""
    try:
        form_data = await request.form()
        
        # Parse outputs
        outputs = []
        i = 0
        while f"outputs[{i}][batch_id]" in form_data:
            if form_data.get(f"outputs[{i}][batch_id]"):
                outputs.append({
                    "batch_id": form_data.get(f"outputs[{i}][batch_id]"),
                    "amount": {
                        "amount": float(form_data.get(f"outputs[{i}][amount][amount]", 0)),
                        "unit": form_data.get(f"outputs[{i}][amount][unit]")
                    }
                })
            i += 1
        
        # Call the event service directly
        from app.services import event_service
        from app.services.validation import ValidationError
        
        event = event_service.split_batch(
            db=db,
            event_id=form_data.get("event_id"),
            actor_id=actor_id,
            source_batch_id=form_data.get("source_batch_id"),
            output_batches=outputs,
            location_id=form_data.get("location_id") if form_data.get("location_id") else None,
            notes=form_data.get("notes") if form_data.get("notes") else None,
            timestamp=None  # Use current time
        )
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error splitting batch: {str(e)}")


@router.post("/actors/{actor_id}/merge-batch/create")
async def create_merge_batch(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db)
):
    """Merge batches via form submission"""
    try:
        form_data = await request.form()
        
        # Parse source batch IDs (entire batches only)
        source_batch_ids = []
        i = 0
        while f"inputs[{i}][batch_id]" in form_data:
            batch_id = form_data.get(f"inputs[{i}][batch_id]")
            if batch_id:
                source_batch_ids.append(batch_id)
            i += 1
        
        # Calculate total quantity from source batches
        total_amount = 0
        unit = None
        
        for batch_id in source_batch_ids:
            batch = db.query(db_models.Batch).filter(
                db_models.Batch.actor_id == actor_id,
                db_models.Batch.id == batch_id
            ).first()
            if batch and batch.jsonb_doc.get("quantity"):
                qty = batch.jsonb_doc["quantity"]
                total_amount += qty.get("amount", 0)
                if not unit:
                    unit = qty.get("unit", "unit")
        
        output_quantity = {
            "amount": total_amount,
            "unit": unit or "unit"
        }
        
        # Call the event service directly
        from app.services import event_service
        from app.services.validation import ValidationError
        
        event = event_service.merge_batches(
            db=db,
            event_id=form_data.get("event_id"),
            actor_id=actor_id,
            source_batch_ids=source_batch_ids,
            output_batch_id=form_data.get("output_batch_id"),
            output_quantity=output_quantity,
            location_id=form_data.get("location_id") if form_data.get("location_id") else None,
            notes=form_data.get("notes") if form_data.get("notes") else None,
            timestamp=None  # Use current time
        )
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error merging batches: {str(e)}")


@router.post("/actors/{actor_id}/events/{event_id}/delete")
def delete_event(actor_id: str, event_id: str, db: Session = Depends(get_db)):
    """Delete an event"""
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/events", status_code=303)
