import argparse
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import chromadb
from tqdm import tqdm
import logging
import requests
import json

# --- Configuration ---
CSV_FILE_PATH = os.environ.get("ARGO_CSV_PATH", "argo_data_export.csv")
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "argo_data")
# ChromaDB Configuration
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "chroma_db")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "argo_profiles_ollama")
# Ollama Embedding Model Configuration
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "")
OLLAMA_EMBED_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/embeddings"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_postgres(confirm_destroy: bool = False):
    """Retired destructive setup entry point; always fail closed."""
    logging.error(
        "This reset-and-reseed utility is retired. Use the documented "
        "non-destructive ingestion and versioned-index commands."
    )
    return None

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

def main(confirm_destroy: bool = False):
    """Main function to load CSV and populate both databases using Ollama."""
    engine = setup_postgres(confirm_destroy=confirm_destroy)
    if not engine: return

    logging.info(f"Loading data from '{CSV_FILE_PATH}'...")
    df = pd.read_csv(CSV_FILE_PATH, parse_dates=['profile_date'])
    df.dropna(inplace=True)

    logging.info("Populating PostgreSQL...")
    unique_floats = pd.DataFrame({'wmo_id': df['wmo_id'].unique()})
    unique_floats.to_sql('floats', engine, if_exists='append', index=False)

    wmo_to_id = pd.read_sql("SELECT id, wmo_id FROM floats", engine).set_index('wmo_id')['id']
    df['float_id'] = df['wmo_id'].map(wmo_to_id)

    # --- FIX: Ensure profiles_df is unique on the key columns before inserting ---
    profiles_df = df[['float_id', 'cycle_number', 'profile_date', 'latitude', 'longitude']].drop_duplicates(
        subset=['float_id', 'cycle_number'],
        keep='first'
    )
    profiles_df['location'] = profiles_df.apply(lambda r: f"POINT({r.longitude} {r.latitude})", axis=1)
    profiles_df[['float_id', 'cycle_number', 'profile_date', 'location']].to_sql('profiles', engine, if_exists='append', index=False)

    profile_key_df = pd.read_sql("SELECT id, float_id, cycle_number FROM profiles", engine)
    df = pd.merge(df, profile_key_df, on=['float_id', 'cycle_number'])
    df.rename(columns={'id': 'profile_id'}, inplace=True)

    measurements_df = df[['profile_id', 'pressure', 'temp', 'psal']]
    measurements_df.to_sql('measurements', engine, if_exists='append', index=False, chunksize=10000)
    logging.info("PostgreSQL population complete.")

    logging.info("Populating ChromaDB using Ollama embeddings...")
    profiles_to_embed = df[['profile_id', 'wmo_id', 'profile_date', 'latitude', 'longitude']].drop_duplicates().to_dict('records')

    documents, metadatas, ids, embeddings = [], [], [], []
    for p in tqdm(profiles_to_embed, desc="Generating Embeddings via Ollama"):
        doc = (f"ARGO float {p['wmo_id']} on {p['profile_date'].strftime('%B %d, %Y')} "
               f"at latitude {p['latitude']:.2f}, longitude {p['longitude']:.2f}.")
        embedding = get_embedding_from_ollama(doc)
        if embedding:
            documents.append(doc)
            embeddings.append(embedding)
            metadatas.append({'wmo_id': p['wmo_id'], 'profile_id': p['profile_id']})
            ids.append(str(p['profile_id']))

    raise RuntimeError(
        "Legacy Chroma population is disabled; use the versioned-index pipeline"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Retired reset utility; retained only to fail safely."
    )
    args = parser.parse_args()
    main()
