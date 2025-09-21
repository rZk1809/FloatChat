import os
import glob
import logging
import pandas as pd
import xarray as xr
import numpy as np  # <-- Added numpy for checking data types
from sqlalchemy import create_engine, text
from tqdm import tqdm

# --- Configuration ---
DB_USER = "rgk"
DB_PASSWORD = "rgk"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "argo_data"


NC_FILES_DIRECTORY = "DATASET"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_db():
    """Creates and returns a SQLAlchemy engine for connecting to the PostgreSQL database."""
    try:
        connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        with engine.connect() as connection:
            logging.info("Successfully connected to the PostgreSQL database.")
        return engine
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

def create_tables(engine):
    """Create required tables using the correct GEOGRAPHY type if they don't exist."""
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS floats (
                    id SERIAL PRIMARY KEY,
                    wmo_id INTEGER UNIQUE NOT NULL,
                    last_seen TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    float_id INTEGER REFERENCES floats(id),
                    cycle_number INTEGER,
                    profile_date TIMESTAMPTZ,
                    location GEOGRAPHY(Point, 4326),
                    UNIQUE (float_id, cycle_number)
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id BIGSERIAL PRIMARY KEY,
                    profile_id INTEGER REFERENCES profiles(id),
                    pressure REAL,
                    temp REAL,
                    psal REAL
                );
            """))
            transaction.commit()
            logging.info("Tables created or already exist.")
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            transaction.rollback()


def process_profile(profile_data):
    """Takes a single xarray profile, extracts, cleans, and structures the data."""
    try:
        wmo_id = int(profile_data.get('PLATFORM_NUMBER').values)
        cycle_num = int(profile_data.get('CYCLE_NUMBER').values)
        juld = profile_data.get('JULD').values
        lat = float(profile_data.get('LATITUDE').values)
        lon = float(profile_data.get('LONGITUDE').values)

        # --- ROBUST FIX: Handle both numeric (Julian Day) and string date formats ---
        if np.issubdtype(juld.dtype, np.number):
            # It's a number, so use the origin date
            profile_date = pd.to_datetime(juld, origin='1950-01-01', unit='D')
        else:
            # It's likely already a datetime string, let pandas parse it automatically
            profile_date = pd.to_datetime(juld)

        metadata = {
            'wmo_id': wmo_id,
            'cycle_number': cycle_num,
            'profile_date': profile_date,
            'lat': lat,
            'lon': lon
        }

        df = pd.DataFrame({
            'pressure': profile_data['PRES'].values,
            'temp': profile_data['TEMP'].values,
            'temp_qc': profile_data['TEMP_QC'].values.astype(str),
            'psal': profile_data['PSAL'].values,
            'psal_qc': profile_data['PSAL_QC'].values.astype(str)
        })

        df.dropna(subset=['pressure'], inplace=True)
        if df.empty: return None

        good_qc_flags = ['1', '2', '5', '8']
        df.loc[~df['temp_qc'].isin(good_qc_flags), 'temp'] = None
        df.loc[~df['psal_qc'].isin(good_qc_flags), 'psal'] = None
        
        measurements_df = df[['pressure', 'temp', 'psal']].copy()
        measurements_df.dropna(subset=['temp', 'psal'], how='all', inplace=True)
        
        if measurements_df.empty: return None

        return {'metadata': metadata, 'measurements': measurements_df}

    except (KeyError, IndexError, ValueError, TypeError) as e:
        wmo_id_str = f"float {profile_data.get('PLATFORM_NUMBER', 'N/A').values}"
        logging.warning(f"Skipping malformed profile for {wmo_id_str} due to: {e}")
        return None

def load_to_postgres(engine, processed_data):
    """Loads the processed data for a single profile into the PostgreSQL database."""
    metadata = processed_data['metadata']
    measurements = processed_data['measurements']
    
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            wmo_id = metadata['wmo_id']
            result = connection.execute(text("SELECT id FROM floats WHERE wmo_id = :wmo_id"), {'wmo_id': wmo_id})
            float_row = result.fetchone()
            
            if float_row:
                float_id = float_row[0]
                connection.execute(text("UPDATE floats SET last_seen = NOW() WHERE id = :id"), {'id': float_id})
            else:
                insert_result = connection.execute(text("INSERT INTO floats (wmo_id, last_seen) VALUES (:wmo_id, NOW()) RETURNING id"), {'wmo_id': wmo_id})
                float_id = insert_result.fetchone()[0]

            location_point = f"ST_SetSRID(ST_MakePoint({metadata['lon']}, {metadata['lat']}), 4326)::geography"
            profile_sql = text(f"""
                INSERT INTO profiles (float_id, cycle_number, profile_date, location)
                VALUES (:float_id, :cycle_number, :profile_date, {location_point})
                ON CONFLICT (float_id, cycle_number) DO NOTHING
                RETURNING id
            """)
            
            profile_result = connection.execute(profile_sql, {
                'float_id': float_id,
                'cycle_number': metadata['cycle_number'],
                'profile_date': metadata['profile_date']
            })
            profile_row = profile_result.fetchone()
            
            if not profile_row:
                logging.warning(f"Profile for float {wmo_id}, cycle {metadata['cycle_number']} already exists. Skipping.")
                transaction.rollback()
                return None
            
            profile_id = profile_row[0]
            measurements['profile_id'] = profile_id
            measurements.to_sql('measurements', connection, if_exists='append', index=False)
            
            transaction.commit()
            return profile_id

        except Exception as e:
            logging.error(f"DB transaction failed for float {metadata.get('wmo_id', 'N/A')}: {e}")
            transaction.rollback()
            return None

def generate_vector_summary(metadata, profile_id):
    """Generates a natural language summary for a profile, for vector embeddings."""
    summary = (
        f"ARGO float with WMO ID {metadata['wmo_id']} reported profile ID {profile_id} on "
        f"{metadata['profile_date'].strftime('%B %d, %Y')}. This was cycle number {metadata['cycle_number']}. "
        f"The profile was taken in the Indian Ocean at latitude {metadata['lat']:.2f} and longitude {metadata['lon']:.2f}. "
        "It contains quality-controlled measurements of temperature and salinity."
    )
    logging.debug(f"Generated Vector Summary: {summary}")
    return summary

def main():
    """Main function to orchestrate the data ingestion pipeline for a whole directory."""
    logging.info("--- Starting ARGO Batch Ingestion Pipeline ---")
    
    engine = connect_to_db()
    if not engine:
        return
    
    create_tables(engine)

    nc_files = glob.glob(os.path.join(NC_FILES_DIRECTORY, '*_prof.nc'))
    if not nc_files:
        logging.error(f"No NetCDF files found in directory: {NC_FILES_DIRECTORY}")
        return
        
    logging.info(f"Found {len(nc_files)} files to process in '{NC_FILES_DIRECTORY}'.")

    total_profiles_processed = 0
    total_profiles_failed = 0

    for nc_file_path in tqdm(nc_files, desc="Processing Files"):
        try:
            with xr.open_dataset(nc_file_path, decode_timedelta=True) as ds:
                # CORRECTED: Use .sizes to avoid FutureWarning
                num_profiles_in_file = ds.sizes.get('N_PROF', 0)
                
                for i in tqdm(range(num_profiles_in_file), desc=f"Profiles in {os.path.basename(nc_file_path)}", leave=False):
                    profile_slice = ds.isel(N_PROF=i)
                    
                    processed_data = process_profile(profile_slice)
                    if processed_data:
                        profile_id = load_to_postgres(engine, processed_data)
                        if profile_id:
                            generate_vector_summary(processed_data['metadata'], profile_id)
                            total_profiles_processed += 1
                        else:
                            total_profiles_failed += 1
                    else:
                        total_profiles_failed += 1
        except Exception as e:
            logging.error(f"Failed to process file {os.path.basename(nc_file_path)}: {e}")

    logging.info("--- Batch Ingestion Pipeline Finished ---")
    logging.info(f"Successfully processed and loaded: {total_profiles_processed} profiles.")
    logging.info(f"Failed or skipped: {total_profiles_failed} profiles.")

if __name__ == "__main__":
    main()

