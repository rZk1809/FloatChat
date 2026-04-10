import os
import glob
import logging
import pandas as pd
import xarray as xr
import numpy as np
from tqdm import tqdm

# --- Configuration ---
# The directory where your downloaded .nc files are stored.
NC_FILES_DIRECTORY = "DATASET"

# The name of the output CSV file that will be created.
OUTPUT_CSV_FILE = "argo_data_export.csv"

# Configure logging to provide feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_nc_file_to_df(file_path):
    """
    Opens a single NetCDF file and converts all its valid profiles into a pandas DataFrame.
    """
    file_profiles_data = []
    try:
        with xr.open_dataset(file_path, decode_timedelta=True) as ds:
            num_profiles = ds.sizes.get('N_PROF', 0)

            for i in range(num_profiles):
                profile_slice = ds.isel(N_PROF=i)
                
                # --- Extract Metadata ---
                try:
                    wmo_id = int(profile_slice.get('PLATFORM_NUMBER').values)
                    cycle_num = int(profile_slice.get('CYCLE_NUMBER').values)
                    juld = profile_slice.get('JULD').values
                    lat = float(profile_slice.get('LATITUDE').values)
                    lon = float(profile_slice.get('LONGITUDE').values)

                    if np.issubdtype(juld.dtype, np.number):
                        profile_date = pd.to_datetime(juld, origin='1950-01-01', unit='D')
                    else:
                        profile_date = pd.to_datetime(juld)

                    # --- Create DataFrame for Measurements ---
                    df = pd.DataFrame({
                        'pressure': profile_slice['PRES'].values,
                        'temp': profile_slice['TEMP'].values,
                        'temp_qc': profile_slice['TEMP_QC'].values.astype(str),
                        'psal': profile_slice['PSAL'].values,
                        'psal_qc': profile_slice['PSAL_QC'].values.astype(str)
                    })

                    df.dropna(subset=['pressure'], inplace=True)
                    if df.empty: continue

                    # Apply Quality Control
                    good_qc_flags = ['1', '2', '5', '8']
                    df.loc[~df['temp_qc'].isin(good_qc_flags), 'temp'] = np.nan
                    df.loc[~df['psal_qc'].isin(good_qc_flags), 'psal'] = np.nan
                    
                    # Drop rows where both temp and psal are null after QC
                    df.dropna(subset=['temp', 'psal'], how='all', inplace=True)
                    if df.empty: continue

                    # Add metadata to every row
                    df['wmo_id'] = wmo_id
                    df['cycle_number'] = cycle_num
                    df['profile_date'] = profile_date
                    df['latitude'] = lat
                    df['longitude'] = lon

                    # Reorder columns for a clean output and select what we need
                    final_cols = ['wmo_id', 'cycle_number', 'profile_date', 'latitude', 'longitude', 'pressure', 'temp', 'psal']
                    file_profiles_data.append(df[final_cols])

                except (KeyError, IndexError, ValueError, TypeError) as e:
                    logging.warning(f"Skipping a malformed profile in {os.path.basename(file_path)} due to: {e}")
                    continue
        
        if not file_profiles_data:
            return None
        
        return pd.concat(file_profiles_data, ignore_index=True)

    except Exception as e:
        logging.error(f"Failed to read or process file {os.path.basename(file_path)}: {e}")
        return None

def main():
    """Main function to find all NetCDF files and export them to a single CSV."""
    logging.info(f"--- Starting ARGO Data Export to CSV ---")
    
    nc_files = sorted(glob.glob(os.path.join(NC_FILES_DIRECTORY, '*_prof.nc')))
    if not nc_files:
        logging.error(f"No NetCDF files found in directory: {NC_FILES_DIRECTORY}")
        return
        
    logging.info(f"Found {len(nc_files)} files to process.")

    all_dataframes = []
    for nc_file in tqdm(nc_files, desc="Processing Files"):
        df = process_nc_file_to_df(nc_file)
        if df is not None:
            all_dataframes.append(df)

    if not all_dataframes:
        logging.error("No valid data was extracted from any of the files.")
        return

    logging.info("Concatenating all data into a final DataFrame...")
    final_df = pd.concat(all_dataframes, ignore_index=True)

    logging.info(f"Saving {len(final_df)} data points to '{OUTPUT_CSV_FILE}'...")
    final_df.to_csv(OUTPUT_CSV_FILE, index=False)
    
    logging.info("--- Export Finished Successfully! ---")
    logging.info(f"Data saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    main()
