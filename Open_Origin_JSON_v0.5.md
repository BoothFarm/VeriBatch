# Open Origin JSON (OOJ) — Version 0.5 Specification

**Version:** 0.5  
**Date:** January 2025  
**Status:** Draft

A lightweight, incremental, interoperable traceability data format for micro‑producers, processors, and small supply chains.

## 1. Introduction

Open Origin JSON (OOJ) is a human‑friendly JSON standard for representing where products come from, how they were transformed, and how batches relate across the simplest or most complex supply chains. It is designed to support:

- **Micro‑farms** tracking harvest to market  
- **Cottage food producers** managing recipes and batches  
- **Herbalists, fermenters, roasters, canners** documenting processes  
- **Small processors and co‑packers** coordinating production  
- **Distributed or multi‑actor supply chains** sharing provenance  
- **Local markets and retailers** verifying origins  
- **Regulatory and audit workflows** maintaining compliance

OOJ is built around three pillars:

1. **Simplicity** — Producers can implement Level 1 by filling out three entities: actor, item, batch.  
2. **Incrementality** — More detail (processes, events, locations) is optional and layered.  
3. **Interoperability** — IDs are namespaced by actor; unknown fields and types are explicitly allowed.

### What's New in v0.5

Version 0.5 adds:

- **Timestamp tracking**: `created_at` and `updated_at` on all entities for audit trails
- **Attachment validation**: Better specification of attachment types and custom extensions
- **Cross-actor references**: Clarified model for multi-actor supply chains
- **Python reference implementation**: Complete `ooj_client` library with validation

---

## 2. Schema Identifier

Every OOJ document MUST contain a `schema` field in the form:

```json
"schema": "open-origin-json/0.5"
```

All valid OOJ schema strings MUST begin with:

```
open-origin-json/
```

**Version Compatibility:**

- Future minor versions (0.6, 0.7) MUST remain backwards compatible for Level 1 & Level 2 fields  
- Breaking changes will increment the major version (1.x)
- Parsers MUST accept documents with schema versions they understand
- Parsers SHOULD warn (but not reject) documents with newer minor versions

**Python Implementation:**

```python
SCHEMA_VERSION = "open-origin-json/0.5"
```

---

## 3. Levels of Adoption

OOJ defines 3 adoption levels so implementers can grow gradually.

### **Level 1 — Minimal Traceability (Required)**  
Required entities:
- `actor`
- `item`
- `batch`

Minimum required fields:
- Actor: `schema`, `type`, `id`, `name`  
- Item: `schema`, `type`, `id`, `actor_id`, `name`  
- Batch: `schema`, `type`, `id`, `actor_id`, `item_id`

Level 1 systems MUST:
- accept unknown fields  
- ignore unknown fields  
- read Level 2/3 JSON without failing validation  

---

### **Level 2 — Process & Event Tracking**

Adds:
- `process`  
- `event`  

Implementations SHOULD support lineage reconstruction via event `inputs` and `outputs`.

---

### **Level 3 — Full Provenance**

Adds:
- `location`
- `link`
- geocoordinates  
- environmental context  
- cross‑actor references  
- advanced metadata

Designed for regulators, researchers, multi‑actor supply chains.

---

## 4. Common Fields (All Entities)

All OOJ entities inherit the following:

| Field        | Type   | Required | Description |
|--------------|--------|----------|-------------|
| `schema`     | string | Yes      | OOJ schema string (e.g., `"open-origin-json/0.4"`) |
| `type`       | string | Yes      | Entity type (actor, item, batch, event…) |
| `id`         | string | Yes      | ID unique in the actor's namespace |
| `actor_id`   | string | No (only omitted for actor) | Namespace owner |
| `created_at` | string | No       | ISO8601 timestamp |
| `updated_at` | string | No       | ISO8601 timestamp |

Actors do NOT contain `actor_id`.

---

## 5. ID Namespacing Model

Each actor maintains local unique IDs.  
A globally unique reference is the pair:

```
(actor_id, id)
```

References inside the same actor MAY omit `actor_id`.  
References across actors MAY include an explicit `actor_id`.

Example internal reference:

```json
{ "batch_id": "b1" }
```

Example cross‑actor reference:

```json
{ "batch_id": "supplier-lot-10", "actor_id": "supplier42" }
```

