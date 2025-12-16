import meilisearch
from app.db.database import settings
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Initialize Meilisearch client
# In a real setup, these would be in settings
MEILI_HOST = "http://localhost:7700"
MEILI_MASTER_KEY = "veribatch_dev_master_key"

try:
    client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
except Exception as e:
    logger.error(f"Failed to connect to Meilisearch: {e}")
    client = None

INDEX_NAME = "veribatch"

def get_index():
    if not client:
        return None
    return client.index(INDEX_NAME)

def setup_index():
    """Configures the index settings (filterable attributes, etc.)"""
    if not client:
        return
    
    index = get_index()
    
    # Configure filterable attributes for security (actor_id) and UI (type)
    try:
        index.update_filterable_attributes([
            'actor_id',
            'type',
            'kind',
            'status',
            'year'
        ])
        
        # Configure searchable attributes (priority)
        index.update_searchable_attributes([
            'title',
            'id',
            'subtitle',
            'description',
            'details'
        ])
        
        # Configure sortable attributes
        index.update_sortable_attributes([
            'timestamp',
            'created_at'
        ])
        
        logger.info("Meilisearch index configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Meilisearch index: {e}")

def index_document(doc_type: str, actor_id: str, doc_data: dict):
    """
    Generic function to index a document.
    doc_data should contain: id, title, subtitle, description, link, timestamp, etc.
    """
    if not client:
        return

    # Add standard fields
    document = {
        'pk': f"{doc_type}_{doc_data.get('id')}", # Unique PK for Meili
        'type': doc_type,
        'actor_id': actor_id,
        **doc_data
    }
    
    try:
        get_index().add_documents([document])
    except Exception as e:
        logger.error(f"Error indexing document {document['pk']}: {e}")

# Specific Indexers

def index_batch(batch, item_name=None):
    """
    Index a Batch model. 
    Requires extracting data from JSONB doc for richer context.
    """
    data = batch.jsonb_doc
    
    # Try to extract useful search terms
    notes = data.get('notes', '')
    quantity = f"{data.get('quantity', {}).get('value', '')} {data.get('quantity', {}).get('unit', '')}"
    
    doc = {
        'id': batch.id,
        'title': f"Batch {batch.id}",
        'subtitle': f"{item_name or batch.item_id} - {batch.status}",
        'description': f"Prod: {batch.production_date}. Qty: {quantity}. {notes}",
        'link': f"/actors/{batch.actor_id}/batches/{batch.id}",
        'status': batch.status,
        'timestamp': batch.created_at.timestamp() if batch.created_at else 0,
        # flexible fields for search
        'details': f"{batch.item_id} {notes} {quantity} {batch.production_date}",
        'year': batch.production_date[:4] if batch.production_date else ""
    }
    index_document('Batch', batch.actor_id, doc)

def index_event(event):
    data = event.jsonb_doc
    
    # Extract locations or inputs involved
    details = []
    if 'inputs' in data:
        for i in data['inputs']:
            details.append(i.get('item_id', ''))
            details.append(i.get('batch_id', ''))
    
    if 'outputs' in data:
        for o in data['outputs']:
            details.append(o.get('batch_id', ''))
            
    note = data.get('notes', '')
    
    doc = {
        'id': event.id,
        'title': f"{event.event_type} Event",
        'subtitle': event.timestamp,
        'description': f"{note} " + ", ".join(filter(None, details))[:50] + "...",
        'link': f"/actors/{event.actor_id}/events/{event.id}/edit", # Link to edit page since no detail view exists
        'details': f"{event.event_type} {note} {' '.join(filter(None, details))}",
        'timestamp': event.timestamp # This might need parsing to unix timestamp for sorting if it's a string
    }
    index_document('Event', event.actor_id, doc)

def index_item(item):
    data = item.jsonb_doc
    desc = data.get('description', '')
    
    doc = {
        'id': item.id,
        'title': item.name,
        'subtitle': item.category,
        'description': desc,
        'link': f"/actors/{item.actor_id}/items/{item.id}/edit", # Link to edit page since no detail view exists
        'details': f"{item.category} {desc}",
        'timestamp': item.created_at.timestamp() if item.created_at else 0
    }
    index_document('Item', item.actor_id, doc)

def index_location(location):
    data = location.jsonb_doc
    desc = data.get('description', '')
    coords = data.get('coordinates', '')
    
    doc = {
        'id': location.id,
        'title': location.name,
        'subtitle': location.kind,
        'description': f"{desc} {coords}",
        'link': f"/actors/{location.actor_id}/locations/{location.id}/edit", # Link to edit page since no detail view exists
        'details': f"{location.kind} {desc} {coords}",
        'timestamp': location.created_at.timestamp() if location.created_at else 0
    }
    index_document('Location', location.actor_id, doc)

def index_process(process):
    data = process.jsonb_doc
    desc = data.get('description', '')
    
    doc = {
        'id': process.id,
        'title': process.name,
        'subtitle': f"{process.kind} - v{process.version}" if process.version else process.kind,
        'description': desc,
        'link': f"/actors/{process.actor_id}/processes/{process.id}", # Link to detail page
        'details': f"{process.kind} {desc}",
        'timestamp': process.created_at.timestamp() if process.created_at else 0
    }
    index_document('Process', process.actor_id, doc)

def search_global(query: str, actor_id: str, limit: int = 10):
    if not client:
        logger.warning("Search client not available")
        return []
    
    try:
        search_params = {
            'filter': f"actor_id = '{actor_id}'",
            'limit': limit,
            'attributesToHighlight': ['title', 'description']
        }
        logger.info(f"Searching Meilisearch: query='{query}', params={search_params}")
        
        result = get_index().search(query, search_params)
        
        hits = result.get('hits', [])
        logger.info(f"Search returned {len(hits)} hits")
        return hits
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return []
