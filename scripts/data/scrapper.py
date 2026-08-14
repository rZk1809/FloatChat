import os
import requests
import tempfile
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from html.parser import HTMLParser

# --- Configuration ---
BASE_URL = "https://nrlgodae1.nrlmry.navy.mil/ftp/outgoing/argo/geo/indian_ocean/"
YEARS_TO_DOWNLOAD = [2025] # Example: Downloading 2024 data
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = Path(os.environ.get("ARGO_NC_DIR", PROJECT_ROOT / "DATASET")).resolve()
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024

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
        print(f"Could not fetch links from {url}: {e}")
        return []

def download_file(url, local_path):
    """Downloads a file with a progress bar."""
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
        with tempfile.NamedTemporaryFile(dir=LOCAL_DATA_DIR, suffix=".part", delete=False) as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            temp_name = f.name
            for data in response.iter_content(chunk_size=1024):
                received += len(data)
                if received > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download exceeded the configured size limit")
                size = f.write(data)
                bar.update(size)
        os.link(f.name, destination)
        os.unlink(f.name)
        print(f"Downloaded: {destination}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)

def visualize_argo_locations(file_path):
    """Visualize ARGO float locations from a NetCDF file."""
    try:
        import xarray as xr
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs

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
             return

        # Handle potential masked arrays or NaNs
        valid_mask = ~(xr.ufuncs.isnan(lons) | xr.ufuncs.isnan(lats))
        lons = lons[valid_mask]
        lats = lats[valid_mask]

        if len(lons) == 0:
            print("No valid locations found in the file.")
            return


        # Create plot
        plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.gridlines(draw_labels=True, linestyle='--')
        # ax.stock_img() # Optional background image
        ax.set_extent([40, 100, -20, 30], crs=ccrs.PlateCarree()) # Indian Ocean extent

        # Plot locations
        ax.scatter(lons, lats, color='red', s=10, transform=ccrs.PlateCarree(), label=f'{len(lons)} Profiles')
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

def main():
    """Main function to orchestrate the download process."""
    print("--- Starting ARGO Data Download for Indian Ocean ---")

    # Create the local data directory if it doesn't exist
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    print(f"Data will be saved in: {os.path.abspath(LOCAL_DATA_DIR)}")

    current_year = datetime.now().year
    current_month = datetime.now().month

    downloaded_files = [] # Keep track of downloaded files for visualization

    for year in YEARS_TO_DOWNLOAD:
        year_url = f"{BASE_URL}{year}/"
        print(f"\nProcessing Year: {year}")

        month_links = get_links(year_url)
        # Filter for month directories (e.g., '01/', '02/' - they end with '/')
        month_dirs = [m for m in month_links if m.endswith('/') and m[:-1].isdigit() and len(m[:-1]) == 2]

        if not month_dirs:
             print(f"No month directories found for year {year}.")
             continue

        for month_dir in sorted(month_dirs):
            month_str = month_dir.strip('/')
            # For the current year, don't try to download future months
            if year == current_year and int(month_str) > current_month:
                print(f"Skipping future month {month_str} of current year {year}.")
                continue

            month_url = f"{year_url}{month_dir}"
            print(f"  -> Month: {month_str}")

            file_links = get_links(month_url)
            # Filter for the profile NetCDF files
            nc_files = [
                f for f in file_links
                if f.endswith('_prof.nc') and Path(f).name == f
            ]

            if not nc_files:
                print(f"    No profile files found for {year}-{month_str}.")
                continue

            for nc_file in nc_files:
                file_url = f"{month_url}{nc_file}"
                local_file_path = os.path.join(LOCAL_DATA_DIR, nc_file)

                # Check if file already exists to avoid re-downloading
                if not os.path.exists(local_file_path):
                    print(f"    Downloading {nc_file}...")
                    download_file(file_url, local_file_path)
                else:
                    print(f"    Skipping {nc_file} (already exists).")

                # Add to list for potential visualization later
                downloaded_files.append(local_file_path)

    print("\n--- Download process complete! ---")

    # --- Visualization ---
    # Visualize one of the downloaded files (e.g., the last one)
    if downloaded_files:
        latest_file = downloaded_files[-1]
        print(f"\n--- Starting Visualization ---")
        visualize_argo_locations(latest_file)
        print("--- Visualization complete! ---")
    else:
        print("No files were downloaded, skipping visualization.")

if __name__ == "__main__":
    main()
