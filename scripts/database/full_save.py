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
OUTPUT_CSV_FILE = "argo_data_export_full.csv"

# Configure logging to provide feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_nc_file_to_df(file_path):
    """
    Opens a single NetCDF file and converts all its profiles into a pandas DataFrame,
    including ALL data variables by intelligently flattening metadata.
    """
    all_profiles_df_list = []
    try:
        with xr.open_dataset(file_path, decode_timedelta=True, engine="netcdf4") as ds:
            num_profiles = ds.sizes.get('N_PROF', 0)

            for i in tqdm(range(num_profiles), desc=f"Profiles in {os.path.basename(file_path)}", leave=False):
                profile_slice = ds.isel(N_PROF=i)
                
                try:
                    # --- Create the base DataFrame for measurements ---
                    measurement_vars = {
                        v_name: v_arr.values for v_name, v_arr in profile_slice.data_vars.items()
                        if 'N_LEVELS' in v_arr.dims
                    }
                    measurements_df = pd.DataFrame(measurement_vars)
                    
                    # A profile must have pressure data to be valid
                    if 'PRES' not in measurements_df.columns or measurements_df['PRES'].isnull().all():
                        continue

                    measurements_df.dropna(subset=['PRES'], inplace=True)
                    if measurements_df.empty:
                        continue

                    # --- Add profile-level data by intelligently flattening ---
                    for var_name, data_array in profile_slice.data_vars.items():
                        if 'N_LEVELS' not in data_array.dims:
                            squeezed_val = data_array.squeeze().values
                            
                            # If it's a single scalar value after squeezing
                            if squeezed_val.ndim == 0:
                                value = squeezed_val.item()
                                if isinstance(value, bytes):
                                    value = value.decode('utf-8', 'ignore').strip()
                                measurements_df[var_name] = value
                            # If it's a 1D array (like STATION_PARAMETERS)
                            elif squeezed_val.ndim == 1:
                                # Convert the array to a single comma-separated string
                                str_value = ','.join([
                                    item.decode('utf-8', 'ignore').strip() if isinstance(item, bytes) else str(item)
                                    for item in squeezed_val
                                ])
                                measurements_df[var_name] = str_value
                            # We ignore more complex multi-dimensional metadata to avoid errors
                    
                    all_profiles_df_list.append(measurements_df)

                except Exception as e:
                    wmo_id = profile_slice.get('PLATFORM_NUMBER', 'N/A').values
                    logging.warning(f"Skipping a malformed profile for float {wmo_id} in {os.path.basename(file_path)} due to: {e}")
                    continue
        
        if not all_profiles_df_list:
            return None
        
        # Use object dtype to handle mixed types from different files gracefully
        return pd.concat(all_profiles_df_list, ignore_index=True).astype('object')

    except Exception as e:
        logging.error(f"Failed to read or process file {os.path.basename(file_path)}: {e}")
        return None

def main():
    """Main function to find all NetCDF files and export their complete data to a single CSV."""
    logging.info(f"--- Starting Full ARGO Data Export to CSV ---")
    
    nc_files = sorted(glob.glob(os.path.join(NC_FILES_DIRECTORY, '*_prof.nc')))
    if not nc_files:
        logging.error(f"No NetCDF files found in directory: {NC_FILES_DIRECTORY}")
        return
        
    logging.info(f"Found {len(nc_files)} files to process.")

    all_dataframes = []
    for nc_file in tqdm(nc_files, desc="Processing Files"):
        df = process_nc_file_to_df(nc_file)
        if df is not None and not df.empty:
            all_dataframes.append(df)

    if not all_dataframes:
        logging.error("No valid data was extracted from any of the files.")
        return

    logging.info("Concatenating all data into a final DataFrame...")
    # This final concat handles columns that may not exist in all files
    final_df = pd.concat(all_dataframes, ignore_index=True)

    logging.info(f"Saving {len(final_df)} data points to '{OUTPUT_CSV_FILE}'...")
    final_df.to_csv(OUTPUT_CSV_FILE, index=False)
    
    logging.info("--- Export Finished Successfully! ---")
    logging.info(f"All data saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    main()

