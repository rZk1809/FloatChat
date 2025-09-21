import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import chromadb
from tqdm import tqdm
import logging
import requests
import json

# --- Configuration ---
CSV_FILE_PATH = "argo_data_export.csv"
# Updated PostgreSQL Credentials
DB_USER = "rgk"
DB_PASSWORD = "rgk"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "argo_data"
# ChromaDB Configuration
CHROMA_DB_PATH = "chroma_db"
CHROMA_COLLECTION_NAME = "argo_profiles_ollama"
# Ollama Embedding Model Configuration
OLLAMA_EMBED_MODEL = "embeddinggemma:300m" # As requested
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_postgres():
    """Connects to PostgreSQL, drops old tables, and creates new ones."""
    logging.info("Setting up PostgreSQL database...")
    try:
        engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        with engine.connect() as conn:
            # Drop tables to ensure a fresh start
            conn.execute(text("DROP TABLE IF EXISTS measurements, profiles, floats CASCADE;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text("""
                CREATE TABLE floats (id SERIAL PRIMARY KEY, wmo_id INTEGER UNIQUE NOT NULL);
            """))
            conn.execute(text("""
                CREATE TABLE profiles (
                    id SERIAL PRIMARY KEY, float_id INTEGER REFERENCES floats(id),
                    cycle_number INTEGER, profile_date TIMESTAMPTZ,
                    location GEOGRAPHY(Point, 4326), UNIQUE (float_id, cycle_number)
                );"""))
            conn.execute(text("""
                CREATE TABLE measurements (
                    id BIGSERIAL PRIMARY KEY, profile_id INTEGER REFERENCES profiles(id),
                    pressure REAL, temp REAL, psal REAL
                );"""))
            conn.commit()
        logging.info("PostgreSQL setup complete (tables reset).")
        return engine
    except Exception as e:
        logging.error(f"PostgreSQL setup failed: {e}")
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

def main():
    """Main function to load CSV and populate both databases using Ollama."""
    engine = setup_postgres()
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

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
        logging.info(f"Existing Chroma collection '{CHROMA_COLLECTION_NAME}' deleted.")
    except Exception:
        logging.info(f"No existing Chroma collection '{CHROMA_COLLECTION_NAME}' to delete.")
        
    collection = client.create_collection(name=CHROMA_COLLECTION_NAME)
    
    # Add to ChromaDB in batches
    batch_size = 500
    for i in tqdm(range(0, len(ids), batch_size), desc="Storing in ChromaDB"):
        collection.add(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        
    logging.info(f"ChromaDB population complete. Collection '{CHROMA_COLLECTION_NAME}' has {collection.count()} entries.")
    logging.info("--- All databases are ready! ---")

if __name__ == "__main__":
    main()

