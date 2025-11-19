# Level 2 & 3 Features Guide

## Overview

OriginStack v0.2.0 adds **Level 2 (Process & Event Tracking)** and **Level 3 (Full Provenance)** capabilities to the base Level 1 system.

## Level 2: Process & Event Tracking

### Processes (Recipes/SOPs)

Processes define reusable recipes or standard operating procedures.

#### Create a Process

```bash
curl -X POST http://localhost:8000/actors/my-farm/processes \
  -H "Content-Type: application/json" \
  -d '{
    "id": "proc-pickled-garlic-v1",
    "name": "Pickled Garlic Recipe v1",
    "kind": "recipe",
    "version": "1.0",
    "steps": [
      "Peel garlic cloves",
      "Heat brine to 180°F",
      "Pack jars leaving 1/2 inch headspace",
      "Process in boiling water bath for 10 minutes"
    ]
  }'
```

#### List Processes

```bash
# All processes
curl http://localhost:8000/actors/my-farm/processes

# Filter by kind
curl http://localhost:8000/actors/my-farm/processes?kind=recipe
```

### Advanced Operations

#### Production Run

Record a complete production event with inputs, outputs, and packaging:

```bash
curl -X POST http://localhost:8000/actors/my-farm/operations/production-run \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-prod-2025-001",
    "process_id": "proc-pickled-garlic-v1",
    "inputs": [
      {
        "batch_id": "garlic-raw-2025-01",
        "amount": {"amount": 8, "unit": "kg"}
      }
    ],
    "outputs": [
      {
        "batch_id": "pg-2025-01",
        "item_id": "pickled-garlic",
        "amount": {"amount": 42, "unit": "jar_500ml"}
      }
    ],
    "packaging_materials": [
      {
        "batch_id": "jars-batch-2025-05",
        "amount": {"amount": 42, "unit": "unit"}
      }
    ],
    "location_id": "kitchen-main",
    "performed_by": "Jane Smith",
    "notes": "Successful batch production"
  }'
```

**What happens:**
- Creates the processing event
- Automatically creates output batch(es)
- Records input consumption
- Tracks packaging materials used

#### Split Batch

Divide one batch into multiple smaller batches:

```bash
curl -X POST http://localhost:8000/actors/my-farm/operations/split-batch \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-split-001",
    "source_batch_id": "pg-2025-01",
    "outputs": [
      {
        "batch_id": "pg-2025-01-retail",
        "amount": {"amount": 30, "unit": "jar_500ml"}
      },
      {
        "batch_id": "pg-2025-01-wholesale",
        "amount": {"amount": 12, "unit": "jar_500ml"}
      }
    ],
    "notes": "Split for farmers market (30) and restaurant (12)"
  }'
```

**What happens:**
- Creates split event
- Creates new output batches
- Marks source batch as "depleted"

#### Merge Batches

Combine multiple batches into one:

```bash
curl -X POST http://localhost:8000/actors/my-farm/operations/merge-batches \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-merge-001",
    "source_batch_ids": ["batch-001", "batch-002", "batch-003"],
    "output_batch_id": "batch-consolidated",
    "output_quantity": {"amount": 75, "unit": "kg"},
    "notes": "Consolidated multiple small batches"
  }'
```

**What happens:**
- Creates merge event
- Creates new consolidated batch
- Marks all source batches as "depleted"

#### Dispose Batch

Record disposal of expired, damaged, or waste batches:

```bash
curl -X POST http://localhost:8000/actors/my-farm/operations/dispose-batch \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-dispose-001",
    "batch_id": "pg-2025-01-damaged",
    "reason": "broken during transport",
    "location_id": "compost-area",
    "notes": "2 jars broken, contents composted"
  }'
```

**What happens:**
- Creates disposal event
- Marks batch as "disposed"

### Traceability

#### Get Batch Traceability

View upstream (inputs) and downstream (outputs) for a batch:

