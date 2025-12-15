# VeriBatch ERP Specification

## 1. What This ERP Is

**Working name:** VeriBatch *(change later if you want)*

A SaaS system for small producers (farms + cottage food) where everything — inventory, production, batch tracking, labels, compliance — is stored and exposed as **Open Origin JSON (OOJ)**.

**Internally:**
- OOJ is the contract between UI, API, and storage
- Your SaaS is basically *"OOJ with opinions, screens, and automations"*

---

## 2. High-Level Architecture

### Backend

**Tech stack:** Python + FastAPI + Postgres *(or Django/HTMX if preferred)*

**Key ideas:**

1. **Multi-tenant:** Each actor = one tenant (or one organization inside a tenant)

2. **OOJ as the API schema:**
   - REST endpoints like `/actors`, `/items`, `/batches`, `/events`, etc.
   - All response bodies are OOJ entities (`Actor`, `Batch`, etc.)
   - Backend uses your `ooj_client` library for validation + serialization

3. **Data storage pattern:**
   - Postgres tables per entity plus a JSONB `document` field:
     ```sql
     actors(id, jsonb_doc, created_at, updated_at, tenant_id, ...)
     batches(id, actor_id, jsonb_doc, status, item_id, production_date, ...)
     ```
   - This gives you:
     - Fast filters on key columns (`status`, `actor_id`, `item_id`)
     - Raw OOJ doc for export/API, untouched
   - When you write/update an entity:
     - Construct it via `ooj_client` (dataclass)
     - `to_dict()`, store in `jsonb_doc`, and update indexed columns

4. **Services layer:**
   - Thin service functions that encapsulate OOJ idioms:
     - `create_batch(...)`
     - `record_event(...)` (and optionally update batch statuses/quantities)
     - `split_batch(...)` (creates new batches + split event)
     - `merge_batches(...)`
     - `dispose_batch(...)`
   - These become the core of your "Farm ERP" operations

### Frontend

**Two workable options:**
- React + Tailwind SPA hitting JSON API (OOJ docs)
- Django/HTMX where templates render OOJ dicts directly

Given how deeply "document-y" OOJ is, a JSON-y front end is natural.

**Mental model:**
```
UI forms → build OOJ dataclasses → send to backend
Backend → validates with ooj_client + validators.py → stores → returns OOJ
```

---

## 3. Core Modules Mapped to OOJ

Let's map SaaS "features" to your OOJ entities, so nothing is vague.

### 3.1 Inventory & Items

**UI concepts:**

"Products & Ingredients" screen:
- Ingredients (raw materials)
- Finished goods
- Packaging

**OOJ mapping:**
- CRUD screens on `Item`
- List of `Batch` records grouped by item

**Nice touch:**
- Show current on-hand quantity per item = `sum(Batch.quantity)` for status in `{"active", "quarantined"}`
- Clicking an item shows:
  - List of batches
  - Indicator if any are near `expiration_date` or `best_before_date`

### 3.2 Batch Management & Lot Codes

**UI:**

"Lots & Batches" screen:
- Create a new batch (harvest, received shipment, produced lot)
- See status (active, depleted, recalled, etc.)
- Quick links to "Split", "Merge", "Dispose"

**OOJ mapping:**
- `Batch` entity for each lot
- `status` field tracked, but event history is canonical
- Use supporting functions:
  - `create_batch_from_receiving_event(...)`
  - `create_batch_from_processing_event(...)`

### 3.3 Production / Recipes

**UI:**

"Processes / Recipes":
- Define reusable processes (e.g., "Pickled Garlic v1")
- Start a production run using that process:
  - Choose inputs (batches)
  - Choose outputs (new batch ID + qty)
  - Record `performed_by`, `location`, notes

**OOJ mapping:**
- `Process` for the recipe template
- `Event` with:
  - `event_type="processing"` (or `x-fermentation_start`, etc.)
  - `inputs` (batches + quantity)
  - `outputs` (new batch)
  - `packaging_materials` as needed
- `Batch` for the resulting lot

**ERP service function:**
```python
def record_processing_run(actor_id, process_id, inputs, outputs, location_id, user):
    # build Event + new Batch docs using ooj_client
    ...
```

### 3.4 Traceability & "Where Did This Come From?"

**UI:**

Search by:
- Lot code
- Product name
- Date

Display a "trace" view:
- **Upstream:** What inputs went into this batch? (batches + actors)
- **Downstream:** What other batches this one fed into

