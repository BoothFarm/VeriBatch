# VeriBatch Backend

FastAPI backend for VeriBatch - an Open Origin JSON (OOJ) compliant ERP system for small producers.

## Quick Start

### 1. Set up PostgreSQL

```bash
# Install PostgreSQL if needed
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE originstack;
CREATE USER originstack WITH PASSWORD 'originstack';
GRANT ALL PRIVILEGES ON DATABASE originstack TO originstack;
\q
```

### 2. Install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Actors
- `POST /actors` - Create actor
- `GET /actors` - List all actors
- `GET /actors/{actor_id}` - Get specific actor

### Items
- `POST /actors/{actor_id}/items` - Create item
- `GET /actors/{actor_id}/items` - List items
- `GET /actors/{actor_id}/items/{item_id}` - Get specific item

### Batches
- `POST /actors/{actor_id}/batches` - Create batch
- `GET /actors/{actor_id}/batches` - List batches (filter by status, item_id)
- `GET /actors/{actor_id}/batches/{batch_id}` - Get specific batch
- `PATCH /actors/{actor_id}/batches/{batch_id}/status` - Update batch status

### Events
- `POST /actors/{actor_id}/events` - Create event
- `GET /actors/{actor_id}/events` - List events (filter by event_type)
- `GET /actors/{actor_id}/events/{event_id}` - Get specific event

## Example Usage

### Create an Actor

```bash
curl -X POST http://localhost:8000/actors \
  -H "Content-Type: application/json" \
  -d '{
    "id": "bfe",
    "name": "Booth Farm Enterprises",
    "kind": "producer",
    "contacts": {
      "email": "info@boothfarm.ca"
    }
  }'
```

### Create an Item

```bash
curl -X POST http://localhost:8000/actors/bfe/items \
  -H "Content-Type: application/json" \
  -d '{
    "id": "garlic-raw",
    "name": "Fresh Garlic",
    "category": "raw_material",
    "unit": "kg"
  }'
```

### Create a Batch

```bash
curl -X POST http://localhost:8000/actors/bfe/batches \
  -H "Content-Type: application/json" \
  -d '{
    "id": "batch-2025-01",
    "item_id": "garlic-raw",
    "quantity": {
      "amount": 50,
      "unit": "kg"
    },
    "production_date": "2025-01-15",
    "status": "active"
  }'
```

## Architecture

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database access
- **PostgreSQL** - Database with JSONB support
- **OOJ Client** - Open Origin JSON entities and validation

### Database Design

Each entity is stored with:
- Indexed columns for fast queries (actor_id, status, dates, etc.)
- Full OOJ document in JSONB column for complete data preservation
- Automatic timestamps (created_at, updated_at)

This hybrid approach provides:
- Fast filtering on key fields
- Complete OOJ compliance
- Easy export to pure OOJ JSON
