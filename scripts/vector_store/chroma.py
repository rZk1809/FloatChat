# peek_chroma_full.py
import chromadb
import logging
import numpy as np # Import numpy to handle potential array types

# --- Configuration ---
CHROMA_DB_PATH = "chroma_db"
CHROMA_COLLECTION_NAME = "argo_profiles_ollama"
# Number of records to fetch per batch
BATCH_SIZE = 100

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def peek_full_chromadb():
    """Connects to ChromaDB and prints details of records in batches."""
    logging.info("--- Inspecting ChromaDB Vector Store ---")
    try:
        # 1. Connect to the Persistent Chroma Client
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        logging.info(f"Connected to ChromaDB at path: {CHROMA_DB_PATH}")

        # 2. Get the specific collection
        collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
        total_count = collection.count()
        logging.info(f"Collection '{CHROMA_COLLECTION_NAME}' contains {total_count} entries.")

        if total_count == 0:
            logging.info("Collection is empty.")
            return

        # 3. Retrieve all IDs first
        # Ensure ids are a standard Python list
        raw_ids_data = collection.get(include=[])
        # The 'ids' field in the returned dict might be a list, np.ndarray, etc.
        # We convert it to a standard Python list to be safe for slicing.
        all_ids = list(raw_ids_data['ids'])
        logging.info(f"Retrieved list of all {len(all_ids)} IDs.")

        print("\n--- Full Records from ChromaDB ---")
        # 4. Iterate through IDs in batches to get full data
        # Use enumerate on the list to get index (i) for printing item number
        for i in range(0, len(all_ids), BATCH_SIZE):
            # Get the slice of IDs for this batch
            batch_ids = all_ids[i:i + BATCH_SIZE]
            # Ensure batch_ids is also a standard list if it's a slice of a numpy array
            if not isinstance(batch_ids, list):
                batch_ids = list(batch_ids)

            # Fetch the full data for this batch of IDs
            # Add error handling for the get call
            try:
                batch_data = collection.get(
                    ids=batch_ids,
                    include=["embeddings", "documents", "metadatas"]
                )
            except Exception as fetch_error:
                logging.error(f"Error fetching batch starting at index {i}: {fetch_error}")
                continue # Skip this batch and try the next one

            # 5. Print details for each item in the batch
            # Check if batch_data contains the expected keys and data
            if not batch_data or 'ids' not in batch_data or not batch_data['ids']:
                logging.warning(f"Batch starting at index {i} returned no data.")
                continue

            num_items_in_batch = len(batch_data['ids'])
            for j in range(num_items_in_batch):
                try:
                    # Safely access data, checking if index j exists
                    item_id = batch_data['ids'][j]
                    document = batch_data['documents'][j] if j < len(batch_data.get('documents', [])) else "N/A"
                    metadata = batch_data['metadatas'][j] if j < len(batch_data.get('metadatas', [])) else {}
                    
                    # Handle embeddings safely
                    embedding_preview = []
                    embedding_dim = 0
                    if 'embeddings' in batch_data and j < len(batch_data['embeddings']):
                        emb = batch_data['embeddings'][j]
                        if emb is not None:
                            embedding_dim = len(emb)
                            embedding_preview = emb[:5] # Get first 5 elements

                    print(f"\n--- Item {i+j+1} (ID: {item_id}) ---")
                    print(f"  Metadata: {metadata}")
                    print(f"  Document: \"{document}\"")
                    print(f"  Embedding: {embedding_dim} dimensions (first 5: {embedding_preview}...)")

                except IndexError as idx_error:
                    logging.error(f"Index error accessing item {j} in batch starting at {i}: {idx_error}")
                except Exception as item_error:
                    logging.error(f"Unexpected error processing item {i+j+1}: {item_error}")

        print("\n--- End of Records ---")

    except Exception as e:
        logging.error(f"Failed to inspect ChromaDB: {e}", exc_info=True) # Add exc_info for more details

if __name__ == "__main__":
    peek_full_chromadb()


