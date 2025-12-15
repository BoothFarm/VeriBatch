"""
Frontend routes - HTMX-powered UI
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import jinja2

from app.db.database import get_db
from app.models import database as db_models
from app.services import traceability_service, batch_service, process_service, location_service, event_service, auth_service
from app.schemas import ooj_schemas
from app.core import security
from ooj_client import entities
from fastapi import Cookie
import logging

router = APIRouter(tags=["frontend"])

logger = logging.getLogger(__name__)

# Template setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

# --- Auth Dependency ---
def get_current_user_from_cookie(request: Request, access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        return None
    
    try:
        scheme, token = access_token.split()
        if scheme.lower() != 'bearer':
            return None
        payload = security.decode_access_token(token)
        if not payload:
            return None
    except (ValueError, AttributeError):
        return None
        
    email = payload.get("sub")
    if not email:
        return None
    
    return auth_service.get_user_by_email(db, email)

# --- Routes ---

@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: Optional[db_models.User] = Depends(get_current_user_from_cookie)):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, 
    actor_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Main dashboard (Protected)"""
    if not user:
        return RedirectResponse(url="/login")
        
    # Get user's actors (sub-accounts)
    actors = user.actors
    
    stats = {}
    current_actor = None
    
    if actors:
        if actor_id:
            # Verify user owns this actor
            current_actor = next((a for a in actors if a.id == actor_id), None)
            if not current_actor:
                # If requested actor not found/owned, default to first
                current_actor = actors[0]
        else:
            current_actor = actors[0]
            
        stats = {
            "actor": current_actor.jsonb_doc,
            "items_count": db.query(db_models.Item).filter(db_models.Item.actor_id == current_actor.id).count(),
            "batches_count": db.query(db_models.Batch).filter(db_models.Batch.actor_id == current_actor.id).count(),
            "active_batches": db.query(db_models.Batch).filter(
                db_models.Batch.actor_id == current_actor.id,
                db_models.Batch.status == "active"
            ).count(),
            "events_count": db.query(db_models.Event).filter(db_models.Event.actor_id == current_actor.id).count(),
            "processes_count": db.query(db_models.Process).filter(db_models.Process.actor_id == current_actor.id).count(),
            "locations_count": db.query(db_models.Location).filter(db_models.Location.actor_id == current_actor.id).count(),
        }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "actors": [a.jsonb_doc for a in actors],
        "stats": stats,
        "user": user,
        "current_actor_id": current_actor.id if current_actor else None
    })


@router.get("/actors", response_class=HTMLResponse)
def list_actors_page(
    request: Request, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Actors list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login")
        
    actors = user.actors
    
    return templates.TemplateResponse("actors.html", {
        "request": request,
        "actors": [actor.jsonb_doc for actor in actors],
        "user": user
    })


def get_actor_if_owned(actor_id: str, db: Session, user: db_models.User):
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id, db_models.Actor.owner_id == user.pk).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found or not owned by user")
    return actor

# All routes below this point (that deal with actor_id) should use get_actor_if_owned
# and have user: Depends(get_current_user_from_cookie) in their signature.


@router.get("/actors/{actor_id}/items", response_class=HTMLResponse)
def list_items_page(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Items list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user) # Ensure user owns the actor
    
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    return templates.TemplateResponse("items.html", {
        "request": request,
        "actor_id": actor_id,
        "items": [item.jsonb_doc for item in items],
        "user": user
    })


