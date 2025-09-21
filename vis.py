import os
import glob
import xarray as xr

# --- Configuration ---
# The directory where your downloaded .nc files are stored.
NC_FILES_DIRECTORY = "DATASET"

# How many files do 1ou want to inspect? Change this number as needed.
FILES_TO_INSPECT = 10

def inspect_netcdf_files():
    """
    Scans a directory for NetCDF files and prints a detailed summary
    of the contents for a specified number of files.
    """
    print(f"--- Starting NetCDF File Inspection ---")
    print(f"Target directory: '{NC_FILES_DIRECTORY}'")
    print(f"Number of files to inspect: {FILES_TO_INSPECT}\n")

    # Find all files ending with _prof.nc in the directory
    nc_files = sorted(glob.glob(os.path.join(NC_FILES_DIRECTORY, '*_prof.nc')))

    if not nc_files:
        print(f"Error: No NetCDF files ending with '_prof.nc' were found in the directory: {NC_FILES_DIRECTORY}")
        return

    # Take a slice of the list for the number of files we want to inspect
    files_to_process = nc_files[:FILES_TO_INSPECT]
    
    print(f"Found {len(nc_files)} total files. Inspecting the first {len(files_to_process)}.\n")

    for i, file_path in enumerate(files_to_process):
        print("="*80)
        print(f"INSPECTING FILE {i+1}/{len(files_to_process)}: {os.path.basename(file_path)}")
        print("="*80)
        
        try:
            # Open the dataset using xarray. The 'with' statement ensures it's properly closed.
            with xr.open_dataset(file_path, decode_timedelta=True) as ds:
                # Print the high-level summary first
                print("--- High-Level Summary ---")
                print(ds)

                # Now, print a detailed list of all data variables
                print("\n--- Detailed Data Variables List ---")
                for var_name, data_array in ds.data_vars.items():
                    print(f"\n[+] Variable: {var_name}")
                    print(f"  - Dimensions: {data_array.dims}")
                    print(f"  - Shape: {data_array.shape}")
                    print(f"  - Attributes:")
                    # Loop through and print each attribute for the variable
                    for attr, value in data_array.attrs.items():
                        # Indent for readability
                        print(f"    - {attr}: {value}")


        except Exception as e:
            print(f"\n--- ERROR ---")
            print(f"Could not read or process file {os.path.basename(file_path)}.")
            print(f"Error details: {e}")
        
        print("\n")

if __name__ == "__main__":
    inspect_netcdf_files()

