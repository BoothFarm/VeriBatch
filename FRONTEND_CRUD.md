# Frontend CRUD Operations

The OriginStack frontend now supports full Create, Read, Update, and Delete operations for all entities through a beautiful web interface.

## Available Operations

### Actors
- **Create**: `/ui/actors/new` - Add new organization
- **Read**: `/ui/actors` - List all actors
- **Update**: `/ui/actors/{id}/edit` - Edit actor details
- **Delete**: Delete button on each actor card

### Items (Products/Ingredients)
- **Create**: `/ui/actors/{actor_id}/items/new` - Add new item
- **Read**: `/ui/actors/{actor_id}/items` - List all items
- **Update**: `/ui/actors/{actor_id}/items/{id}/edit` - Edit item
- **Delete**: Delete button in table row

### Batches
- **Create**: `/ui/actors/{actor_id}/batches/new` - Record new batch
- **Read**: `/ui/actors/{actor_id}/batches` - List all batches (with filters)
- **Delete**: Delete button in table row
- Note: Batch editing not implemented (batches are immutable by design)

### Processes (Recipes/SOPs)
- **Create**: `/ui/actors/{actor_id}/processes/new` - Define new process
- **Read**: `/ui/actors/{actor_id}/processes` - List all processes
- **Delete**: Delete button on each process card

### Locations
- **Create**: `/ui/actors/{actor_id}/locations/new` - Add new location
- **Read**: `/ui/actors/{actor_id}/locations` - List all locations
- **Delete**: Delete button on each location card

### Events (Production Activities)
- **Create**: `/ui/actors/{actor_id}/events/new` - Record new event
- **Read**: `/ui/actors/{actor_id}/events` - List all events (with filters)
- **Delete**: Delete button on each event

## Features

### Forms Include:
- ✅ Input validation
- ✅ Required field indicators
- ✅ Helpful placeholder text
- ✅ Dropdown selections for related entities
- ✅ Responsive design

### Safety Features:
- ✅ Confirmation dialogs before delete
- ✅ Read-only ID fields on edit forms
- ✅ Cancel buttons to abort
- ✅ Clear error messages

### User Experience:
- ✅ Instant redirects after success
- ✅ Color-coded buttons (green=create, blue=edit, red=delete)
- ✅ Breadcrumb navigation
- ✅ Consistent styling across all forms

## Quick Start

1. **Start the server**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Visit the UI**: http://localhost:8000/

3. **Create your first actor**:
   - Click "+ New Actor"
   - Fill in the form
   - Click "Create Actor"

4. **Add items, batches, and more**:
   - Navigate to each section via the dashboard
   - Use the "+ New ..." buttons

## Form Field Guide

### Actor Form
- **ID**: Unique identifier (lowercase, no spaces)
- **Name**: Display name
- **Kind**: producer, processor, distributor, retailer
- **Contacts**: Email, phone, website (all optional)
- **Address**: Full address fields (all optional)

### Item Form
- **ID**: Unique identifier (e.g., "organic-tomatoes")
- **Name**: Display name
- **Kind**: ingredient, product, packaging, supply
- **Description**: Optional details
- **Variety**: Optional cultivar/variant

### Batch Form
- **ID**: Unique identifier (e.g., "2024-001")
- **Item**: Select from dropdown (must create items first!)
- **Production Date**: When batch was created
- **Quantity**: Amount and unit
- **Status**: active, depleted, quarantined, disposed
- **Origin Kind**: Set if this is a supply chain origin

### Process Form
- **ID**: Unique identifier (e.g., "wash-and-pack")
- **Name**: Display name
- **Kind**: processing, packaging, quality-check, storage
- **Steps**: One per line or comma-separated

### Location Form
- **ID**: Unique identifier (e.g., "field-1")
- **Name**: Display name
- **Kind**: field, greenhouse, warehouse, processing-facility
- **Address**: Full address
- **Coordinates**: Lat/lon for mapping

### Event Form
- **ID**: Unique identifier (e.g., "evt-2024-001")
- **Event Type**: processing, split, merge, disposal, transfer
- **Timestamp**: Defaults to now
- **Process**: Select from dropdown (optional)
- **Location**: Select from dropdown (optional)
- **Inputs**: Comma-separated batch IDs consumed
- **Outputs**: Comma-separated batch IDs created

## Tips

- **Start with Actors**: Create at least one actor first
- **Then Items**: Define your products/ingredients
- **Then Batches**: Record your inventory
- **Then Processes** (optional): Define your SOPs
- **Then Events**: Record production activities

- **Use descriptive IDs**: They're permanent, make them meaningful
- **Fill optional fields**: More data = better traceability
- **Delete carefully**: No undo!

## Next Steps

After using the CRUD interface to populate your data, try:
- View traceability graphs
- Export OOJ archives
- Use the API for automation
- Build custom integrations
