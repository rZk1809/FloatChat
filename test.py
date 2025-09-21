import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# --- Load the NetCDF file (with the fix) ---
file_path = '/Users/admin/Documents/SIH/20250901_prof.nc'
ds = xr.open_dataset(file_path, decode_timedelta=True)

# --- Get the coordinates for ALL profiles ---
lons = ds['LONGITUDE'].values
lats = ds['LATITUDE'].values

# --- Create a map ---
plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines()
ax.gridlines(draw_labels=True)
ax.stock_img()


# --- Add a marker for EACH float location ---
plt.scatter(lons, lats, color='red', s=10, transform=ccrs.Geodetic(), label=f'{len(lons)} Profile Locations')
plt.title('Locations of all 67 ARGO Profiles in the file')
plt.legend()
plt.show()