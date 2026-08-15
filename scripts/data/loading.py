import logging
import argparse
import pandas as pd
from sqlalchemy import create_engine

from agentic_workflow.core.config import DATABASE_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def inspect_postgres():
    """Connects to PostgreSQL and prints sample data from each table."""
    logging.info("--- Inspecting PostgreSQL Database ---")
    try:
        engine = create_engine(
            DATABASE_CONFIG.connection_string,
            connect_args=DATABASE_CONFIG.connect_args,
        )
        
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
    """Fail closed: live Chroma inspection is intentionally unsupported."""
    logging.error("Inspect Chroma only through the checksummed-copy verifier.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only PostgreSQL sample inspector")
    parser.add_argument("--postgres", action="store_true", help="Run bounded PostgreSQL samples")
    args = parser.parse_args()
    if args.postgres:
        inspect_postgres()
    else:
        parser.print_help()
