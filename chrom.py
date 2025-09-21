# populate_chroma_only.py
import pandas as pd
import chromadb
from tqdm import tqdm
import logging
import requests
import json

# --- Configuration ---
CSV_FILE_PATH = "argo_data_export.csv"
# ChromaDB Configuration
CHROMA_DB_PATH = "chroma_db"
CHROMA_COLLECTION_NAME = "argo_profiles_ollama"
# Ollama Embedding Model Configuration
OLLAMA_EMBED_MODEL = "embeddinggemma:300m" # As requested
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_embedding_from_ollama(doc):
    """Gets a single vector embedding from the Ollama API."""
    try:
        payload = {"model": OLLAMA_EMBED_MODEL, "prompt": doc}
        response = requests.post(OLLAMA_EMBED_URL, json=payload)
        response.raise_for_status()
        return response.json().get("embedding")
    except Exception as e:
        logging.warning(f"Failed to get embedding for a document: {e}")
        return None

def main():
    """Main function to load CSV and populate ChromaDB using Ollama."""

    logging.info(f"Loading data from '{CSV_FILE_PATH}'...")
    # Load the CSV
    # Note: 'profile_id' is not in the file, we will create it.
    df = pd.read_csv(CSV_FILE_PATH) # Removed parse_dates here

    # --- ADDED: Create a unique profile_id from wmo_id and cycle_number ---
    df['profile_id'] = df['wmo_id'].astype(str) + "_" + df['cycle_number'].astype(str)
    logging.info("Generated 'profile_id' from 'wmo_id' and 'cycle_number'.")

    # --- CORRECTED: Parse dates robustly after loading ---
    try:
        df['profile_date'] = pd.to_datetime(df['profile_date'], format='mixed')
        logging.info("Parsed 'profile_date' column successfully with format='mixed'.")
    except Exception as parse_error:
        logging.error(f"Failed to parse 'profile_date' column: {parse_error}")
        return # Abort if date parsing fails

    # Drop any rows with missing critical data (using the newly created profile_id)
    df.dropna(subset=['profile_id', 'wmo_id', 'profile_date', 'latitude', 'longitude'], inplace=True)

    if df.empty:
        logging.error("No data found in CSV or all rows dropped due to missing values.")
        return

    logging.info("Preparing data for ChromaDB...")

    # --- Prepare unique profiles for embedding ---
    # Select the relevant columns
    # Include 'cycle_number' if you want it in the metadata
    profiles_for_embedding_df = df[['profile_id', 'wmo_id', 'cycle_number', 'profile_date', 'latitude', 'longitude']].drop_duplicates()
    # --- CORRECTED: Date parsing is already done on the main df ---
    # No need to re-parse here unless you suspect issues in the subset
    # If issues persist, you could add error handling here too, but it's usually not necessary.

    # Convert to records (list of dicts)
    profiles_to_embed = profiles_for_embedding_df.to_dict('records')

    documents, metadatas, ids, embeddings = [], [], [], []
    logging.info("Generating Embeddings via Ollama...")
    for p in tqdm(profiles_to_embed, desc="Generating Embeddings"):
        try:
            # Ensure p['profile_date'] is a datetime object for strftime
            # This check should be more robust now that parsing is fixed, but let's keep it.
            if not isinstance(p['profile_date'], pd.Timestamp):
                 p['profile_date'] = pd.to_datetime(p['profile_date'], format='mixed') # Fallback parse

            # Create the document string for embedding
            doc = (f"ARGO float {p['wmo_id']} (Cycle {p['cycle_number']}) on {p['profile_date'].strftime('%B %d, %Y')} "
                   f"at latitude {p['latitude']:.2f}, longitude {p['longitude']:.2f}.")
        except Exception as date_error:
            logging.warning(f"Error formatting date for profile_id {p.get('profile_id', 'Unknown')}: {date_error}")
            # Fallback: use the string representation if datetime conversion fails
            # Note: p['profile_date'] is likely already a string if the above failed
            doc = (f"ARGO float {p['wmo_id']} (Cycle {p['cycle_number']}) on {p['profile_date']} "
                   f"at latitude {p['latitude']:.2f}, longitude {p['longitude']:.2f}.")

        embedding = get_embedding_from_ollama(doc)

        if embedding:
            documents.append(doc)
            embeddings.append(embedding)
            # Metadata can include wmo_id, cycle_number, and the derived profile_id
            metadatas.append({
                'wmo_id': int(p['wmo_id']),
                'cycle_number': int(p['cycle_number']),
                'profile_id': p['profile_id'] # Use the string ID we created
            })
            # Chroma IDs should be strings. Use the generated profile_id.
            ids.append(p['profile_id'])
        else:
            logging.warning(f"Embedding failed for profile_id {p.get('profile_id', 'Unknown')}, doc: {doc[:50]}...")


    if not ids:
        logging.error("No valid embeddings were generated. ChromaDB population aborted.")
        return

    logging.info(f"Generated {len(ids)} embeddings. Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Delete the collection if it exists
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
        logging.info(f"Existing Chroma collection '{CHROMA_COLLECTION_NAME}' deleted.")
    except Exception as e:
        logging.info(f"No existing Chroma collection '{CHROMA_COLLECTION_NAME}' to delete or deletion failed: {e}")

    # Create the new collection
    collection = client.create_collection(name=CHROMA_COLLECTION_NAME)
    logging.info(f"Created new Chroma collection '{CHROMA_COLLECTION_NAME}'.")

    # Add embeddings to ChromaDB in batches
    logging.info("Storing embeddings in ChromaDB...")
    batch_size = 500
    for i in tqdm(range(0, len(ids), batch_size), desc="Storing in ChromaDB"):
        end_idx = min(i + batch_size, len(ids))
        try:
            collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        except Exception as e:
            logging.error(f"Failed to add batch {i//batch_size + 1} to ChromaDB: {e}")
            # Depending on requirements, you might want to continue or abort
            # For now, we'll log and try to continue with the next batch


    logging.info(f"ChromaDB population complete. Collection '{CHROMA_COLLECTION_NAME}' has {collection.count()} entries.")
    logging.info("--- ChromaDB is ready! ---")

if __name__ == "__main__":
    main()