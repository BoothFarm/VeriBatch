# Getting Started with OriginStack

This guide will help you get OriginStack up and running on your local machine.

## Prerequisites

- **Python 3.8+** - Check with `python3 --version`
- **PostgreSQL 12+** - Check with `psql --version`
- **Git** - For cloning the repository

## Installation Steps

### 1. Verify OpenOriginJSON is Present

OriginStack depends on the `ooj_client` library from OpenOriginJSON:

```bash
# From BoothFarmEnterprises directory
ls OpenOriginJSON/ooj_client
# Should show: __init__.py, entities.py, models.py, serializers.py, validators.py
```

### 2. Set Up PostgreSQL

If PostgreSQL isn't installed:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql
```

Create the database and user:

```bash
sudo -u postgres psql
```

Then run these SQL commands:

```sql
CREATE DATABASE originstack;
CREATE USER originstack WITH PASSWORD 'originstack';
GRANT ALL PRIVILEGES ON DATABASE originstack TO originstack;
\q
```

### 3. Set Up Python Environment

```bash
cd OriginStack/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit if needed (default works for local dev)
nano .env
```

Default `.env` contents:
```
DATABASE_URL=postgresql://originstack:originstack@localhost:5432/originstack
SECRET_KEY=change-this-in-production
```

### 5. Start the Application

```bash
# Make sure you're in backend/ and venv is activated
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 6. Test the API

Open your browser and visit:
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Root**: http://localhost:8000/

Or use curl:

```bash
# Check health
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

## Your First Entities

Let's create a complete workflow: Actor → Item → Batch

### 1. Create an Actor (Your Farm)

```bash
curl -X POST http://localhost:8000/actors \
  -H "Content-Type: application/json" \
  -d '{
    "id": "demo-farm",
    "name": "Demo Farm",
    "kind": "producer",
    "contacts": {
      "email": "demo@farm.com",
      "phone": "+1-555-0100"
    },
    "address": {
      "city": "Farmville",
      "region": "PE",
      "country": "CA"
    }
  }'
```

### 2. Create Items

```bash
# Raw material
curl -X POST http://localhost:8000/actors/demo-farm/items \
  -H "Content-Type: application/json" \
  -d '{
    "id": "garlic-raw",
    "name": "Fresh Garlic",
    "category": "raw_material",
    "unit": "kg"
  }'

# Finished product
curl -X POST http://localhost:8000/actors/demo-farm/items \
  -H "Content-Type: application/json" \
  -d '{
    "id": "pickled-garlic",
    "name": "Pickled Garlic (500ml)",
    "category": "finished_good",
    "unit": "jar_500ml"
  }'
```

### 3. Create a Batch

```bash
curl -X POST http://localhost:8000/actors/demo-farm/batches \
  -H "Content-Type: application/json" \
  -d '{
    "id": "batch-2025-001",
    "item_id": "garlic-raw",
    "quantity": {
      "amount": 50,
      "unit": "kg"
    },
    "production_date": "2025-01-15",
    "status": "active",
    "origin_kind": "harvested"
  }'
```

### 4. Query Your Data

```bash
# List all items
curl http://localhost:8000/actors/demo-farm/items

# List all batches
curl http://localhost:8000/actors/demo-farm/batches

# Get specific batch
curl http://localhost:8000/actors/demo-farm/batches/batch-2025-001

# Filter batches by status
curl http://localhost:8000/actors/demo-farm/batches?status=active
```

## Using the Interactive API Docs

The easiest way to explore the API is through the built-in Swagger UI:

1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., "POST /actors")
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. See the response!

## Next Steps

- **Read the spec**: See [draft_spec.md](../draft_spec.md) for the full product vision
- **Explore OOJ**: Read [Open_Origin_JSON_v0.5.md](../Open_Origin_JSON_v0.5.md) to understand the data format
- **Run tests**: `pytest` in the backend directory
- **Add more features**: Events, Processes, Locations coming soon!

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Make sure PostgreSQL is running and credentials in `.env` are correct.

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Test connection manually
psql -U originstack -d originstack -h localhost
```

### Import Error: No module named 'ooj_client'

**Solution**: Make sure OpenOriginJSON is in the parent directory:

```bash
# From OriginStack directory
ls ../OpenOriginJSON/ooj_client
```

### Port 8000 Already in Use

**Solution**: Either stop the other process or use a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

## Getting Help

- Check the [backend README](../backend/README.md)
- Review the API docs at http://localhost:8000/docs
- Look at example code in `tests/test_api.py`

Happy tracking! 🎯
