# dump_postgres_to_text.py
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import argparse
from pathlib import Path

from agentic_workflow.core.config import DATABASE_CONFIG, PROJECT_ROOT

# --- Configuration ---
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_db():
    """Creates and returns a SQLAlchemy engine for connecting to the PostgreSQL database."""
    try:
        engine = create_engine(
            DATABASE_CONFIG.connection_string,
            connect_args=DATABASE_CONFIG.connect_args,
        )
        # Test the connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logging.info("Successfully connected to the PostgreSQL database.")
        return engine
    except Exception as exc:
        logging.error("Failed to connect to the database (%s)", type(exc).__name__)
        return None

def dump_data(engine, output_file):
    """Dumps data from PostgreSQL tables to a text file."""
    output_path = Path(output_file).expanduser().resolve()
    if output_path.exists():
        raise FileExistsError("Refusing to overwrite an existing export")
    try:
        logging.info("Starting data dump...")

        # --- 1. Fetch profile metadata joined with float WMO ID ---
        # This query gets one line per profile with its key identifiers and location/date.
        # Using ST_AsText to get a readable format for the location.
        profile_query = text("""
            SELECT
                f.wmo_id,
                p.cycle_number,
                p.profile_date,
                ST_AsText(p.location) AS location_wkt -- Convert geometry to text
            FROM profiles p
            JOIN floats f ON p.float_id = f.id
            ORDER BY f.wmo_id, p.cycle_number
        """)
        logging.info("Fetching profile metadata...")
        profiles_df = pd.read_sql(profile_query, engine)
        logging.info(f"Fetched {len(profiles_df)} profiles.")

        if profiles_df.empty:
            logging.warning("No profile data found. Dump file will be empty.")
            with open(output_file, 'w') as f:
                f.write("# ARGO Data Dump\n")
                f.write("# No data found in the database.\n")
            return

        # --- 2. Fetch all measurement data ---
        # This query gets all temperature, salinity, pressure measurements.
        measurements_query = text("""
            SELECT
                pr.id AS profile_db_id, -- Internal DB ID for joining
                f.wmo_id,
                pr.cycle_number,
                m.pressure,
                m.temp,
                m.psal
            FROM measurements m
            JOIN profiles pr ON m.profile_id = pr.id
            JOIN floats f ON pr.float_id = f.id
            ORDER BY f.wmo_id, pr.cycle_number, m.pressure
        """)
        logging.info("Fetching measurement data...")
        measurements_df = pd.read_sql(measurements_query, engine)
        logging.info(f"Fetched {len(measurements_df)} measurements.")

        # --- 3. Write to text file ---
        logging.info(f"Writing data to '{output_file}'...")
        with open(output_file, 'w') as f:
            f.write("# ARGO Data Dump\n")
            f.write("# Format:\n")
            f.write("# --- PROFILE START ---\n")
            f.write("# WMO_ID: <wmo_id>\n")
            f.write("# Cycle_Number: <cycle_number>\n")
            f.write("# Profile_Date: <profile_date>\n")
            f.write("# Location: <location_wkt>\n")
            f.write("# Measurements (Pressure, Temperature, Salinity):\n")
            f.write("# P,T,S\n") # Header for measurements
            f.write("# <pressure1>,<temp1>,<psal1>\n")
            f.write("# <pressure2>,<temp2>,<psal2>\n")
            f.write("# ...\n")
            f.write("# --- PROFILE END ---\n")
            f.write("#\n")
            f.write("# --- NEXT PROFILE START ---\n")
            f.write("# ...\n")
            f.write("#\n\n")

            # --- 4. Iterate through unique profiles and write data ---
            # Group measurements by wmo_id and cycle_number to match profile list
            grouped_measurements = measurements_df.groupby(['wmo_id', 'cycle_number'])

            for index, profile_row in profiles_df.iterrows():
                wmo_id = profile_row['wmo_id']
                cycle_number = profile_row['cycle_number']
                profile_date = profile_row['profile_date']
                location_wkt = profile_row['location_wkt']

                f.write("--- PROFILE START ---\n")
                f.write(f"WMO_ID: {wmo_id}\n")
                f.write(f"Cycle_Number: {cycle_number}\n")
                f.write(f"Profile_Date: {profile_date}\n")
                f.write(f"Location: {location_wkt}\n")
                f.write("Measurements (Pressure, Temperature, Salinity):\n")
                f.write("P,T,S\n") # Header for measurements

                # Find measurements for this specific profile
                profile_key = (wmo_id, cycle_number)
                if profile_key in grouped_measurements.groups:
                    profile_measurements = grouped_measurements.get_group(profile_key)
                    for _, measurement_row in profile_measurements.iterrows():
                        p = measurement_row['pressure']
                        t = measurement_row['temp']
                        s = measurement_row['psal']
                        # Handle potential NaNs by writing 'NaN' or leaving blank
                        p_str = f"{p:.2f}" if pd.notna(p) else "NaN"
                        t_str = f"{t:.4f}" if pd.notna(t) else "NaN"
                        s_str = f"{s:.4f}" if pd.notna(s) else "NaN"
                        f.write(f"{p_str},{t_str},{s_str}\n")
                else:
                    f.write("# No measurements found for this profile.\n")

                f.write("--- PROFILE END ---\n\n")

        logging.info(f"Data dump complete. Output written to '{output_file}'.")

    except Exception as e:
        logging.error(f"An error occurred during the data dump: {e}", exc_info=True)

def main(output_file: str):
    """Main function to orchestrate the data dumping process."""
    logging.info("--- Starting PostgreSQL Data Dump to Text File ---")
    
    engine = connect_to_db()
    if not engine:
        logging.error("Exiting due to database connection failure.")
        return

    dump_data(engine, output_file)
    logging.info("--- Data Dump Process Finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export read-only ARGO data to a new file")
    parser.add_argument("--output", required=True, help="New output path; existing files are refused")
    args = parser.parse_args()
    main(args.output)