Actor IDs SHOULD be globally unique strings such as:
- domain names (`"boothfamilyfarm.ca"`)  
- reverse DNS (`"ca.boothfamilyfarm"`)  
- UUIDs  

---

## 6. Entity Definitions

OOJ defines seven entity types:

```
actor
location
item
batch
process
event
link
```

Unknown entity types MUST NOT cause failure and MUST be ignored or passed through.

---

## 6.1 Actor

Represents an organization or person participating in the supply chain.

**Level:** 1 (Required)

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"actor"`
- `id` — Unique identifier for this actor (SHOULD be globally unique)
- `name` — Human-readable name

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | string | Type of actor: `"producer"`, `"processor"`, `"distributor"`, `"retailer"`, `"lab"` |
| `contacts` | object | Contact information (e.g., `{"email": "...", "phone": "..."}`) |
| `address` | object | Physical address with keys: `street`, `city`, `region`, `postal_code`, `country` |
| `certifications` | array | List of certification strings (e.g., `["organic", "kosher", "halal"]`) |
| `external_ids` | object | External system identifiers (see External IDs section) |
| `created_at` | string | ISO 8601 timestamp when record was created |
| `updated_at` | string | ISO 8601 timestamp when record was last updated |

### Example

```json
{
  "schema": "open-origin-json/0.5",
  "type": "actor",
  "id": "bfe",
  "name": "Booth Farm Enterprises Ltd.",
  "kind": "producer",
  "contacts": { 
    "email": "info@boothfamilyfarm.ca",
    "phone": "+1-555-0100"
  },
  "address": {
    "street": "123 Farm Road",
    "city": "Summerside",
    "region": "PE",
    "postal_code": "C1N 1A1",
    "country": "CA"
  },
  "certifications": ["organic", "local_food"],
  "external_ids": {
    "gln": "1234567890123"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Actor ID Best Practices

Actor IDs SHOULD be globally unique. Recommended formats:

- **Domain names**: `"boothfamilyfarm.ca"`
- **Reverse DNS**: `"ca.boothfamilyfarm"`  
- **UUIDs**: `"550e8400-e29b-41d4-a716-446655440000"`
- **Short codes**: `"bfe"` (only if coordinated within your ecosystem)

---

## 6.2 Location

Represents a physical or logical place where production, storage, or handling occurs.

**Level:** 3

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"location"`
- `id` — Unique within actor's namespace
- `actor_id` — ID of the actor who owns this location
- `name` — Human-readable name

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | string | Type: `"field"`, `"bed"`, `"kitchen"`, `"warehouse"`, `"cooler"`, `"vehicle"`, etc. |
| `coordinates` | object | Geographic coordinates: `{"lat": <number>, "lon": <number>}` |
| `address` | object | Physical address (same structure as Actor) |
| `external_ids` | object | External system identifiers |
| `created_at` | string | ISO 8601 timestamp when created |
| `updated_at` | string | ISO 8601 timestamp when last updated |

### Example

```json
{
  "schema": "open-origin-json/0.5",
  "type": "location",
  "id": "kitchen-main",
  "actor_id": "bfe",
  "name": "Main Kitchen",
  "kind": "kitchen",
  "coordinates": { 
    "lat": 46.3954, 
    "lon": -63.7983 
  },
  "created_at": "2025-01-10T08:00:00Z"
}
```

---

## 6.3 Item

Represents types of goods: raw materials, ingredients, packaging, finished goods.

**Level:** 1 (Required)

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"item"`
- `id` — Unique within actor's namespace
- `actor_id` — ID of the actor who owns this item definition
- `name` — Human-readable name

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | `"raw_material"`, `"ingredient"`, `"packaging"`, `"finished_good"`, `"intermediate"` |
| `unit` | string | Default unit of measure (e.g., `"kg"`, `"L"`, `"jar_500ml"`, `"unit"`) |
| `description` | string | Additional description or notes |
| `external_ids` | object | External system identifiers (GTIN, SKU, etc.) |
| `created_at` | string | ISO 8601 timestamp when created |
| `updated_at` | string | ISO 8601 timestamp when last updated |

### Examples

**Raw Material:**

```json
{
  "schema": "open-origin-json/0.5",
  "type": "item",
  "id": "garlic-raw",
  "actor_id": "bfe",
  "name": "Fresh Garlic",
  "category": "raw_material",
  "unit": "kg",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Finished Product:**

```json
{
  "schema": "open-origin-json/0.5",
  "type": "item",
  "id": "pickled-garlic-jar",
  "actor_id": "bfe",
  "name": "Pickled Garlic (500ml)",
  "category": "finished_good",
  "unit": "jar_500ml",
  "external_ids": {
    "gtin": "01234567890128",
    "sku": "BFE-PG-500"
  },
  "created_at": "2025-01-05T12:00:00Z"
}
```

**Packaging Material:**

```json
{
  "schema": "open-origin-json/0.5",
  "type": "item",
  "id": "glass-jar-500ml",
  "actor_id": "bfe",
  "name": "Glass Jar 500ml with Lid",
  "category": "packaging",
  "unit": "unit"
}
```

---

## 6.4 Batch

Represents the smallest traceable unit of an item. Batches are the core of traceability.

**Level:** 1 (Required)

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"batch"`
- `id` — Unique within actor's namespace (often a lot code)
- `actor_id` — ID of the actor who owns this batch
- `item_id` — Reference to the item type

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `location_id` | string | Current or production location |
| `quantity` | object | Amount object: `{"amount": <number>, "unit": "<string>"}` |
| `status` | string | Lifecycle status (see Status Values below) |
| `origin_kind` | string | How batch was created: `"harvested"`, `"received"`, `"transformed"`, `"purchased"` |
| `production_date` | string | ISO 8601 date when batch was produced |
| `expiration_date` | string | ISO 8601 date when batch expires |
| `best_before_date` | string | ISO 8601 date for best quality |
| `external_ids` | object | External system identifiers (lot codes, etc.) |
| `attachments` | array | Photos, certificates, test results (see Attachments) |
| `created_at` | string | ISO 8601 timestamp when record created |
| `updated_at` | string | ISO 8601 timestamp when record updated |

### Status Values

| Status | Description |
|--------|-------------|
| `active` | **Default** — Batch is available for use |
| `depleted` | Batch has been fully consumed (zero remaining) |
| `quarantined` | Batch is held pending investigation |
| `recalled` | Batch has been recalled |
| `expired` | Batch has passed expiration date |
| `disposed` | Batch has been disposed of as waste |

**Note:** If `status` is not present, implementations SHOULD treat the batch as `"active"`.

### Example — Basic Batch

```json
{
  "schema": "open-origin-json/0.5",
  "type": "batch",
  "id": "pg-2025-01",
  "actor_id": "bfe",
  "item_id": "pickled-garlic-jar",
  "quantity": { 
    "amount": 42, 
    "unit": "jar_500ml" 
  },
  "status": "active",
  "production_date": "2025-07-20"
}
```

### Example — Complete Batch with Metadata

```json
{
  "schema": "open-origin-json/0.5",
  "type": "batch",
  "id": "pg-2025-01",
  "actor_id": "bfe",
  "item_id": "pickled-garlic-jar",
  "location_id": "kitchen-main",
  "quantity": { 
    "amount": 42, 
    "unit": "jar_500ml" 
  },
  "status": "active",
  "origin_kind": "transformed",
  "production_date": "2025-07-20",
  "best_before_date": "2027-07-20",
  "external_ids": {
    "lot_code": "PG-072025-01"
  },
  "attachments": [
    {
      "type": "photo",
      "url": "https://storage.boothfarm.ca/batches/pg-2025-01.jpg",
      "description": "Finished product photo",
      "mime_type": "image/jpeg"
    },
    {
      "type": "test_result",
      "url": "https://storage.boothfarm.ca/tests/pg-2025-01-micro.pdf",
      "description": "Microbial test results - PASS",
      "mime_type": "application/pdf"
    }
  ],
  "created_at": "2025-07-20T14:00:00-03:00",
  "updated_at": "2025-07-20T14:00:00-03:00"
}
```

### Status Management Best Practices

**Status vs Events:**

- `status` is a cached state for quick understanding of batch lifecycle
- Event history (via `event` entities) is the authoritative audit trail
- After a `disposal` event consuming remaining quantity → set `status` to `"disposed"`
- After a `split` or `merge` → update input batch status to `"depleted"` when fully consumed
- Consumers SHOULD be prepared for inconsistencies and MAY recompute status from events

---

## 6.5 Process

Defines a recipe, procedure, or standard operating procedure that can be referenced by events.

**Level:** 2

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"process"`
- `id` — Unique within actor's namespace
- `actor_id` — ID of the actor who owns this process
- `name` — Human-readable name

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | string | Type: `"recipe"`, `"harvest"`, `"packaging"`, `"cleaning"`, `"testing"` |
| `version` | string | Version identifier for process evolution |
| `steps` | array | Array of step descriptions (strings) |
| `inputs` | array | Expected input specifications (informational, not validated) |
| `outputs` | array | Expected output specifications (informational) |
| `attachments` | array | Recipe PDFs, SOPs, training videos, etc. |
| `created_at` | string | ISO 8601 timestamp when created |
| `updated_at` | string | ISO 8601 timestamp when last updated |

### Example

```json
{
  "schema": "open-origin-json/0.5",
  "type": "process",
  "id": "proc-pickled-garlic-v1",
  "actor_id": "bfe",
  "name": "Pickled Garlic Recipe v1",
  "kind": "recipe",
  "version": "1.2",
  "steps": [
    "Peel garlic cloves",
    "Heat brine to 180°F",
    "Pack jars leaving 1/2 inch headspace",
    "Process in boiling water bath for 10 minutes"
  ],
  "attachments": [
    {
      "type": "document",
      "url": "https://storage.boothfarm.ca/processes/pickled-garlic-recipe.pdf",
      "description": "Full recipe document",
      "mime_type": "application/pdf"
    }
  ],
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

### Process Versioning

Process versions allow tracking recipe evolution over time:

- Use semantic versioning (e.g., `"1.0"`, `"1.1"`, `"2.0"`)
- Create new process IDs for major changes (e.g., `proc-pickled-garlic-v2`)
- Use `version` field for minor revisions within same process ID

---

## 6.6 Event

Represents a timestamped action that transforms, moves, or changes the status of goods. Events are the backbone of provenance tracking.

**Level:** 2

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"event"`
- `id` — Unique within actor's namespace
- `actor_id` — ID of the actor who performed this event
- `timestamp` — ISO 8601 timestamp with timezone (MUST include timezone)
- `event_type` — One of the canonical types or custom `x-*` type

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `location_id` | string | Where event occurred |
| `process_id` | string | Process/recipe used (if applicable) |
| `inputs` | array | Input batches consumed (see I/O Objects below) |
| `outputs` | array | Output batches produced |
| `packaging_materials` | array | Packaging consumed (same structure as inputs) |
| `notes` | string | Free-form notes |
| `performed_by` | string | Person or role who performed the event |
| `external_ids` | object | External system identifiers |
| `attachments` | array | Photos, documents, etc. |
| `created_at` | string | ISO 8601 timestamp when record created |
| `updated_at` | string | ISO 8601 timestamp when record updated |

### Canonical Event Types

| Event Type | Description | Typical Pattern |
|------------|-------------|-----------------|
| `harvest` | Gathering raw materials | No inputs → batch outputs |
| `processing` | Transforming inputs to outputs | Input batches → output batches |
| `packaging` | Putting product into containers | Input batch → packaged batch + packaging materials |
| `receiving` | Accepting goods from supplier | No inputs → output batches |
| `shipping` | Sending goods out | Input batches → (outputs optional) |
| `storage_move` | Moving between locations | Input batch → output batch (may be same ID) |
| `quality_check` | Inspection or testing | Input = output; may change status |
| `split` | Dividing one batch into multiple | 1 input → N outputs |
| `merge` | Combining batches into one | N inputs → 1 output |
| `disposal` | Discarding waste/expired product | Input batches → no outputs |

### Custom Event Types

Custom event types MUST be prefixed with `x-`:

```
x-fermentation_start
x-labeling
x-aging_transfer
x-field_rotation
```

Consumers MUST accept unknown event types without failing.

### Input/Output Objects

Each entry in `inputs`, `outputs`, or `packaging_materials` is an object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batch_id` | string | Yes | Referenced batch ID |
| `amount` | object | No | Quantity: `{"amount": <number>, "unit": "<string>"}` |
| `actor_id` | string | No | Actor ID for cross-actor references; defaults to event's `actor_id` |

### Example — Processing Event

```json
{
  "schema": "open-origin-json/0.5",
  "type": "event",
  "id": "evt-2025-07-20-run1",
  "actor_id": "bfe",
  "timestamp": "2025-07-20T13:00:00-03:00",
  "event_type": "processing",
  "location_id": "kitchen-main",
  "process_id": "proc-pickled-garlic-v1",
  "inputs": [
    {
      "batch_id": "garlic-raw-2025-01",
      "amount": { "amount": 8, "unit": "kg" }
    }
  ],
  "outputs": [
    {
      "batch_id": "pg-2025-01",
      "amount": { "amount": 42, "unit": "jar_500ml" }
    }
  ],
  "packaging_materials": [
    {
      "batch_id": "jars-batch-2025-05",
      "amount": { "amount": 42, "unit": "unit" }
    }
  ],
  "performed_by": "Jane Smith",
  "attachments": [
    {
      "type": "photo",
      "url": "https://storage.boothfarm.ca/events/evt-2025-07-20-setup.jpg",
      "description": "Kitchen setup before processing"
    }
  ],
  "created_at": "2025-07-20T13:00:00-03:00"
}
```

### Example — Split Event

```json
{
  "schema": "open-origin-json/0.5",
  "type": "event",
  "id": "evt-split-2025-07-25",
  "actor_id": "bfe",
  "timestamp": "2025-07-25T09:00:00-03:00",
  "event_type": "split",
  "location_id": "kitchen-main",
  "inputs": [
    {
      "batch_id": "pg-2025-01",
      "amount": { "amount": 42, "unit": "jar_500ml" }
    }
  ],
  "outputs": [
    {
      "batch_id": "pg-2025-01-retail",
      "amount": { "amount": 30, "unit": "jar_500ml" }
    },
    {
      "batch_id": "pg-2025-01-wholesale",
      "amount": { "amount": 12, "unit": "jar_500ml" }
    }
  ],
  "notes": "Split for farmers market (30) and restaurant wholesale (12)"
}
```

### Example — Disposal Event

```json
{
  "schema": "open-origin-json/0.5",
  "type": "event",
  "id": "evt-disposal-2025-08-01",
  "actor_id": "bfe",
  "timestamp": "2025-08-01T16:30:00-03:00",
  "event_type": "disposal",
  "location_id": "compost-area",
  "inputs": [
    {
      "batch_id": "pg-2025-01-retail",
      "amount": { "amount": 2, "unit": "jar_500ml" }
    }
  ],
  "notes": "2 jars broken during transport. Contents composted, glass recycled.",
  "attachments": [
    {
      "type": "photo",
      "url": "https://storage.boothfarm.ca/disposal/broken-jars-2025-08-01.jpg",
      "description": "Photo of damaged jars"
    }
  ]
}
```

### Example — Cross-Actor Event

```json
{
  "schema": "open-origin-json/0.5",
  "type": "event",
  "id": "evt-receive-supplier-001",
  "actor_id": "bfe",
  "timestamp": "2025-07-15T10:00:00-03:00",
  "event_type": "receiving",
  "inputs": [
    {
      "batch_id": "supplier-garlic-lot-42",
      "actor_id": "supplier-farm-xyz",
      "amount": { "amount": 50, "unit": "kg" }
    }
  ],
  "outputs": [
    {
      "batch_id": "garlic-raw-2025-01",
      "amount": { "amount": 50, "unit": "kg" }
    }
  ],
  "notes": "Received organic garlic from Supplier XYZ"
}
```

---

## 6.7 Link

Explicit relationship edges between entities or batches. Useful for complex supply chains and research applications.

**Level:** 3

### Required Fields

- `schema` — OOJ version string
- `type` — Must be `"link"`
- `id` — Unique within actor's namespace
- `actor_id` — ID of the actor who created this link
- `kind` — Relationship type (see below)

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `from_batch_id` | string | Source batch ID |
| `to_batch_id` | string | Destination batch ID |
| `from_entity_id` | string | Source entity ID (for non-batch links) |
| `to_entity_id` | string | Destination entity ID |
| `from_actor_id` | string | Source actor (for cross-actor links) |
| `to_actor_id` | string | Destination actor |
| `metadata` | object | Additional key-value data about the relationship |
| `created_at` | string | ISO 8601 timestamp when created |
| `updated_at` | string | ISO 8601 timestamp when updated |

### Common Link Kinds

- `"input_to_output"` — Explicit lineage edge
- `"parent_child"` — Hierarchical relationship
- `"reference"` — General reference
- `"derived_from"` — Product derivation
- `"supplied_by"` — Supply chain relationship

### Example

```json
{
  "schema": "open-origin-json/0.5",
  "type": "link",
  "id": "lnk-raw-to-pickled",
  "actor_id": "bfe",
  "kind": "input_to_output",
  "from_batch_id": "garlic-raw-2025-01",
  "to_batch_id": "pg-2025-01",
  "metadata": {
    "conversion_ratio": 0.19,
    "notes": "8kg raw garlic yields approximately 42 x 500ml jars"
  },
  "created_at": "2025-07-20T14:00:00Z"
}
```

### When to Use Links

Links are optional; most lineage can be expressed via Events. Use links when:

- Building explicit graph structures for analysis
- Representing relationships not captured by events
- Cross-referencing between actors in complex supply chains
- Creating multi-level hierarchies (e.g., pallet → case → unit)

---

## 7. Attachments

Attachments provide links to photos, documents, certificates, test results, videos, etc.

### Fields
- `type` (canonical or `"x-*"` extension)  
- `url` (HTTPS recommended)  
- `mime_type`  
- `hash` (SHA‑256 recommended)  
- `description`  
- `created_at`

Consumers MAY verify hashes but MUST NOT reject documents solely because of hash mismatch.

---

## 8. External IDs

OOJ supports linking entities to external systems.

Example:

```json
{
  "external_ids": {
    "gtin": "00123456789012",
    "sku": "BFE-PG-500"
  }
}
```

Common keys include:
- `gtin`
- `gln`
- `sscc`
- `fda_ffr`
- `organic_ca`
- `lot_code`
- `sku`

---

## 9. Quantities

Quantities follow:

```json
{ "amount": 10, "unit": "kg" }
```

Units:
- MAY be actor-defined  
- SHOULD map to internal semantics  
- SHOULD use SI units when appropriate

OOJ does not standardize unit semantics in v0.4.

---

## 10. Extension Model

OOJ explicitly supports forward-compatible extensibility.

### Allowed Extensions

- Unknown entity types  
- Unknown event types (`x-*`)  
- Unknown attachment types (`x-*`)  
- Custom top-level fields beginning with `"x_"`  
- Custom nested fields anywhere in JSON  

Consumers MUST:
- preserve unknown fields  
- ignore unknown fields  
- avoid rejecting documents containing them  

---

## 11. Validity & Backwards Compatibility

OOJ v0.4 is:

- 100% backward compatible with v0.3 at Level 1 & Level 2  
- Parsers MUST accept `open-origin-json/0.x` where x ≤ current minor version  
- Parsers SHOULD NOT reject unknown fields or types  

---

## 12. JSON Schema (Informative)

A simplified Batch JSON Schema fragment:

```json
{
  "$id": "https://openorigin.dev/ooj/0.4/batch.schema.json",
  "type": "object",
  "properties": {
    "schema": { "type": "string", "pattern": "^open-origin-json/0\.4$" },
    "type": { "const": "batch" },
    "id": { "type": "string" },
    "actor_id": { "type": "string" },
    "item_id": { "type": "string" },
    "quantity": {
      "type": "object",
      "properties": {
        "amount": { "type": "number" },
        "unit": { "type": "string" }
      }
    }
  },
  "required": ["schema", "type", "id", "actor_id", "item_id"],
  "additionalProperties": true
}
```

OOJ does NOT require strict JSON Schema validation.

---

## 13. Best Practices

### Splits
- One input batch → multiple output batches  
- Set input batch status to `depleted` when consumed  

### Merges
- Multiple input batches → one output batch  
- Outputs inherit applicable metadata (expiry, production date…)  

### Disposal
- Use `event_type: "disposal"`  
- Set batch status → `disposed`  

### Storage Moves
- `inputs` MAY list the batch only  
- `outputs` MAY be omitted  

---

---
## License

This specification is licensed under the [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).

**Copyright © 2025 Booth Farm Enterprises Ltd.**

---

# **End of Specification — OOJ v0.4**
