# OriginStack

**Open Origin JSON ERP for Small Producers**

A SaaS system for small producers (farms + cottage food) where everything — inventory, production, batch tracking, labels, compliance — is stored and exposed as **Open Origin JSON (OOJ) v0.5**.

## What Makes OriginStack Special

✨ **OOJ Native** - Every object is Open Origin JSON v0.5 compliant out of the box  
📦 **Never Locked In** - Export all your data as clean OOJ archives anytime  
🎯 **Built for Small Producers** - Designed for farms, cottage food, herbalists, fermenters  
📈 **Incremental Adoption** - Start simple (Level 1), grow into full traceability (Level 2/3)

## Features

### Level 1 - Minimal Traceability (v1)
- ✅ Actor management (your farm/business)
- ✅ Item catalog (products, ingredients, packaging)
- ✅ Batch tracking with lot codes
- ✅ Basic inventory
- ✅ OOJ JSON export

### Level 2 - Process & Event Tracking (Planned)
- ⏳ Production recipes/processes
- ⏳ Event logging (harvest, processing, packaging)
- ⏳ Input/output tracking
- ⏳ Traceability graphs

### Level 3 - Full Provenance (Future)
- ⏳ Location management with coordinates
- ⏳ Cross-actor relationships
- ⏳ Advanced reporting
- ⏳ External data integration

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+

### Installation

```bash
# Clone the repository
cd OriginStack

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
OriginStack/
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

OriginStack implements **Open Origin JSON v0.5**:
- All entities include proper `schema`, `type`, `id` fields
- Timestamps in ISO 8601 format
- Extensible with custom fields (forward-compatible)
- Full export to OOJ archives

## Roadmap

- [x] Backend API with Actor, Item, Batch, Event entities
- [x] PostgreSQL storage with JSONB
- [x] OOJ v0.5 compliance
- [ ] Frontend UI (React or HTMX)
- [ ] Process/Recipe management
- [ ] Event tracking with input/output
- [ ] Traceability graphs
- [ ] Label generation
- [ ] CSV/JSON export
- [ ] Multi-user authentication
- [ ] Production deployment guide

## Contributing

This is an open source project. Contributions welcome!

## License

TBD

## Learn More

- [Open Origin JSON Spec](./Open_Origin_JSON_v0.5.md)
- [Product Specification](./draft_spec.md)
- [Backend README](./backend/README.md)

---

**Built with ❤️ for small producers who care about transparency and traceability.**
