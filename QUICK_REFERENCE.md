# VeriBatch Quick Reference

## Start the Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## API Endpoints

Base URL: `http://localhost:8000`

### Actors
```bash
POST   /actors                    # Create actor
GET    /actors                    # List actors
GET    /actors/{id}               # Get actor
```

### Items
```bash
POST   /actors/{id}/items         # Create item
GET    /actors/{id}/items         # List items
GET    /actors/{id}/items/{id}    # Get item
```

### Batches
```bash
POST   /actors/{id}/batches       # Create batch
GET    /actors/{id}/batches       # List batches
GET    /actors/{id}/batches/{id}  # Get batch
PATCH  /actors/{id}/batches/{id}/status  # Update status
```

### Events
```bash
POST   /actors/{id}/events        # Create event
GET    /actors/{id}/events        # List events
GET    /actors/{id}/events/{id}   # Get event
```

### Processes (Level 2)
```bash
POST   /actors/{id}/processes     # Create process/recipe
GET    /actors/{id}/processes     # List processes
GET    /actors/{id}/processes/{id} # Get process
PUT    /actors/{id}/processes/{id} # Update process
```

### Operations (Level 2)
```bash
POST   /actors/{id}/operations/production-run  # Production run
POST   /actors/{id}/operations/split-batch     # Split batch
POST   /actors/{id}/operations/merge-batches   # Merge batches
POST   /actors/{id}/operations/dispose-batch   # Dispose batch
```

### Traceability (Level 2)
```bash
GET    /actors/{id}/traceability/batches/{id}       # Batch trace
GET    /actors/{id}/traceability/batches/{id}/graph # Full graph
GET    /actors/{id}/traceability/items/{id}/summary # Item summary
```

### Locations (Level 3)
```bash
POST   /actors/{id}/locations     # Create location
GET    /actors/{id}/locations     # List locations
GET    /actors/{id}/locations/{id} # Get location
```

## Example Workflow

```bash
# 1. Create actor
curl -X POST http://localhost:8000/api/actors \
  -H "Content-Type: application/json" \
  -d '{"id":"farm1","name":"My Farm","kind":"producer"}'

# 2. Create item
curl -X POST http://localhost:8000/api/actors/farm1/items \
  -H "Content-Type: application/json" \
  -d '{"id":"tomatoes","name":"Tomatoes","category":"raw_material","unit":"kg"}'

# 3. Create batch
curl -X POST http://localhost:8000/api/actors/farm1/batches \
  -H "Content-Type: application/json" \
  -d '{"id":"batch-001","item_id":"tomatoes","quantity":{"amount":50,"unit":"kg"},"production_date":"2025-01-15"}'

# 4. List batches
curl http://localhost:8000/api/actors/farm1/batches
```

## OOJ Required Fields

### Actor
- `id`, `name`

### Item
- `id`, `actor_id`, `name`

### Batch
- `id`, `actor_id`, `item_id`

### Event
- `id`, `actor_id`, `timestamp`, `event_type`

## Common Status Values

- `active` - Available for use
- `depleted` - Fully consumed
- `quarantined` - Held pending investigation
- `recalled` - Recalled from market
- `expired` - Past expiration date
- `disposed` - Discarded as waste

## Interactive Docs

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Troubleshooting

### Can't connect to database
```bash
sudo systemctl status postgresql
psql -U originstack -d originstack -h localhost
```

### Import errors
```bash
# Check ooj_client exists
ls ../OpenOriginJSON/ooj_client
```

### Port in use
```bash
uvicorn app.main:app --reload --port 8001
```