**OOJ mapping:**
- All from `Event.inputs` / `Event.outputs` (+ `Link` for cross-actor)
- For Level 1 users you can fake it: just show batch + item + `origin_kind`, etc., no full graph
- Later you can add a simple graph view (like a little tree of batches/events)

### 3.5 Compliance & Documents

**UI:**

"Documents & Attachments" tab on:
- `Actor`
- `Batches`
- `Processes`

Label preview: show what would go on jar/label

**OOJ mapping:**
- `attachments` on `Batch`, `Process`, `Actor`, etc.
- `external_ids` for cert numbers, GTIN, SKUs

**Nice feature:** Your system can generate label text from OOJ data:
- Item name
- Lot code (`external_ids.lot_code`)
- Best before
- Actor name & address

### 3.6 Integrations & Export

**UI:**

"Integrations & Export" page:

Export all data for this actor as:
- OOJ JSON (folder or zip)
- CSVs (items, batches, events)

Configure push to:
- S3 / MinIO bucket
- GitHub (like you do for CIOOS)
- Another traceability system

**OOJ mapping:**
- Your Python client already round-trips OOJ docs
- Exports are literally `to_dict()` for each entity, plus some namespace layout like:
  ```
  /actor.json
  /items/*.json
  /batches/*.json
  /events/*.json
  ```

**That's insanely compelling:** *"Click one button → full OOJ archive ready for inspector/regulator/import"*

---

## 4. Levels of Adoption → Product Tiers / UX Modes

Your spec has Levels 1/2/3. You can turn that into "modes" in the app.

### Level 1 Mode — Minimal Traceability (Starter / Cheap Plan)

**Only show:**
- `Actor`
- `Items`
- `Batches`

No explicit "Events" section in UI (you might still create minimal events under the hood, but user doesn't see them).

**Features:**
- Simple lot creation
- Inventory list
- Printable labels with lot code & dates
- CSV/JSON export

✅ **Perfect for smallest producers**

### Level 2 Mode — Process & Event Tracking (Pro Plan)

**Unlock:**
- "Events" and "Processes" sections
- Production runs with inputs/outputs, packaging
- Split/Merge UI
- Basic traceability graph ("follow this lot backwards")

✅ **This is the sweet spot for small serious businesses**

### Level 3 Mode — Full Provenance & Context (Enterprise / Regulator / Research)

**Unlock:**
- `Location` entity management
- Map/coordinate views
- `Link` entities for cross-actor relationships
- More advanced exports and reporting
- Possibly external dataset ingestion (lab results, environmental data)

✅ **Target this later** — it's more work, but aligns with your R&D lab + CIOOS brain

---

## 5. A Concrete v1 Slice

If you wanted to ship something non-embarrassing but small, I'd define v1 as:

### Backend v1

**FastAPI (or Django) app with routes:**
- `POST/GET /actors/{actor_id}`
- `POST/GET /actors/{actor_id}/items`
- `POST/GET /actors/{actor_id}/batches`
- `POST/GET /actors/{actor_id}/events`

**Uses `ooj_client` for:**
- Building entities
- Validation (via `validators.validate_entity`)

**Stores OOJ docs in Postgres (`jsonb_doc`) with a few indexed columns:**
- `actor_id`
- `type`
- `batch.status`, `batch.item_id`, `batch.production_date` (extracted)

### Frontend v1

**Authenticated user** (one organization for now)

**Screens:**

1. **Dashboard:**
   - Total batches
   - Warnings (expiring soon, etc.)

2. **Items:**
   - List + create/edit

3. **Batches:**
   - List (filter by item)
   - Create "new batch" (simple form)
   - Detail page showing:
     - Core fields
     - Attachments (if any)
     - "Export this batch as JSON"

4. **Production Run (Single Event):**
   - Manually pick:
     - Input batch
     - Output batch ID + qty
     - Packaging batch
   - Backend creates:
     - `Event` (processing)
     - `Batch` (output)

**No traceability graph yet, just simple navigation.**

---

## What Makes It Uniquely "Yours"

1. **Every object created is OOJ v0.4 compliant out of the box**
2. **"Export all data" gives the user a clean OOJ archive**
3. **You can say in marketing:**
   > *"Open Origin JSON inside – you're never locked in."*

**That is a huge trust signal for small, paranoid producers.** 🎯
