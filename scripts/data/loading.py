import logging
import pandas as pd
import chromadb
from sqlalchemy import create_engine

DB_USER = "rgk"              # <-- use your actual creds
DB_PASSWORD = "rgk"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "argo_data"
CHROMA_COLLECTION_NAME = "argo_profiles"
CHROMA_DB_PATH = "chroma_db"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def inspect_postgres():
    """Connects to PostgreSQL and prints sample data from each table."""
    logging.info("--- Inspecting PostgreSQL Database ---")
    try:
        connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        print("\n[+] Querying 'floats' table (first 5 rows):")
        df_floats = pd.read_sql("SELECT * FROM floats LIMIT 5;", engine)
        print(df_floats.to_string())
        
        print("\n[+] Querying 'profiles' table (first 5 rows):")
        # Note: We select the location as text to make it readable
        df_profiles = pd.read_sql("SELECT id, float_id, cycle_number, profile_date, ST_AsText(location) as location_wkt FROM profiles LIMIT 5;", engine)
        print(df_profiles.to_string())

        print("\n[+] Querying 'measurements' table (first 10 rows):")
        df_measurements = pd.read_sql("SELECT * FROM measurements LIMIT 10;", engine)
        print(df_measurements.to_string())

    except Exception as e:
        logging.error(f"Failed to inspect PostgreSQL: {e}")

def inspect_chromadb():
    """Connects to ChromaDB and prints a sample of the stored data."""
    logging.info("\n--- Inspecting ChromaDB Vector Store ---")
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
        
        logging.info(f"Collection '{CHROMA_COLLECTION_NAME}' contains {collection.count()} entries.")
        
        # .peek() is the standard way to get a small sample from a Chroma collection
        sample = collection.peek(limit=5)
        
        print("\n[+] Peeking at 5 items from the ChromaDB collection:")
        
        # Nicely format the output
        for i in range(len(sample['ids'])):
            print(f"\n--- Item {i+1} ---")
            print(f"  ID: {sample['ids'][i]}")
            print(f"  Distance: {sample.get('distances', 'N/A')}") # Distance is only present in query results
            print(f"  Metadata: {sample['metadatas'][i]}")
            print(f"  Document: \"{sample['documents'][i]}\"")
            # Embeddings are very long arrays, so we'll just show the first few dimensions
            embedding_preview = sample['embeddings'][i][:5]
            print(f"  Embedding (first 5 dims): {embedding_preview}...")

    except Exception as e:
        logging.error(f"Failed to inspect ChromaDB: {e}")


if __name__ == "__main__":
    inspect_postgres()
    inspect_chromadb()
