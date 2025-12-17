# VeriBatch 🥕

> **"From the Berry Patch to VeriBatch."**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![HTMX](https://img.shields.io/badge/HTMX-1.9-blue?style=flat-square)](https://htmx.org)
[![License](https://img.shields.io/badge/License-AGPL%20v3-black?style=flat-square)](LICENSE)

**VeriBatch** is the open-source operating system for small farms, food processors, and cottage kitchens.

We built this because notebooks get lost, spreadsheets get messy, and "Enterprise Traceability" software costs more than your tractor.

---

## 🚜 Who is this for?

VeriBatch is designed for the **realities of production**, not just a database admin's fantasy.

*   **Farmers & Market Gardeners:** Track harvest lots from field to wash-pack.
*   **Value-Added Producers:** Trace raw garlic → peeling → pickling → jarring.
*   **Co-ops & Hubs:** Manage inventory across multiple producers.
*   **You:** If you've ever spent a Sunday night panic-entering data for an audit.

---

## ✨ Features that actually matter

### 🛡️ Sleep-at-Night Compliance
Audits shouldn't be scary. VeriBatch keeps you "inspection ready" by default.
*   **One-Click Mock Recalls:** Generate a full downstream report in seconds.
*   **Audit Logs:** Prove exactly who did what, and when.
*   **Data Export:** You own your data. Export everything to JSON or CSV instantly.

### 🏷️ Built-in Labeling Engine
Stop fighting with Word templates.
*   **Auto-Generated QR Codes:** Let customers scan to see the story behind their food.
*   **Dynamic Barcodes:** Supports retail UPCs (SCAN) and internal tracking codes (Code 128).
*   **Print-Ready:** formatted for standard label sizes (4x2", etc.).

### ⚡ The "OmniBar" Search
Don't dig through menus.
*   Type `garlic` -> See all garlic batches.
*   Type `lot-123` -> Jump straight to that batch's history.
*   Type `planting` -> Find all planting events.
*   *It just works.*

### 🧬 Real-World Modeling
Food production isn't a straight line. VeriBatch handles the messiness:
*   **Splits:** Divide one harvest into "Retail", "Wholesale", and "Processing".
*   **Merges:** Combine three days of picking into one sauce batch.
*   **Loss:** Track shrink, spoilage, and compost.

---

## 🛠️ The "Boring" Stack (That won't break)

We use proven, stable technology so you don't have to be a cloud architect to run your farm.

*   **Backend:** Python + FastAPI (Robust, fast, type-safe).
*   **Database:** PostgreSQL (The gold standard for data integrity).
*   **Frontend:** HTMX + Alpine.js + Tailwind (Fast, lightweight, no massive JavaScript bundles).
*   **Search:** Meilisearch (Typo-tolerant, instant results).

---

## 🚀 Get Started in 2 Minutes

### 1. Installation

```bash
# Clone the repo
git clone https://github.com/BoothFarm/VeriBatch.git
cd VeriBatch

# Run the all-in-one setup script
./setup.sh
```

### 2. Launch

```bash
# In backend/
source venv/bin/activate
uvicorn app.main:app --reload
```

### 3. Organize
Go to `http://localhost:8000`. You'll see our onboarding wizard:
1.  Create your **Actor** (Farm/Business profile).
2.  Define your **Items** (Carrots, Jams, etc.).
3.  Log your first **Harvest** or **Batch**.

---

## 🤝 Open Origin JSON

VeriBatch isn't just an app; it's a reference implementation of **Open Origin JSON (OOJ)**. This means your data is stored in a standardized, interoperable format. If you ever outgrow VeriBatch, you can take your data with you—structure and all.

---

<p align="center">
  <sub>Built with 💚 by Booth Farm Enterprises.</sub><br>
  <sub>Licensed under AGPL v3. <i>"Your harvest, your history."</i></sub>
</p>