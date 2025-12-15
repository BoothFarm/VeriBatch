# System Capabilities: VeriBatch (OOJ ERP)

This document outlines the capabilities, data models, and workflows of the VeriBatch system. It is designed to inform an AI agent of the system's full scope for future development, refactoring, or support tasks.

## 1. Core Architecture & Data Model
VeriBatch is built on the **Open Origin JSON (OOJ) v0.5** standard. It uses a hybrid data storage approach:
*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL with SQLAlchemy.
*   **Hybrid Storage:** All entities (`Actor`, `Item`, `Batch`, `Event`, etc.) are stored as full JSONB documents in a `jsonb_doc` column for schema flexibility, while key fields (`id`, `actor_id`, `timestamp`, `status`) are duplicated in relational columns for high-performance indexing and querying.
*   **Frontend:** Server-side rendered HTML using Jinja2 templates + Tailwind CSS.

## 2. Entity Capabilities

### 2.1 Actors (Identity)
*   **Multi-Tenancy:** A single `User` account can manage multiple `Actor` profiles (e.g., separate farms, processing facilities, or business units).
*   **Profile Management:** Stores detailed business info (Name, Address, Contacts, Certifications).
*   **Security:** Users can only access/modify Actors they explicitly own.

### 2.2 Items (Products)
*   **Catalog Management:** Defines the "what" of the supply chain (Ingredients, Raw Materials, Finished Goods).
*   **Categorization:** Supports categories like "raw_material", "product", "packaging".
*   **Details:** Tracks variety, origin, french name translations, and unit types.

### 2.3 Locations (Geo-Spatial)
*   **Site Management:** Defines physical places (Fields, Greenhouses, Warehouses, Bins).
*   **Mapping:** Stores GPS coordinates (`lat`, `lon`) and physical addresses.
*   **Integration:** Events are linked to specific Locations to prove *where* something happened.

### 2.4 Batches (Inventory & Lot Codes)
*   **Lot Management:** Automatically generates unique Batch IDs / Lot Codes.
*   **Lifecycle Status:** Tracks status: `active`, `depleted`, `quarantined`, `recalled`, `expired`, `disposed`.
*   **Quantity Tracking:** precise amounts with units (kg, lb, count, etc.).
*   **Origin Tracking:**
    *   **Harvested:** Created from a location/planting.
    *   **Received:** Intake from an external supplier.
    *   **Manufactured:** Result of a process (merge/split/transform).
*   **Notes:** Supports attaching free-text notes to any batch for quality/observation data.

### 2.5 Events (The Traceability Engine)
*   **Event Types:**
    *   `planting`: Records seeding/planting at a Location.
    *   `harvest`: Creates new bio-mass from a Location/Planting.
    *   `processing`: Transforms input batches -> output batches (e.g., washing, cutting).
    *   `split`: Divides one batch into many.
    *   `merge`: Combines many batches into one.
    *   `storage_move`: Relocates inventory.
    *   `shipping`: records transfer to a client (Output: One step forward).
    *   `receiving`: records intake from supplier (Input: One step back).
    *   `disposal`: Records waste/loss.
*   **Linkage:** Every event explicitly links `inputs` (consumed batches) to `outputs` (created batches).
*   **Context:** Captures `timestamp`, `location_id`, `performed_by`, and `notes`.

### 2.6 Processes (Recipes/SOPs)
*   **Standardization:** Defines reusable recipes or Standard Operating Procedures (SOPs).
*   **Versioning:** Tracks versions of a process.
*   **Steps:** Lists sequential steps for the process.

## 3. User Workflows & Features

### 3.1 Traceability & Compliance (SFCR Ready)
*   **Graph Visualization:** A "Traceability Graph" feature visualizes the entire history of a batch, upstream (where did it come from?) and downstream (where did it go?).
*   **One-Step-Back:** Captures supplier info via `receiving` events.
*   **One-Step-Forward:** Captures distribution via `shipping` events.
*   **Public Verification:** Generates public-facing verification pages for consumers to scan a QR code and see the product's journey without login.

### 3.2 Production Operations
*   **Quick Actions:** Dashboard buttons for common tasks (Log Planting, Log Harvest).
*   **Harvest Logging:** Specialized flow to link a new Harvest Batch to a specific Planting Event (inheriting location/history).
*   **Batch Operations:**
    *   **Split:** UI to divide a large batch into smaller units.
    *   **Merge:** UI to combine multiple source batches into a new lot.
    *   **Production Run:** UI to record a complex transformation (Inputs + Process -> Outputs).

### 3.3 Reporting & Export
*   **OOJ Archive Export:** "One-click audit" feature that zips all entity data into a standardized JSON format.
*   **PDF Labels:** Generates printable QR code labels for batches.
*   **Label Templates:** Visual editor to customize label layout (size, elements, branding).

## 4. API & Integration
*   **RESTful API:** Full CRUD endpoints for all entities at `/api/*`.
*   **Authentication:** Cookie-based auth for frontend, Bearer token support for API clients.
*   **Validation:** Strict validation logic ensures date ordering (production < expiration) and valid state transitions.

## 5. Current UI Structure
*   **Dashboard:** High-level stats, alerts for missing data, and Quick Action buttons.
*   **List Views:** Filterable lists for Batches (Active/All), Items, Events, Locations.
*   **Detail Views:** Deep-dive pages for specific Batches (showing lineage graph) and Events.