```bash
# Both directions
curl http://localhost:8000/actors/my-farm/traceability/batches/pg-2025-01

# Upstream only (what went into this batch)
curl http://localhost:8000/actors/my-farm/traceability/batches/pg-2025-01?direction=upstream

# Downstream only (what came from this batch)
curl http://localhost:8000/actors/my-farm/traceability/batches/pg-2025-01?direction=downstream
```

**Response:**
```json
{
  "batch_id": "pg-2025-01",
  "actor_id": "my-farm",
  "upstream": [
    {
      "batch_id": "garlic-raw-2025-01",
      "item_id": "garlic-raw",
      "amount": {"amount": 8, "unit": "kg"},
      "status": "depleted",
      "event_id": "evt-prod-2025-001"
    }
  ],
  "downstream": [
    {
      "batch_id": "pg-2025-01-retail",
      "item_id": "pickled-garlic",
      "amount": {"amount": 30, "unit": "jar_500ml"},
      "status": "active",
      "event_id": "evt-split-001"
    }
  ],
  "events": [...]
}
```

#### Get Full Traceability Graph

Get a complete tree showing all dependencies:

```bash
curl http://localhost:8000/actors/my-farm/traceability/batches/pg-2025-01/graph
```

**Response (nested tree):**
```json
{
  "batch_id": "pg-2025-01",
  "item_id": "pickled-garlic",
  "status": "depleted",
  "quantity": {"amount": 42, "unit": "jar_500ml"},
  "depth": 0,
  "inputs": [
    {
      "batch": {
        "batch_id": "garlic-raw-2025-01",
        "item_id": "garlic-raw",
        "status": "depleted",
        "depth": 1,
        "inputs": [
          {
            "batch": {
              "batch_id": "seed-garlic-2024",
              "item_id": "garlic-seed",
              "depth": 2,
              "inputs": []
            }
          }
        ]
      },
      "amount": {"amount": 8, "unit": "kg"},
      "event_id": "evt-prod-2025-001"
    }
  ]
}
```

#### Get Item Traceability Summary

Overview of all batches for an item:

```bash
curl http://localhost:8000/actors/my-farm/traceability/items/pickled-garlic/summary
```

## Level 3: Full Provenance

### Locations

Track physical locations with coordinates.

#### Create a Location

```bash
curl -X POST http://localhost:8000/actors/my-farm/locations \
  -H "Content-Type: application/json" \
  -d '{
    "id": "kitchen-main",
    "name": "Main Processing Kitchen",
    "kind": "kitchen",
    "coordinates": {
      "lat": 46.3954,
      "lon": -63.7983
    },
    "address": {
      "street": "123 Farm Road",
      "city": "Summerside",
      "region": "PE",
      "postal_code": "C1N 1A1",
      "country": "CA"
    }
  }'
```

#### List Locations

```bash
# All locations
curl http://localhost:8000/actors/my-farm/locations

# Filter by kind
curl http://localhost:8000/actors/my-farm/locations?kind=field
```

#### Location Types (kind)

Common location kinds:
- `field` - Growing areas
- `bed` - Garden beds
- `kitchen` - Processing kitchens
- `warehouse` - Storage facilities
- `cooler` - Cold storage
- `vehicle` - Transport
- `market` - Sales locations

### Using Locations

Add `location_id` to batches, events, and operations:

```bash
# Create batch at location
curl -X POST http://localhost:8000/actors/my-farm/batches \
  -H "Content-Type: application/json" \
  -d '{
    "id": "batch-001",
    "item_id": "tomatoes",
    "location_id": "field-north",
    "quantity": {"amount": 50, "unit": "kg"}
  }'

# Production run at location
curl -X POST http://localhost:8000/actors/my-farm/operations/production-run \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "location_id": "kitchen-main",
    ...
  }'
```

## Complete Workflow Example

### Scenario: Pickled Garlic Production

