import logging
import os
from pathlib import Path
import chromadb
import pandas as pd
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- Configuration ---
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "argo_data")

# Name for the collection in ChromaDB
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "argo_profiles_v2")
CHROMA_PATH = Path(os.environ.get("CHROMA_PATH", PROJECT_ROOT / "chroma_v2")).resolve()
EMBED_MODEL_PATH = os.environ.get("LOCAL_EMBED_MODEL_PATH", "")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to fetch data from PostgreSQL, generate embeddings,
    and populate a ChromaDB vector store.
    """
    logging.info("--- Starting Vector Database Population ---")

    if not EMBED_MODEL_PATH or not Path(EMBED_MODEL_PATH).is_dir():
        logging.error("LOCAL_EMBED_MODEL_PATH must point to an already-installed model.")
        return
    if CHROMA_PATH == (PROJECT_ROOT / "chroma_db").resolve() or CHROMA_COLLECTION_NAME in {
        "argo_profiles",
        "argo_profiles_ollama",
    }:
        logging.error("Refusing to write to a legacy path or collection.")
        return

    # --- 1. Connect to PostgreSQL and fetch all profile data ---
    try:
        connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        # SQL query to join floats and profiles table to get all necessary info
        sql_query = """
        SELECT
            p.id AS profile_id,
            f.wmo_id,
            p.cycle_number,
            p.profile_date,
            ST_Y(p.location::geometry) AS latitude,
            ST_X(p.location::geometry) AS longitude
        FROM profiles p
        JOIN floats f ON p.float_id = f.id;
        """
        
        logging.info("Fetching profile data from PostgreSQL...")
        df = pd.read_sql(sql_query, engine)
        logging.info(f"Successfully fetched {len(df)} profiles from the database.")

    except Exception as e:
        logging.error(f"Failed to fetch data from PostgreSQL: {e}")
        return

    if df.empty:
        logging.warning("No profiles found in the database to process.")
        return

    # --- 2. Generate the text summaries (documents) for each profile ---
    logging.info("Generating text summaries for vectorization...")
    documents = []
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Generating Summaries"):
        summary = (
            f"ARGO float with WMO ID {row['wmo_id']} reported profile ID {row['profile_id']} on "
            f"{row['profile_date'].strftime('%B %d, %Y')}. This was cycle number {row['cycle_number']}. "
            f"The profile was taken at latitude {row['latitude']:.2f} and longitude {row['longitude']:.2f}."
        )
        documents.append(summary)
    
    df['document'] = documents

    # --- 3. Initialize the AI model to create embeddings ---
    # 'all-MiniLM-L6-v2' is a small but powerful model, great for getting started.
    logging.info("Loading sentence-transformer model (this may take a moment)...")
    model = SentenceTransformer(EMBED_MODEL_PATH, local_files_only=True)
    logging.info("Model loaded successfully.")

    # --- 4. Create the vector embeddings ---
    logging.info("Generating vector embeddings for all documents...")
    embeddings = model.encode(df['document'].tolist(), show_progress_bar=True)
    logging.info(f"Successfully generated {len(embeddings)} embeddings.")

    # --- 5. Setup ChromaDB and store the embeddings ---
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        
        try:
            client.get_collection(name=CHROMA_COLLECTION_NAME)
            logging.error("Target collection already exists; refusing to mix embeddings.")
            return
        except Exception:
            pass
        collection = client.create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"embedding_model": str(Path(EMBED_MODEL_PATH).resolve()), "schema_version": "2"},
        )

        # Prepare metadata and IDs for ChromaDB
        metadatas = df[['wmo_id', 'profile_id', 'latitude', 'longitude']].to_dict('records')
        ids = df['profile_id'].astype(str).tolist()

        # Add the data to the collection in batches for efficiency
        batch_size = 512
        logging.info(f"Adding data to ChromaDB collection '{CHROMA_COLLECTION_NAME}'...")
        for i in tqdm(range(0, len(ids), batch_size), desc="Storing in ChromaDB"):
            collection.add(
                embeddings=embeddings[i:i+batch_size].tolist(),
                documents=df['document'].tolist()[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

        logging.info("--- Vector Database Population Finished Successfully! ---")
        logging.info(f"ChromaDB now contains {collection.count()} entries.")
        logging.info("Your backend data layer is now complete.")

    except Exception as e:
        logging.error(f"Failed to setup or store data in ChromaDB: {e}")


if __name__ == "__main__":
    main()