@router.get("/actors/{actor_id}/batches", response_class=HTMLResponse)
def list_batches_page(
    request: Request, 
    actor_id: str, 
    status: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Batches list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    limit = 20
    skip = (page - 1) * limit
    
    batches, total = batch_service.get_batches_by_actor(
        db, actor_id, status=status, skip=skip, limit=limit
    )
    
    total_pages = (total + limit - 1) // limit
    
    return templates.TemplateResponse("batches.html", {
        "request": request,
        "actor_id": actor_id,
        "batches": [batch.jsonb_doc for batch in batches],
        "filter_status": status,
        "page": page,
        "total_pages": total_pages,
        "total_items": total,
        "user": user
    })


# --- BATCH CRUD (forms must come before detail routes) ---

@router.get("/actors/{actor_id}/batches/new", response_class=HTMLResponse)
def new_batch_form(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new batch (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    # Get items for dropdown
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    return templates.TemplateResponse("batch_form.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": None,
        "items": [item.jsonb_doc for item in items],
        "mode": "create",
        "user": user
    })


@router.get("/actors/{actor_id}/batches/{batch_id}/edit", response_class=HTMLResponse)
def edit_batch_form(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit an existing batch (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    batch = batch_service.get_batch(db, actor_id, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    return templates.TemplateResponse("batch_form.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": batch.jsonb_doc,
        "items": [item.jsonb_doc for item in items],
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/batches/{batch_id}/update")
async def update_batch(
    request: Request,
    actor_id: str,
    batch_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing batch (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    update_data = {}
    
    if form_data.get("production_date"):
        update_data["production_date"] = form_data.get("production_date")
        
    if form_data.get("expiration_date"):
        update_data["expiration_date"] = form_data.get("expiration_date")
    else:
        update_data["expiration_date"] = None
        
    if form_data.get("quantity_amount") and form_data.get("quantity_unit"):
        update_data["quantity"] = {
            "amount": float(form_data.get("quantity_amount")),
            "unit": form_data.get("quantity_unit")
        }
        
    if form_data.get("origin_kind"):
        update_data["origin_kind"] = form_data.get("origin_kind")
    else:
        update_data["origin_kind"] = None
        
    if form_data.get("notes"):
        update_data["notes"] = form_data.get("notes")
    else:
        update_data["notes"] = None
        
    if form_data.get("lot_code"):
        update_data["lot_code"] = form_data.get("lot_code")
        
    if form_data.get("external_lot_code"):
        update_data["external_lot_code"] = form_data.get("external_lot_code")
        
    # Checkbox logic: if present = True, else False (usually). 
    # But for updates, we might only want to update if explicitly set? 
    # HTML forms don't send unchecked boxes. Let's assume if it's in form, set it.
    # Actually, standard pattern is checking for presence.
    update_data["is_mock_recall"] = form_data.get("is_mock_recall") == "true"

    batch = batch_service.update_batch_details(db, actor_id, batch_id, update_data)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)


@router.get("/actors/{actor_id}/batches/{batch_id}", response_class=HTMLResponse)
def batch_detail_page(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Batch detail page with traceability (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id,
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        return HTMLResponse("Batch not found", status_code=404)
    
    # Get traceability info
    trace = traceability_service.get_batch_traceability(db, actor_id, batch_id, direction="both")
    
    # Get all label templates for the actor
    label_templates = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id).all()

    return templates.TemplateResponse("batch_detail.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": batch.jsonb_doc,
        "upstream": trace.get("upstream", []),
        "downstream": trace.get("downstream", []),
        "events": trace.get("events", []),
        "label_templates": label_templates,
        "user": user
    })


@router.get("/actors/{actor_id}/batches/{batch_id}/recall-report", response_class=HTMLResponse)
def recall_report_page(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Generate and display a formal Recall Report (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    from app.services import compliance_service
    
    batch = db.query(db_models.Batch).filter_by(actor_id=actor_id, id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    report = compliance_service.generate_recall_report(db, actor_id, batch_id)
    
    return templates.TemplateResponse("recall_report.html", {
        "request": request,
        "actor_id": actor_id,
        "batch": batch.jsonb_doc,
        "report": report,
        "user": user
    })


@router.get("/verify/{actor_id}/{batch_id}", response_class=HTMLResponse)
def public_verify_page(request: Request, actor_id: str, batch_id: str, db: Session = Depends(get_db)):
    """Public verification page for a batch."""
    batch = db.query(db_models.Batch).filter(db_models.Batch.actor_id == actor_id, db_models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=44, detail="Batch not found")

    item = db.query(db_models.Item).filter(db_models.Item.id == batch.item_id).first()
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    trace = traceability_service.get_batch_traceability(db, actor_id, batch_id, "none")
    
    events_with_dt = []
    for event_data in trace.get("events", []):
        if isinstance(event_data.get("timestamp"), str):
            try:
                event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                # If parsing fails, keep the original string or set to None
                pass
        events_with_dt.append(event_data)

    # Try to find a location with coordinates from the events
    location = None
    for event in events_with_dt:
        if event.get("location_id"):
            loc = db.query(db_models.Location).filter(db_models.Location.id == event["location_id"]).first()
            if loc and loc.jsonb_doc and 'latitude' in loc.jsonb_doc and 'longitude' in loc.jsonb_doc:
                location = loc
                break

    return templates.TemplateResponse("public_verify.html", {
        "request": request,
        "batch": batch,
        "item": item,
        "actor": actor,
        "events": events_with_dt,
        "location": location
    })


@router.get("/actors/{actor_id}/batches/{batch_id}/print_label", response_class=HTMLResponse)
def print_label_page(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Generate a printable label for a batch (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    # 1. Get the Batch
    batch = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id, 
        db_models.Batch.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # 2. Get the Item (Product details)
    item = db.query(db_models.Item).filter(db_models.Item.id == batch.item_id).first()

    # 3. Get the Actor (Business details)
    actor = db.query(db_models.Actor).filter(db_models.Actor.id == actor_id).first()
    
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    # 4. Generate the Public URL for the QR Code
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/verify/{actor_id}/{batch_id}"

    return templates.TemplateResponse("print_label.html", {
        "request": request,
        "batch": batch,
        "item": item,
        "actor": actor,
        "public_url": public_url,
        "user": user
    })


@router.get("/actors/{actor_id}/batches/{batch_id}/print_label/pdf")
def print_label_pdf(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    template_id: Optional[str] = None, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Generate a downloadable PDF label for a batch, optionally using a custom template (Protected)."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    get_actor_if_owned(actor_id, db, user)
    
    from fpdf import FPDF
    import qrcode
    import io
    import urllib
    import barcode
    from barcode.writer import ImageWriter
    from jinja2 import Environment, FileSystemLoader

    # 1. Fetch Data
    batch = db.query(db_models.Batch).filter_by(actor_id=actor_id, id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    item = db.query(db_models.Item).filter_by(id=batch.item_id).first()
    actor = db.query(db_models.Actor).filter_by(id=actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/verify/{actor_id}/{batch_id}"

    # Data available to templates
    template_context = {
        "batch": batch.jsonb_doc,
        "item": item.jsonb_doc,
        "actor": actor.jsonb_doc,
        "public_url": public_url,
        "actor_id": actor_id, # For consistency, though part of actor.jsonb_doc
        "batch_id": batch_id  # For consistency, though part of batch.jsonb_doc
    }

    # Setup Jinja2 environment for inline template rendering
    env = Environment(loader=FileSystemLoader(str(BASE_DIR / "frontend" / "templates")))
    
    # 2. Initialize PDF
    if template_id:
        template = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id, id=template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Label Template not found")
        
        pdf_width = template.width_in
        pdf_height = template.height_in
        elements_to_render = template.jsonb_doc.get('elements', [])

        pdf = FPDF(orientation='P' if pdf_height > pdf_width else 'L', unit='in', format=(pdf_height, pdf_width))
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)

        # Iterate and render elements from template
        for element in elements_to_render:
            elem_type = element.get('type')
            x = element.get('x', 0)
            y = element.get('y', 0)
            w = element.get('width')
            h = element.get('height')

            # Render dynamic content using Jinja2
            def render_jinja(text_content, context):
                if not isinstance(text_content, str):
                    return text_content
                jinja_template = env.from_string(text_content)
                return jinja_template.render(context)
            
            if elem_type == "text":
                text_content = render_jinja(element.get('text', ''), template_context)
                font_family = element.get('font_family', 'Helvetica')
                font_size = element.get('font_size', 10)
                font_weight = element.get('font_weight', '') # B, I, U
                align = element.get('align', 'L')
                
                pdf.set_font(font_family, font_weight, font_size)
                pdf.set_xy(x, y)
                if w and h:
                    pdf.multi_cell(w, h / len(text_content.split('\n')) if text_content else h, text_content, align=align)
                else:
                    pdf.write(font_size / 72, text_content) # Estimate line height if not given

            elif elem_type == "image":
                image_src = render_jinja(element.get('src', ''), template_context)
                if image_src and w and h:
                    try:
                        with urllib.request.urlopen(image_src) as response:
                            image_data = response.read()
                            img_buffer = io.BytesIO(image_data)
                            pdf.image(img_buffer, x=x, y=y, w=w, h=h)
                    except Exception:
                        pass # Ignore image errors
            
            elif elem_type == "qrcode":
                qr_data = render_jinja(element.get('data', public_url), template_context)
                if qr_data and w and h:
                    try:
                        qr_img = qrcode.make(qr_data, box_size=10, border=1)
                        qr_img_bytes = io.BytesIO()
                        qr_img.save(qr_img_bytes, format='PNG')
                        qr_img_bytes.seek(0)
                        pdf.image(qr_img_bytes, x=x, y=y, w=w, h=h)
                    except Exception:
                        pass # Ignore QR code errors

            elif elem_type == "barcode":
                barcode_data = render_jinja(element.get('data', batch.id), template_context)
                barcode_type = element.get('barcode_type', 'code128') # e.g., 'code128', 'ean13', 'upca'
                if barcode_data and w and h:
                    try:
                        # Barcode library expects string, convert if necessary
                        barcode_data_str = str(barcode_data)
                        
                        # Use specific barcode types or fallback
                        if barcode_type.lower() == 'upca' and barcode.UPCA.is_valid(barcode_data_str):
                             code = barcode.UPCA(barcode_data_str, writer=ImageWriter())
                        elif barcode_type.lower() == 'ean13' and barcode.EAN13.is_valid(barcode_data_str):
                             code = barcode.EAN13(barcode_data_str, writer=ImageWriter())
                        else: # Default to Code128
                            code = barcode.Code128(barcode_data_str, writer=ImageWriter())
                            
                        barcode_img_bytes = io.BytesIO()
                        code.write(barcode_img_bytes)
                        barcode_img_bytes.seek(0)
                        pdf.image(barcode_img_bytes, x=x, y=y, w=w, h=h)
                    except Exception:
                        pass # Ignore barcode errors
    else:
        # --- Default Hardcoded Layout (for backwards compatibility if no template_id) ---
        pdf = FPDF(orientation='L', unit='in', format=(2, 4))
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)
        pdf.set_font('Helvetica', 'B', 14)
        
        # --- Left Panel (PDP) ---
        pdp_width = 4 * 0.6
        pdf.set_xy(0.12, 0.12)
        pdf.multi_cell(pdp_width - 0.24, 0.2, item.name, align='L')
        
        if item.jsonb_doc.get('french_name'):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.ln(0.05)
            pdf.cell(pdp_width - 0.24, 0.15, item.jsonb_doc.get('french_name'), align='L')

        # Logo
        if actor.jsonb_doc.get('logo_url'):
            try:
                with urllib.request.urlopen(actor.jsonb_doc.get('logo_url')) as response:
                    logo_data = response.read()
                    logo_image = io.BytesIO(logo_data)
                    pdf.image(logo_image, x=0.2, y=0.8, w=pdp_width - 0.4)
            except Exception:
                pass # Ignore logo errors

        # Footer
        pdf.set_xy(0.12, 2 - 0.6)
        pdf.set_font('Helvetica', 'B', 13)
        if batch.jsonb_doc.get('quantity'):
            qty = batch.jsonb_doc['quantity']
            pdf.cell(pdp_width, 0.2, f"{qty.get('amount')} {qty.get('unit')}")
        
        pdf.set_xy(0.12, 2 - 0.4)
        pdf.set_font('Helvetica', '', 6)
        if item.jsonb_doc.get('origin'):
            pdf.cell(pdp_width, 0.2, item.jsonb_doc.get('origin'))

        # --- Right Panel (Info) ---
        info_width = 4 * 0.4
        info_start_x = pdp_width
        pdf.line(info_start_x, 0, info_start_x, 2)
        
        pdf.set_xy(info_start_x + 0.05, 0.1)
        pdf.set_font('Helvetica', 'B', 6)
        pdf.multi_cell(info_width - 0.1, 0.1, actor.name, align='C')
        
        if actor.jsonb_doc.get('address'):
            addr = actor.jsonb_doc['address']
            address_line = f"{addr.get('street', '')}\n{addr.get('city', '')}, {addr.get('region', '')} {addr.get('postal_code', '')}"
            pdf.set_xy(info_start_x + 0.05, pdf.get_y())
            pdf.set_font('Helvetica', '', 5.5)
            pdf.multi_cell(info_width - 0.1, 0.1, address_line, align='C')

        # QR Code
        try:
            qr_img = qrcode.make(public_url, box_size=10, border=1)
            qr_img_bytes = io.BytesIO()
            qr_img.save(qr_img_bytes, format='PNG')
            qr_img_bytes.seek(0)
            pdf.image(qr_img_bytes, x=info_start_x + (info_width - 0.8) / 2, y=pdf.get_y() + 0.05, w=0.8, h=0.8)
        except Exception:
            pass # Ignore QR code errors
        
        # Lot Code
        pdf.set_xy(info_start_x + 0.05, 1.5)
        pdf.set_font('Courier', 'B', 7)
        pdf.cell(info_width - 0.1, 0.2, f"LOT: {batch.jsonb_doc.get('lot_code', batch.id)}", align='C')
        
        # Barcode
        try:
            code128 = barcode.get('code128', batch.id, writer=ImageWriter())
            barcode_img_bytes = io.BytesIO()
            code128.write(barcode_img_bytes)
            barcode_img_bytes.seek(0)
            pdf.image(barcode_img_bytes, x=info_start_x + 0.1, y=1.7, w=info_width - 0.2, h=0.2)
        except Exception:
            pass # Ignore barcode errors

    # 3. Return PDF
    pdf_bytes = bytes(pdf.output())
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=label_{batch_id}.pdf"
    })


# --- LABEL TEMPLATE CRUD ---

@router.get("/actors/{actor_id}/labels", response_class=HTMLResponse)
def list_label_templates_page(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """List all label templates for an actor (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    label_templates = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id).all()
    return templates.TemplateResponse("label_templates.html", {
        "request": request,
        "actor_id": actor_id,
        "templates": label_templates,
        "user": user
    })

@router.get("/actors/{actor_id}/labels/new", response_class=HTMLResponse)
def new_label_template_form(
    request: Request, 
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new label template (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    return templates.TemplateResponse("label_template_form.html", {
        "request": request,
        "actor_id": actor_id,
        "template": None,
        "mode": "create",
        "user": user
    })

@router.post("/actors/{actor_id}/labels/create")
async def create_label_template(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new label template (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    now = datetime.utcnow().isoformat() + "Z"
    
    template_id = form_data.get("id")
    template_name = form_data.get("name")
    width_in = float(form_data.get("width_in"))
    height_in = float(form_data.get("height_in"))
    elements_json = form_data.get("elements_json", "[]") # Default to empty array

    try:
        elements_data = json.loads(elements_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for elements.")

    # Store full template data in jsonb_doc
    template_data = {
        "id": template_id,
        "name": template_name,
        "actor_id": actor_id,
        "width_in": width_in,
        "height_in": height_in,
        "elements": elements_data,
        "created_at": now,
        "updated_at": now
    }

    db_template = db_models.LabelTemplate(
        id=template_id,
        actor_id=actor_id,
        name=template_name,
        width_in=width_in,
        height_in=height_in,
        jsonb_doc=template_data
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return RedirectResponse(url=f"/actors/{actor_id}/labels", status_code=303)


@router.get("/actors/{actor_id}/labels/{template_id}/edit", response_class=HTMLResponse)
def edit_label_template_form(
    request: Request, 
    actor_id: str, 
    template_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit an existing label template (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    template = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id, id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Label Template not found")
    
    # Pre-populate elements_json for the form
    template.jsonb_doc['elements_json'] = json.dumps(template.jsonb_doc.get('elements', []), indent=2)

    return templates.TemplateResponse("label_template_form.html", {
        "request": request,
        "actor_id": actor_id,
        "template": template,
        "mode": "edit",
        "user": user
    })

@router.post("/actors/{actor_id}/labels/{template_id}/update")
async def update_label_template(
    request: Request,
    actor_id: str,
    template_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing label template (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    template = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id, id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Label Template not found")

    form_data = await request.form()
    
    template.name = form_data.get("name")
    template.width_in = float(form_data.get("width_in"))
    template.height_in = float(form_data.get("height_in"))
    elements_json = form_data.get("elements_json", "[]")

    try:
        elements_data = json.loads(elements_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for elements.")

    # Update jsonb_doc
    template.jsonb_doc['name'] = template.name
    template.jsonb_doc['width_in'] = template.width_in
    template.jsonb_doc['height_in'] = template.height_in
    template.jsonb_doc['elements'] = elements_data
    template.jsonb_doc['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/labels", status_code=303)


@router.post("/actors/{actor_id}/labels/{template_id}/delete")
def delete_label_template(
    actor_id: str, 
    template_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete a label template (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    template = db.query(db_models.LabelTemplate).filter_by(actor_id=actor_id, id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Label Template not found")
    
    db.delete(template)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/labels", status_code=303)


# --- PROCESS CRUD (forms must come before detail routes) ---

@router.get("/actors/{actor_id}/processes/new", response_class=HTMLResponse)
def new_process_form(
    request: Request, 
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new process (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    return templates.TemplateResponse("process_form.html", {
        "request": request,
        "actor_id": actor_id,
        "process": None,
        "mode": "create",
        "user": user
    })


@router.get("/actors/{actor_id}/processes/{process_id}/edit", response_class=HTMLResponse)
def edit_process_form(
    request: Request, 
    actor_id: str, 
    process_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit a process (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    process = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id,
        db_models.Process.id == process_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    return templates.TemplateResponse("process_form.html", {
        "request": request,
        "actor_id": actor_id,
        "process": process.jsonb_doc,
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/processes/{process_id}/update")
async def update_process(
    request: Request,
    actor_id: str,
    process_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing process (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    update_data = {}
    
    if form_data.get("name"):
        update_data["name"] = form_data.get("name")
    
    if form_data.get("kind"):
        update_data["kind"] = form_data.get("kind")
        
    if form_data.get("description"):
        update_data["description"] = form_data.get("description")
    else:
        update_data["description"] = None
    
    if form_data.get("version"):
        update_data["version"] = form_data.get("version")
    else:
        update_data["version"] = None
        
    steps_raw = form_data.get("steps", "")
    if steps_raw:
        update_data["steps"] = [s.strip() for s in steps_raw.replace("\n", ",").split(",") if s.strip()]
    else:
        update_data["steps"] = None

    process = process_service.update_process(db, actor_id, process_id, update_data)
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    return RedirectResponse(url=f"/actors/{actor_id}/processes", status_code=303)


@router.get("/actors/{actor_id}/processes", response_class=HTMLResponse)
def list_processes_page(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Processes list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    processes = db.query(db_models.Process).filter(
        db_models.Process.actor_id == actor_id
    ).all()
    
    return templates.TemplateResponse("processes.html", {
        "request": request,
        "actor_id": actor_id,
        "processes": [process.jsonb_doc for process in processes],
        "user": user
    })


@router.get("/actors/{actor_id}/processes/{process_id}", response_class=HTMLResponse)
def process_detail_page(
    request: Request, 
    actor_id: str, 
    process_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Process detail page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "events": process_events,
        "user": user
    })


@router.get("/actors/{actor_id}/locations", response_class=HTMLResponse)
def list_locations_page(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Locations list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    locations = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id
    ).all()
    
    return templates.TemplateResponse("locations.html", {
        "request": request,
        "actor_id": actor_id,
        "locations": [location.jsonb_doc for location in locations],
        "user": user
    })


@router.get("/actors/{actor_id}/events", response_class=HTMLResponse)
def list_events_page(
    request: Request, 
    actor_id: str,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Events list page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "filter_type": event_type,
        "user": user
    })


@router.get("/actors/{actor_id}/traceability", response_class=HTMLResponse)
def traceability_page(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Traceability explorer page (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    # Get all batches for selection
    batches = db.query(db_models.Batch).filter(
        db_models.Batch.actor_id == actor_id
    ).order_by(db_models.Batch.production_date.desc()).limit(50).all()
    
    return templates.TemplateResponse("traceability.html", {
        "request": request,
        "actor_id": actor_id,
        "batches": [batch.jsonb_doc for batch in batches],
        "user": user
    })


@router.get("/actors/{actor_id}/traceability/batch/{batch_id}", response_class=HTMLResponse)
def traceability_graph_page(
    request: Request, 
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Traceability graph visualization (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "graph": graph,
        "user": user
    })


# ============================================================================
# CRUD Operations (Create, Update, Delete)
# ============================================================================

# --- ACTOR CRUD ---

@router.get("/actors/new", response_class=HTMLResponse)
def new_actor_form(
    request: Request,
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new actor (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    return templates.TemplateResponse("actor_form.html", {
        "request": request,
        "actor": None,
        "mode": "create",
        "user": user
    })


import re
import secrets

@router.post("/actors/create")
async def create_actor(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new actor"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    form_data = await request.form()
    
    name = form_data.get("name")
    
    # Always auto-generate ID
    # Simple slugify: lowercase, replace non-alphanumeric with hyphen
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if not slug:
        slug = "actor" # Fallback if name has no alphanumeric chars
    
    # Append 4-digit random hex suffix for uniqueness
    suffix = secrets.token_hex(2) 
    actor_id = f"{slug}-{suffix}"
            
    actor_data = {
        "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
        "id": actor_id,
        "name": name,
        "kind": form_data.get("kind", "producer"),
        "contacts": {}
    }
    
    if form_data.get("email"):
        actor_data["contacts"]["email"] = form_data.get("email")
    if form_data.get("phone"):
        actor_data["contacts"]["phone"] = form_data.get("phone")
    if form_data.get("website"):
        actor_data["contacts"]["website"] = form_data.get("website")
    if form_data.get("logo_url"):
        actor_data["logo_url"] = form_data.get("logo_url")
    
    # SFCR Compliance Fields
    if form_data.get("sfcr_license_id"):
        actor_data["sfcr_license_id"] = form_data.get("sfcr_license_id")
    if form_data.get("recall_contact_name"):
        actor_data["recall_contact_name"] = form_data.get("recall_contact_name")
    if form_data.get("recall_phone"):
        actor_data["recall_phone"] = form_data.get("recall_phone")

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
        owner_id=user.pk, # Associate with user
        jsonb_doc=actor_data
    )
    db.add(db_actor)
    db.commit()
    
    return RedirectResponse(url="/actors", status_code=303)


@router.get("/actors/{actor_id}/edit", response_class=HTMLResponse)
def edit_actor_form(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit an actor (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    actor = get_actor_if_owned(actor_id, db, user)
    
    if not actor: # Already checked by get_actor_if_owned, but explicit for clarity
        return HTMLResponse("Actor not found", status_code=404)
    
    return templates.TemplateResponse("actor_form.html", {
        "request": request,
        "actor": actor.jsonb_doc,
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/update")
async def update_actor(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing actor (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    actor = get_actor_if_owned(actor_id, db, user)
    
    if not actor: # Already checked by get_actor_if_owned, but explicit for clarity
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
    if form_data.get("logo_url"):
        actor_data["logo_url"] = form_data.get("logo_url")
    else:
        actor_data.pop("logo_url", None)
        
    # SFCR Compliance Fields
    if form_data.get("sfcr_license_id"):
        actor_data["sfcr_license_id"] = form_data.get("sfcr_license_id")
    else:
        actor_data.pop("sfcr_license_id", None)
        
    if form_data.get("recall_contact_name"):
        actor_data["recall_contact_name"] = form_data.get("recall_contact_name")
    else:
        actor_data.pop("recall_contact_name", None)
        
    if form_data.get("recall_phone"):
        actor_data["recall_phone"] = form_data.get("recall_phone")
    else:
        actor_data.pop("recall_phone", None)
    
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
def delete_actor(
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete an actor (Protected)"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    actor = get_actor_if_owned(actor_id, db, user)
    
    if not actor: # Already checked by get_actor_if_owned, but explicit for clarity
        raise HTTPException(status_code=404, detail="Actor not found")
    
    db.delete(actor)
    db.commit()
    
    return RedirectResponse(url="/actors", status_code=303)


# --- ITEM CRUD ---

@router.get("/actors/{actor_id}/items/new", response_class=HTMLResponse)
def new_item_form(
    request: Request, 
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new item (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    return templates.TemplateResponse("item_form.html", {
        "request": request,
        "actor_id": actor_id,
        "item": None,
        "mode": "create",
        "user": user
    })


@router.post("/actors/{actor_id}/items/create")
async def create_item(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new item (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    if form_data.get("french_name"):
        item_data["french_name"] = form_data.get("french_name")
    if form_data.get("origin"):
        item_data["origin"] = form_data.get("origin")
    
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
def edit_item_form(
    request: Request, 
    actor_id: str, 
    item_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit an item (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/items/{item_id}/update")
async def update_item(
    request: Request,
    actor_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing item (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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

    if form_data.get("french_name"):
        item_data["french_name"] = form_data.get("french_name")
    else:
        item_data.pop("french_name", None)

    if form_data.get("origin"):
        item_data["origin"] = form_data.get("origin")
    else:
        item_data.pop("origin", None)
    
    item.name = item_data["name"]
    item.jsonb_doc = item_data
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/items", status_code=303)


@router.post("/actors/{actor_id}/items/{item_id}/delete")
def delete_item(
    actor_id: str, 
    item_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete an item (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new batch (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    try:
        form_data = await request.form()
        
        # Add quantity if provided
        quantity_obj = None
        if form_data.get("quantity_amount") and form_data.get("quantity_unit"):
            quantity_obj = entities.Quantity(
                amount=float(form_data.get("quantity_amount")),
                unit=form_data.get("quantity_unit")
            )
        
        # Auto-generate ID if not provided
        batch_id = form_data.get("id")
        if not batch_id:
            # Generate short 8-char hex ID (e.g. "a1b2c3d4")
            batch_id = secrets.token_hex(4)

        # Add lot code, default to id if not provided
        lot_code = form_data.get("lot_code") or batch_id
        
        # Compliance fields
        external_lot_code = form_data.get("external_lot_code")
        is_mock_recall = form_data.get("is_mock_recall") == "true"

        batch_service.create_batch(
            db=db,
            batch_id=batch_id,
            actor_id=actor_id,
            item_id=form_data.get("item_id"),
            production_date=form_data.get("production_date"),
            expiration_date=form_data.get("expiration_date"),
            status=form_data.get("status", "active"),
            quantity=quantity_obj,
            origin_kind=form_data.get("origin_kind"),
            notes=form_data.get("notes"),
            lot_code=lot_code,
            external_lot_code=external_lot_code,
            is_mock_recall=is_mock_recall
        )
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating batch: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error creating batch: {str(e)}")


@router.post("/actors/{actor_id}/batches/{batch_id}/delete")
def delete_batch(
    actor_id: str, 
    batch_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete a batch (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new process (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    # Handle steps (comma-separated or line-separated)
    steps = None
    steps_raw = form_data.get("steps", "")
    if steps_raw:
        steps = [s.strip() for s in steps_raw.replace("\n", ",").split(",") if s.strip()]
    
    process_service.create_process(
        db=db,
        actor_id=actor_id,
        process_id=form_data.get("id"),
        name=form_data.get("name"),
        kind=form_data.get("kind", "processing"),
        description=form_data.get("description"),
        version=form_data.get("version"),
        steps=steps
    )
    
    return RedirectResponse(url=f"/actors/{actor_id}/processes", status_code=303)


@router.post("/actors/{actor_id}/processes/{process_id}/delete")
def delete_process(
    actor_id: str, 
    process_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete a process (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
def new_location_form(
    request: Request, 
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new location (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    return templates.TemplateResponse("location_form.html", {
        "request": request,
        "actor_id": actor_id,
        "location": None,
        "mode": "create",
        "user": user
    })


@router.get("/actors/{actor_id}/locations/{location_id}/edit", response_class=HTMLResponse)
def edit_location_form(
    request: Request, 
    actor_id: str, 
    location_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit a location (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    location = db.query(db_models.Location).filter(
        db_models.Location.actor_id == actor_id,
        db_models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return templates.TemplateResponse("location_form.html", {
        "request": request,
        "actor_id": actor_id,
        "location": location.jsonb_doc,
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/locations/{location_id}/update")
async def update_location(
    request: Request,
    actor_id: str,
    location_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing location (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    update_data = {}
    
    if form_data.get("name"):
        update_data["name"] = form_data.get("name")
    
    if form_data.get("kind"):
        update_data["kind"] = form_data.get("kind")
        
    if form_data.get("description"):
        update_data["description"] = form_data.get("description")
    else:
        update_data["description"] = None
        
    # Address
    address = None
    if form_data.get("street") or form_data.get("city"):
        address = {}
        if form_data.get("street"):
            address["street"] = form_data.get("street")
        if form_data.get("city"):
            address["city"] = form_data.get("city")
        if form_data.get("region"):
            address["region"] = form_data.get("region")
        if form_data.get("postal_code"):
            address["postal_code"] = form_data.get("postal_code")
        if form_data.get("country"):
            address["country"] = form_data.get("country")
    update_data["address"] = address

    # Coordinates
    coordinates = None
    if form_data.get("lat") and form_data.get("lon"):
        coordinates = {
            "lat": float(form_data.get("lat")),
            "lon": float(form_data.get("lon"))
        }
    update_data["coordinates"] = coordinates
    
    location = location_service.update_location(db, actor_id, location_id, update_data)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return RedirectResponse(url=f"/actors/{actor_id}/locations", status_code=303)


@router.post("/actors/{actor_id}/locations/create")
async def create_location(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new location (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    # Address
    address = None
    if form_data.get("street") or form_data.get("city"):
        address = {}
        if form_data.get("street"):
            address["street"] = form_data.get("street")
        if form_data.get("city"):
            address["city"] = form_data.get("city")
        if form_data.get("region"):
            address["region"] = form_data.get("region")
        if form_data.get("postal_code"):
            address["postal_code"] = form_data.get("postal_code")
        if form_data.get("country"):
            address["country"] = form_data.get("country")
            
    # Coordinates
    coordinates = None
    if form_data.get("lat") and form_data.get("lon"):
        coordinates = {
            "lat": float(form_data.get("lat")),
            "lon": float(form_data.get("lon"))
        }

    location_service.create_location(
        db=db,
        actor_id=actor_id,
        location_id=form_data.get("id"),
        name=form_data.get("name"),
        kind=form_data.get("kind", "field"),
        description=form_data.get("description"),
        address=address,
        coordinates=coordinates
    )
    
    return RedirectResponse(url=f"/actors/{actor_id}/locations", status_code=303)


@router.post("/actors/{actor_id}/locations/{location_id}/delete")
def delete_location(
    actor_id: str, 
    location_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete a location (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
def new_production_run_form(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a production run (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "locations": [l.jsonb_doc for l in locations],
        "user": user
    })


@router.get("/actors/{actor_id}/split-batch/new", response_class=HTMLResponse)
def new_split_batch_form(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to split a batch (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "locations": [l.jsonb_doc for l in locations],
        "user": user
    })


@router.get("/actors/{actor_id}/merge-batch/new", response_class=HTMLResponse)
def new_merge_batch_form(
    request: Request, 
    actor_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to merge batches (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "locations": [l.jsonb_doc for l in locations],
        "user": user
    })


@router.get("/actors/{actor_id}/events/new", response_class=HTMLResponse)
def new_event_form(
    request: Request, 
    actor_id: str, 
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to create a new event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
        "mode": "create",
        "user": user,
        "preselected_type": event_type
    })


@router.get("/actors/{actor_id}/events/{event_id}/edit", response_class=HTMLResponse)
def edit_event_form(
    request: Request, 
    actor_id: str, 
    event_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to edit an event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    processes = db.query(db_models.Process).filter(db_models.Process.actor_id == actor_id).all()
    locations = db.query(db_models.Location).filter(db_models.Location.actor_id == actor_id).all()
    
    return templates.TemplateResponse("event_form.html", {
        "request": request,
        "actor_id": actor_id,
        "event": event.jsonb_doc,
        "processes": [p.jsonb_doc for p in processes],
        "locations": [l.jsonb_doc for l in locations],
        "mode": "edit",
        "user": user
    })


@router.post("/actors/{actor_id}/events/{event_id}/update")
async def update_event(
    request: Request,
    actor_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Update an existing event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    form_data = await request.form()
    
    update_data = {}
    
    # Only allow editing metadata, not inputs/outputs or type
    if form_data.get("timestamp"):
        update_data["timestamp"] = form_data.get("timestamp")
        
    if form_data.get("performed_by"):
        update_data["performed_by"] = form_data.get("performed_by")
    else:
        update_data["performed_by"] = None
        
    if form_data.get("process_id"):
        update_data["process_id"] = form_data.get("process_id")
    else:
        update_data["process_id"] = None
        
    if form_data.get("location_id"):
        update_data["location_id"] = form_data.get("location_id")
    else:
        update_data["location_id"] = None
        
    if form_data.get("notes"):
        update_data["notes"] = form_data.get("notes")
    else:
        update_data["notes"] = None

    event = event_service.update_event(db, actor_id, event_id, update_data)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return RedirectResponse(url=f"/actors/{actor_id}/events", status_code=303)


@router.post("/actors/{actor_id}/events/create")
async def create_event(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a new event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    input_ids = form_data.getlist("inputs")
    if input_ids:
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
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a production run via form submission (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Split a batch via form submission (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Merge batches via form submission (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
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


@router.get("/actors/{actor_id}/harvest/new", response_class=HTMLResponse)
def new_harvest_form(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Form to log a harvest (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    # Get items (products)
    items = db.query(db_models.Item).filter(db_models.Item.actor_id == actor_id).all()
    
    # Get recent planting events
    plantings = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.event_type == 'planting'
    ).order_by(db_models.Event.timestamp.desc()).limit(50).all()
    
    # Process plantings for display (add location name)
    planting_data = []
    for p in plantings:
        p_doc = p.jsonb_doc
        loc_name = "Unknown Location"
        location_id = p_doc.get("location_id")
        if location_id:
            loc = db.query(db_models.Location).filter(db_models.Location.id == location_id).first()
            if loc:
                loc_name = loc.name
        
        planting_data.append({
            "id": p.id,
            "timestamp": p.timestamp,
            "location_name": loc_name,
            "notes": p_doc.get("notes", "")
        })
    
    return templates.TemplateResponse("harvest_form.html", {
        "request": request,
        "actor_id": actor_id,
        "items": [i.jsonb_doc for i in items],
        "plantings": planting_data,
        "now_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
        "user": user
    })


@router.post("/actors/{actor_id}/harvest/create")
async def create_harvest(
    request: Request,
    actor_id: str,
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Create a harvest batch and event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    try:
        form_data = await request.form()
        
        # 1. Gather Data
        item_id = form_data.get("item_id")
        quantity_amount = float(form_data.get("quantity_amount"))
        quantity_unit = form_data.get("quantity_unit")
        harvest_date = form_data.get("harvest_date") or (datetime.utcnow().isoformat() + "Z")
        planting_event_id = form_data.get("planting_event_id")
        user_notes = form_data.get("notes", "")
        
        location_id = None
        notes = user_notes
        
        # 2. If Linked to Planting: Get Location & Link
        if planting_event_id:
            planting = db.query(db_models.Event).filter(
                db_models.Event.actor_id == actor_id,
                db_models.Event.id == planting_event_id
            ).first()
            
            if planting:
                location_id = planting.jsonb_doc.get("location_id")
                # Append linkage info to notes for human readability
                link_note = f"\n[System] Linked to Planting Event: {planting.id} ({planting.timestamp[:10]})"
                notes += link_note
        
        # 3. Create the Batch
        batch_id = secrets.token_hex(4) # Generate ID
        
        quantity_obj = entities.Quantity(amount=quantity_amount, unit=quantity_unit)
        
        batch_service.create_batch(
            db=db,
            batch_id=batch_id,
            actor_id=actor_id,
            item_id=item_id,
            production_date=harvest_date, # Harvest date is production date
            status="active",
            quantity=quantity_obj,
            origin_kind="harvested",
            notes=notes,
            lot_code=batch_id # Default lot code to ID
        )
        
        # 4. Create the Harvest Event
        event_id = f"evt-{secrets.token_hex(4)}"
        now = datetime.utcnow().isoformat() + "Z"
        
        event_data = {
            "schema": "https://github.com/OpenOriginFood/open-origin-json/tree/v0.5",
            "type": "event",
            "id": event_id,
            "actor_id": actor_id,
            "event_type": "harvest",
            "timestamp": harvest_date,
            "location_id": location_id,
            "notes": notes,
            "outputs": [{"batch_id": batch_id}], # Output the new batch
            "created_at": now,
            "updated_at": now
        }
        
        # If we linked a planting, maybe store it in external_ids or metadata?
        if planting_event_id:
            event_data["external_ids"] = {"planting_event_id": planting_event_id}

        db_event = db_models.Event(
            id=event_id,
            actor_id=actor_id,
            event_type="harvest",
            timestamp=harvest_date,
            jsonb_doc=event_data
        )
        db.add(db_event)
        db.commit()
        
        return RedirectResponse(url=f"/actors/{actor_id}/batches", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating harvest: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error creating harvest: {str(e)}")


@router.post("/actors/{actor_id}/events/{event_id}/delete")
def delete_event(
    actor_id: str, 
    event_id: str, 
    db: Session = Depends(get_db),
    user: Optional[db_models.User] = Depends(get_current_user_from_cookie)
):
    """Delete an event (Protected)."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    get_actor_if_owned(actor_id, db, user)
    
    event = db.query(db_models.Event).filter(
        db_models.Event.actor_id == actor_id,
        db_models.Event.id == event_id
    ).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    
    return RedirectResponse(url=f"/actors/{actor_id}/events", status_code=303)
