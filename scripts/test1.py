import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

# --- Load the NetCDF file ---
file_path = '/Users/admin/Documents/SIH/DATASET/20240115_prof.nc'
ds = xr.open_dataset(file_path, decode_timedelta=True)

# --- Check the PRES variable ---
print("Pressure Variable Info:")
print(ds['PRES'].attrs)  # Look for scaling attributes like 'scale_factor' or 'add_offset'

# --- Try to scale the pressure ---
# Many ARGO files store pressure in a scaled format (e.g., integer * scale_factor)
# You can try common scaling factors:
scale_factors = [1.0, 0.01, 0.1]  # Try different factors

for sf in scale_factors:
    pres_scaled = ds['PRES'].values * sf
    print(f"\nScaling factor {sf}:")
    print(f"  Min: {pres_scaled.min():.2f}, Max: {pres_scaled.max():.2f}")
    
    # If the max value is around 1000-2000 dbar, it's likely correct
    if pres_scaled.max() > 100 and pres_scaled.min() < 0:
        print(f"  Looks promising! Using scaling factor {sf}.")
        break