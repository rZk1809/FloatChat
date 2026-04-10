import logging
import chromadb
import pandas as pd
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- Configuration ---
DB_USER = "rgk"
DB_PASSWORD = "rgk"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "argo_data"

# Name for the collection in ChromaDB
CHROMA_COLLECTION_NAME = "argo_profiles"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to fetch data from PostgreSQL, generate embeddings,
    and populate a ChromaDB vector store.
    """
    logging.info("--- Starting Vector Database Population ---")

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
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logging.info("Model loaded successfully.")

    # --- 4. Create the vector embeddings ---
    logging.info("Generating vector embeddings for all documents...")
    embeddings = model.encode(df['document'].tolist(), show_progress_bar=True)
    logging.info(f"Successfully generated {len(embeddings)} embeddings.")

    # --- 5. Setup ChromaDB and store the embeddings ---
    try:
        # Using a persistent client to save the DB to a local folder named 'chroma_db'
        client = chromadb.PersistentClient(path="chroma_db")
        
        # Create the collection. If it already exists, we can use it.
        # get_or_create_collection is helpful to avoid errors on subsequent runs.
        collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

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