```bash
# 1. Create actor
curl -X POST http://localhost:8000/actors \
  -d '{"id":"demo-farm","name":"Demo Farm","kind":"producer"}'

# 2. Create locations
curl -X POST http://localhost:8000/actors/demo-farm/locations \
  -d '{"id":"field-1","name":"Field #1","kind":"field"}'
curl -X POST http://localhost:8000/actors/demo-farm/locations \
  -d '{"id":"kitchen","name":"Processing Kitchen","kind":"kitchen"}'

# 3. Create items
curl -X POST http://localhost:8000/actors/demo-farm/items \
  -d '{"id":"garlic-raw","name":"Fresh Garlic","category":"raw_material","unit":"kg"}'
curl -X POST http://localhost:8000/actors/demo-farm/items \
  -d '{"id":"pickled-garlic","name":"Pickled Garlic 500ml","category":"finished_good","unit":"jar_500ml"}'
curl -X POST http://localhost:8000/actors/demo-farm/items \
  -d '{"id":"glass-jar","name":"Glass Jar 500ml","category":"packaging","unit":"unit"}'

# 4. Create process
curl -X POST http://localhost:8000/actors/demo-farm/processes \
  -d '{"id":"proc-pg-v1","name":"Pickled Garlic v1","kind":"recipe","version":"1.0"}'

# 5. Harvest garlic
curl -X POST http://localhost:8000/actors/demo-farm/batches \
  -d '{"id":"garlic-harvest-001","item_id":"garlic-raw","location_id":"field-1","quantity":{"amount":50,"unit":"kg"},"origin_kind":"harvested"}'

# 6. Receive packaging
curl -X POST http://localhost:8000/actors/demo-farm/batches \
  -d '{"id":"jars-001","item_id":"glass-jar","quantity":{"amount":200,"unit":"unit"},"origin_kind":"received"}'

# 7. Production run
curl -X POST http://localhost:8000/actors/demo-farm/operations/production-run \
  -d '{
    "event_id":"evt-prod-001",
    "process_id":"proc-pg-v1",
    "inputs":[{"batch_id":"garlic-harvest-001","amount":{"amount":8,"unit":"kg"}}],
    "outputs":[{"batch_id":"pg-batch-001","item_id":"pickled-garlic","amount":{"amount":42,"unit":"jar_500ml"}}],
    "packaging_materials":[{"batch_id":"jars-001","amount":{"amount":42,"unit":"unit"}}],
    "location_id":"kitchen",
    "performed_by":"Jane Smith"
  }'

# 8. Split for different markets
curl -X POST http://localhost:8000/actors/demo-farm/operations/split-batch \
  -d '{
    "event_id":"evt-split-001",
    "source_batch_id":"pg-batch-001",
    "outputs":[
      {"batch_id":"pg-retail","amount":{"amount":30,"unit":"jar_500ml"}},
      {"batch_id":"pg-wholesale","amount":{"amount":12,"unit":"jar_500ml"}}
    ]
  }'

# 9. View traceability
curl http://localhost:8000/actors/demo-farm/traceability/batches/pg-retail
curl http://localhost:8000/actors/demo-farm/traceability/batches/pg-retail/graph
```

## API Endpoints Summary

### Level 1 (Base)
- `POST/GET /actors`
- `POST/GET /actors/{id}/items`
- `POST/GET /actors/{id}/batches`
- `POST/GET /actors/{id}/events`

### Level 2 (Process & Event Tracking)
- `POST/GET /actors/{id}/processes`
- `POST /actors/{id}/operations/production-run`
- `POST /actors/{id}/operations/split-batch`
- `POST /actors/{id}/operations/merge-batches`
- `POST /actors/{id}/operations/dispose-batch`
- `GET /actors/{id}/traceability/batches/{id}`
- `GET /actors/{id}/traceability/batches/{id}/graph`
- `GET /actors/{id}/traceability/items/{id}/summary`

### Level 3 (Full Provenance)
- `POST/GET /actors/{id}/locations`

## Next Steps

- Explore the interactive API docs at http://localhost:8000/docs
- Try the complete workflow example above
- Build a frontend UI for these operations
- Add export features (OOJ archives, CSV)
