import sys
import os
import time
from sqlalchemy.orm import Session
import requests

# Add backend directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SessionLocal
from app.models import database as db_models
from app.services import search_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_meilisearch(host, port, timeout=60, interval=1):
    """Waits for Meilisearch to be available."""
    url = f"http://{host}:{port}/health"
    start_time = time.time()
    logger.info(f"Waiting for Meilisearch at {url}...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=interval)
            if response.status_code == 200 and response.json().get("status") == "available":
                logger.info("Meilisearch is available!")
                return True
        except requests.exceptions.ConnectionError:
            logger.debug(f"Meilisearch not yet available, retrying in {interval}s...")
        except Exception as e:
            logger.error(f"Error checking Meilisearch health: {e}")
        time.sleep(interval)
    logger.error("Meilisearch did not become available within the timeout.")
    return False

def reindex_all():
    logger.info("Starting reindexing process...")
    
    # Wait for Meilisearch to be ready
    if not wait_for_meilisearch("localhost", 7700):
        logger.error("Aborting reindexing: Meilisearch not available.")
        return
    
    db = SessionLocal()
    try:
        # Setup index
        search_service.setup_index()
        
        # 1. Index Items
        items = db.query(db_models.Item).all()
        logger.info(f"Indexing {len(items)} items...")
        for item in items:
            search_service.index_item(item)
            
        # 2. Index Locations
        locations = db.query(db_models.Location).all()
        logger.info(f"Indexing {len(locations)} locations...")
        for location in locations:
            search_service.index_location(location)
            
        # 3. Index Batches (need item name for better context)
        batches = db.query(db_models.Batch).all()
        logger.info(f"Indexing {len(batches)} batches...")
        
        # Cache item names to avoid N+1 queries
        item_names = {i.id: i.name for i in items}
        
        for batch in batches:
            item_name = item_names.get(batch.item_id)
            search_service.index_batch(batch, item_name)
            
        # 4. Index Events
        events = db.query(db_models.Event).all()
        logger.info(f"Indexing {len(events)} events...")
        for event in events:
            search_service.index_event(event)
            
        # 5. Index Processes
        processes = db.query(db_models.Process).all()
        logger.info(f"Indexing {len(processes)} processes...")
        for process in processes:
            search_service.index_process(process)
            
        logger.info("Reindexing complete!")
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reindex_all()
