import os
import requests
from tqdm import tqdm
from datetime import datetime
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import tempfile
from pathlib import Path

# --- Configuration ---
BASE_URL = "https://nrlgodae1.nrlmry.navy.mil/ftp/outgoing/argo/geo/indian_ocean/" # Fixed trailing space
YEARS_TO_DOWNLOAD = [2024] # Example: Downloading 2024 data
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = Path(os.environ.get("ARGO_NC_DIR", PROJECT_ROOT / "DATASET1")).resolve()
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024
MAX_WORKERS = 5  # Number of parallel download threads

# --- Threading lock for print statements ---
print_lock = threading.Lock()

# --- HTML Parser to find links on the FTP index pages ---
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)

def get_links(url):
    """Fetches a URL and returns all href links found on the page."""
    try:
        response = requests.get(url, timeout=(5, 30))
        response.raise_for_status()  # Raises an exception for bad status codes
        parser = LinkParser()
        parser.feed(response.text)
        return parser.links
    except requests.exceptions.RequestException as e:
        with print_lock:
            print(f"Could not fetch links from {url}: {e}")
        return []

def download_file(url, local_path):
    """Downloads a single file."""
    destination = Path(local_path).resolve()
    if destination.parent != LOCAL_DATA_DIR or destination.exists():
        raise ValueError("Download target must be a new file inside ARGO_NC_DIR")
    temp_name = None
    try:
        response = requests.get(url, stream=True, timeout=(5, 30))
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        if total_size > MAX_DOWNLOAD_BYTES:
            raise ValueError("Remote file exceeds the configured size limit")

        received = 0
        with tempfile.NamedTemporaryFile(dir=LOCAL_DATA_DIR, suffix=".part", delete=False) as f:
            temp_name = f.name
            # Use a local tqdm instance for cleaner output in multithreaded environment
            with tqdm(
                desc=os.path.basename(local_path),
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                leave=False, # Prevents cluttering the output
                position=threading.get_ident() % 10 # Tries to separate progress bars
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    received += len(data)
                    if received > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Download exceeded the configured size limit")
                    size = f.write(data)
                    bar.update(size)
        os.link(f.name, destination)
        os.unlink(f.name)
        with print_lock:
            print(f"Downloaded: {local_path}")
        return True
    except requests.exceptions.RequestException as e:
        with print_lock:
            print(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        with print_lock:
            print(f"Unexpected error downloading {url}: {e}")
        return False
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)

def visualize_argo_locations(file_path):
    """Visualize ARGO float locations from a NetCDF file."""
    try:
        import xarray as xr
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import numpy as np

        # Check if file exists before trying to open
        if not os.path.exists(file_path):
             print(f"File not found for visualization: {file_path}")
             return

        print(f"Visualizing locations from: {file_path}")
        # Load dataset (decode_timedelta can help with time variables)
        ds = xr.open_dataset(file_path, decode_timedelta=True)

        # Get coordinates (assuming standard ARGO variable names)
        if 'LONGITUDE' in ds and 'LATITUDE' in ds:
            lons = ds['LONGITUDE'].values
            lats = ds['LATITUDE'].values
        elif 'lon' in ds and 'lat' in ds: # Sometimes variables are named 'lon', 'lat'
             lons = ds['lon'].values
             lats = ds['lat'].values
        else:
             print("Could not find longitude/latitude variables in the NetCDF file.")
             ds.close()
             return

        # Handle potential masked arrays or NaNs using numpy
        # Ensure lons and lats are NumPy arrays for compatibility
        lons = np.asarray(lons)
        lats = np.asarray(lats)
        # Create a mask for valid (non-NaN) values in both arrays
        valid_mask = ~(np.isnan(lons) | np.isnan(lats))
        lons = lons[valid_mask]
        lats = lats[valid_mask]

        if len(lons) == 0:
            print("No valid locations found in the file.")
            ds.close()
            return

        # Create plot
        plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.gridlines(draw_labels=True, linestyle='--', linewidth=0.5)
        ax.set_extent([40, 100, -20, 30], crs=ccrs.PlateCarree()) # Indian Ocean extent

        # Plot locations
        sc = ax.scatter(lons, lats, color='red', s=10, transform=ccrs.PlateCarree(), label=f'{len(lons)} Profiles', alpha=0.7)
        ax.set_title(f'ARGO Float Locations - {os.path.basename(file_path)}')
        ax.legend(loc='lower left')
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error visualizing file {file_path}: {e}")
    finally:
        # Ensure the dataset is closed if it was opened
        try:
            ds.close()
        except:
            pass

def collect_files_to_download():
    """Collects all files that need to be downloaded."""
    files_to_download = []
    print("--- Collecting files to download ---")

    # Create the local data directory if it doesn't exist
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    print(f"Data will be saved in: {os.path.abspath(LOCAL_DATA_DIR)}")

    current_year = datetime.now().year
    current_month = datetime.now().month

    for year in YEARS_TO_DOWNLOAD:
        year_url = f"{BASE_URL}{year}/"
        with print_lock:
            print(f"\nProcessing Year: {year}")

        month_links = get_links(year_url)
        # Filter for month directories (e.g., '01/', '02/' - they end with '/')
        month_dirs = [m for m in month_links if m.endswith('/') and m[:-1].isdigit() and len(m[:-1]) == 2]

        if not month_dirs:
             with print_lock:
                 print(f"No month directories found for year {year}.")
             continue

        for month_dir in sorted(month_dirs):
            month_str = month_dir.strip('/')
            # For the current year, don't try to download future months
            if year == current_year and int(month_str) > current_month:
                with print_lock:
                    print(f"Skipping future month {month_str} of current year {year}.")
                continue

            month_url = f"{year_url}{month_dir}"
            with print_lock:
                print(f"  -> Checking Month: {month_str}")

            file_links = get_links(month_url)
            # Filter for the profile NetCDF files
            nc_files = [
                f for f in file_links
                if f.endswith('_prof.nc') and Path(f).name == f
            ]

            if not nc_files:
                with print_lock:
                    print(f"    No profile files found for {year}-{month_str}.")
                continue

            for nc_file in nc_files:
                file_url = f"{month_url}{nc_file}"
                local_file_path = os.path.join(LOCAL_DATA_DIR, nc_file)

                # Check if file already exists to avoid re-downloading
                if not os.path.exists(local_file_path):
                    files_to_download.append((file_url, local_file_path))
                    # print(f"    Queued for download: {nc_file}") # Can be verbose
                else:
                    with print_lock:
                        print(f"    Skipping {nc_file} (already exists).")

    print(f"--- Found {len(files_to_download)} files to download ---")
    return files_to_download

def main():
    """Main function to orchestrate the download process."""
    print("--- Starting ARGO Data Download for Indian Ocean (Multithreaded) ---")

    # Step 1: Collect all files to download
    files_to_download = collect_files_to_download()

    if not files_to_download:
        print("No new files to download.")
        return

    downloaded_files = []
    failed_downloads = []

    # Step 2: Download files using ThreadPoolExecutor
    print(f"\n--- Starting download of {len(files_to_download)} files using {MAX_WORKERS} threads ---")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all download tasks
        future_to_file = {executor.submit(download_file, url, path): (url, path) for url, path in files_to_download}

        # Process completed downloads
        for future in as_completed(future_to_file):
            url, local_path = future_to_file[future]
            try:
                success = future.result()
                if success:
                    downloaded_files.append(local_path)
                else:
                    failed_downloads.append((url, local_path))
            except Exception as exc:
                with print_lock:
                    print(f'File {local_path} generated an exception: {exc}')
                failed_downloads.append((url, local_path))

    print(f"\n--- Download process complete! ---")
    print(f"Successfully downloaded: {len(downloaded_files)} files")
    if failed_downloads:
        print(f"Failed downloads: {len(failed_downloads)} files")
        # Optionally list failed files
        # for url, path in failed_downloads:
        #     print(f"  - {path} (from {url})")


    # --- Visualization ---
    # Visualize one of the downloaded files (e.g., the last one successfully downloaded)
    if downloaded_files:
        latest_file = downloaded_files[-1]
        print(f"\n--- Starting Visualization ---")
        visualize_argo_locations(latest_file)
        print("--- Visualization complete! ---")
    else:
        print("No files were downloaded successfully, skipping visualization.")

if __name__ == "__main__":
    main()
