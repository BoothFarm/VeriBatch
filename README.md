# VeriBatch

**Pass Every Food Safety Inspection with Digital Traceability**

Never worry about recalls or compliance again. VeriBatch helps small producers track every batch from farm to shelf with industry-standard digital records.

## Why Producers Choose VeriBatch

🛡️ **Pass Every Inspection** - Complete digital records ready for FDA, organic, and HACCP auditors  
⚡ **Handle Recalls Fast** - Find all affected products in under 30 seconds  
🔓 **Own Your Data** - Export everything anytime in industry-standard Open Origin JSON format  
🎯 **Built for Small Scale** - Designed for farms, cottage food, herbalists, and small processors  
📈 **Start Simple, Grow Advanced** - Begin with basic lot tracking, expand to full supply chain traceability

## Features

### Level 1 - Minimal Traceability ✅ COMPLETE
- ✅ Actor management (your farm/business)
- ✅ Item catalog (products, ingredients, packaging)
- ✅ Batch tracking with lot codes
- ✅ Basic inventory
- ✅ Event logging
- ✅ OOJ JSON export

### Level 2 - Process & Event Tracking ✅ COMPLETE
- ✅ Production recipes/processes
- ✅ Event logging with input/output tracking
- ✅ Production run operations
- ✅ Batch split operations
- ✅ Batch merge operations
- ✅ Disposal tracking
- ✅ Upstream/downstream traceability
- ✅ Full traceability graphs

### Level 3 - Full Provenance ✅ COMPLETE
- ✅ Location management with coordinates
- ✅ Geographic tracking
- ⏳ Cross-actor relationships (ready, not implemented)
- ⏳ Advanced reporting
- ⏳ External data integration

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+

### Installation

```bash
# Clone the repository
cd VeriBatch

# Run setup script (creates database, installs dependencies)
./setup.sh

# Start the backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Architecture

```
┌─────────────┐
│   Frontend  │  (React/HTMX - coming soon)
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │  REST API - OOJ compliant
└──────┬──────┘
       │
┌──────▼──────┐
│ PostgreSQL  │  JSONB storage + indexed columns
└─────────────┘
       │
┌──────▼──────┐
│ OOJ Client  │  Open Origin JSON entities
└─────────────┘
```

### Data Storage Pattern

Hybrid approach for best of both worlds:
- **Indexed columns** for fast queries (actor_id, status, dates, etc.)
- **JSONB document** for complete OOJ compliance
- **Easy export** to pure OOJ JSON archives

## API Examples

### Create an Actor (Your Farm)

```bash
curl -X POST http://localhost:8000/actors \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-farm",
    "name": "My Farm",
    "kind": "producer",
    "contacts": {"email": "hello@myfarm.com"}
  }'
```

### Create an Item

```bash
curl -X POST http://localhost:8000/actors/my-farm/items \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tomatoes",
    "name": "Roma Tomatoes",
    "category": "raw_material",
    "unit": "kg"
  }'
```

### Create a Batch

```bash
curl -X POST http://localhost:8000/actors/my-farm/batches \
  -H "Content-Type: application/json" \
  -d '{
    "id": "batch-2025-01",
    "item_id": "tomatoes",
    "quantity": {"amount": 25, "unit": "kg"},
    "production_date": "2025-01-15",
    "status": "active"
  }'
```

### List All Batches

```bash
curl http://localhost:8000/actors/my-farm/batches
```

## Project Structure

```
VeriBatch/
├── backend/
│   ├── app/
│   │   ├── api/          # API route handlers
│   │   ├── db/           # Database configuration
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── frontend/             # Coming soon
├── draft_spec.md         # Product specification
├── Open_Origin_JSON_v0.5.md
└── setup.sh
```

## Development

### Run Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Database Migrations

```bash
# Coming soon - Alembic migrations
```

## OOJ Compliance

VeriBatch implements **Open Origin JSON v0.5**:
- All entities include proper `schema`, `type`, `id` fields
- Timestamps in ISO 8601 format
- Extensible with custom fields (forward-compatible)
- Full export to OOJ archives

## Roadmap

- [x] Backend API with Actor, Item, Batch, Event entities
- [x] PostgreSQL storage with JSONB
- [x] OOJ v0.5 compliance
- [x] Process/Recipe management
- [x] Event tracking with input/output
- [x] Production run operations
- [x] Split/Merge/Dispose operations
- [x] Traceability graphs (upstream/downstream)
- [x] Location management with coordinates
- [ ] Frontend UI (React or HTMX)
- [ ] Label generation
- [ ] OOJ archive export (ZIP)
- [ ] CSV export
- [ ] Multi-user authentication
- [ ] Cross-actor link entities
- [ ] Production deployment guide

## Contributing

This is an open source project. Contributions welcome!

## License

TBD

## Learn More

- [Open Origin JSON Spec](./Open_Origin_JSON_v0.5.md)
- [Product Specification](./draft_spec.md)
- [Backend README](./backend/README.md)
- [Level 2 & 3 Features Guide](./LEVEL_2_3_GUIDE.md)
- [Getting Started](./GETTING_STARTED.md)

---

**Built with ❤️ for small producers who care about transparency and traceability.**
