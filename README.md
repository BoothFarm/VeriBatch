# VeriBatch 🥕

**An open, producer-first food traceability platform**

VeriBatch is an open-source platform for tracking batches, processes, and provenance in food and small-scale manufacturing. It is built on **Open Origin JSON (OOJ)**, an open data specification designed to make traceability practical, portable, and vendor-neutral.

VeriBatch exists to replace spreadsheet chaos without replacing your ownership of data.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![OOJ](https://img.shields.io/badge/Open_Origin_JSON-v0.5-green.svg)](./Open_Origin_JSON_v0.5.md)
[![License](https://img.shields.io/badge/License-AGPL%20%2F%20MIT-blue.svg)](LICENSE)

---

## What is VeriBatch?

VeriBatch is **production-ready traceability software** designed for:

- Farms and market gardens
- Food processors and value-added producers
- Bakeries, fermenters, and small manufacturers
- Co-ops and shared facilities
- Consultants supporting regulated food businesses

It models the *actual lifecycle* of food and products: inputs, transformations, losses, splits, merges, and hand-offs between actors.

Unlike traditional systems, VeriBatch treats traceability as **structured data**, not locked-in records.

---

## Core Principles

### 🧱 Built on an Open Standard
VeriBatch uses **Open Origin JSON (OOJ v0.5)** as its native data model.

This means:
- Your data is readable JSON
- You can export everything, at any time
- Other systems can interoperate without custom adapters
- Switching tools does not destroy your history

VeriBatch is opinionated software on top of an **unopinionated standard**.

---

### 🔓 No Vendor Lock-In
Most traceability tools trap years of operational history inside proprietary schemas.

VeriBatch does the opposite.

- All records are stored as OOJ documents
- JSONB storage preserves structure and flexibility
- Exports are first-class, not an afterthought

If VeriBatch disappeared tomorrow, your data would still make sense.

---

### 🌱 Designed for Real Operations
VeriBatch models things most systems avoid:

- Loss, shrink, spoilage, and disposal
- Partial batch usage and splits
- Multi-step processing workflows
- Cross-actor sourcing and supply chains
- Human accountability via events and timestamps

If it happens in real production, it belongs in the system.

---

## Key Capabilities

- **Batch lifecycle tracking** from input to final sale
- **Event-based provenance** (processing, transfer, disposal, recall)
- **Fast full-text search** across batches, items, and events
- **QR code generation** for public batch verification
- **Compliance-friendly exports** for audits and inspections
- **Multi-operation support** within a single instance
- **API-first design** with auto-generated documentation

---

## Architecture Overview

VeriBatch uses a modern but intentionally boring stack:

```
Browser
  ↓
HTMX templates (server-rendered, minimal JS)
  ↓
FastAPI (typed, async, documented)
  ↓
PostgreSQL (JSONB + relational indexes)
  ↓
Meilisearch (fast, typo-tolerant search)
```

Why this matters:
- Easy to self-host
- Easy to reason about
- Easy to extend
- No frontend framework churn
- No cloud lock-in assumptions

---

## Getting Started

### Self-Hosted (Recommended for Developers)

```bash
git clone https://github.com/BoothFarm/VeriBatch.git
cd VeriBatch
./setup.sh
```

Then open:

```
http://localhost:8000
```

You will get:
- A working web UI
- Sample data
- Search enabled
- API docs available at `/docs`

---

### API Access

VeriBatch exposes a full REST API.

```bash
http://localhost:8000/docs
```

All core actions (actors, items, batches, events) are available via API and map directly to OOJ entities.

---

## Relationship to Open Origin JSON

VeriBatch is the **reference implementation** of the Open Origin JSON specification.

- OOJ is vendor-neutral and independently licensed
- VeriBatch implements OOJ fully and faithfully
- Other tools can implement OOJ without using VeriBatch
- VeriBatch benefits from interoperability as OOJ adoption grows

Think of OOJ as the protocol, VeriBatch as one good client.

---

## Who This Is For

VeriBatch is a good fit if you:

- Need traceability but hate spreadsheets
- Want audit-ready records without enterprise pricing
- Care about owning your operational data
- Prefer open systems over black boxes
- Are a developer, consultant, or technically curious producer

It may *not* be a fit if you want a closed, compliance-only checkbox tool.

---

## Documentation

- **GETTING_STARTED.md** – Initial setup and workflow
- **CAPABILITIES.md** – What is implemented today
- **Open_Origin_JSON_v0.5.md** – Data specification
- **LEVEL_2_3_GUIDE.md** – Advanced traceability concepts
- **PROD_DEPLOYMENT.md** – Production deployment notes

---

## Contributing

Contributions are welcome and encouraged.

Especially valuable:
- Real-world edge cases
- Additional export formats
- Frontend usability improvements
- OOJ client libraries in other languages
- Documentation clarifications

This project improves fastest when grounded in reality.

---

## License

- **VeriBatch software**: Open-source, see LICENSE
- **Open Origin JSON specification**: CC-BY 4.0

---

**Booth Farm Enterprises Ltd.**  
*Open traceability, without the bullshit.*
