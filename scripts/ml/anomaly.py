import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import BallTree
import logging

# --- Configuration ---
# Using the simpler 8-column CSV for this task
CSV_FILE_PATH = "argo_data_export.csv" 
# Contamination is the expected proportion of outliers in the data set. 
# It's a key parameter for Isolation Forest. Let's assume 1% are anomalies.
CONTAMINATION_RATE = 0.01

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_prepare_data(file_path):
    """Loads the 8-column CSV and prepares it for ML."""
    logging.info(f"Loading data from '{file_path}'...")
    try:
        df = pd.read_csv(file_path)
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None

    # --- Feature Engineering & Cleaning ---
    # For simplicity, we drop rows with any missing values. 
    # A more advanced approach could use imputation.
    df.dropna(inplace=True)
    logging.info(f"Data shape after dropping NaNs: {df.shape}")

    if df.empty:
        logging.error("No data left after dropping missing values.")
        return None

    # Select the features for the model
    features = ['latitude', 'longitude', 'pressure', 'temp', 'psal']
    
    # --- Scaling Features ---
    # Anomaly detection models are sensitive to feature scales.
    logging.info("Scaling features using StandardScaler...")
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[features])
    
    return df, df_scaled, features

def train_and_predict(data_scaled):
    """Trains an Isolation Forest model and predicts anomalies."""
    logging.info("Training Isolation Forest model...")
    model = IsolationForest(contamination=CONTAMINATION_RATE, random_state=42, n_jobs=-1)
    predictions = model.fit_predict(data_scaled)
    logging.info("Model training and prediction complete.")
    
    # Add predictions to the original dataframe
    # Anomalies are marked as -1, inliers as 1.
    return predictions

def plot_anomaly_map(df_with_anomalies):
    """Plots a map showing the geographic location of normal vs. anomalous points."""
    logging.info("Generating anomaly location map...")
    
    anomalies = df_with_anomalies[df_with_anomalies['anomaly'] == -1]
    inliers = df_with_anomalies[df_with_anomalies['anomaly'] == 1]
    
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.stock_img()

    # Plot a sample of inliers to avoid overplotting
    inlier_sample = inliers.sample(n=min(len(inliers), 50000), random_state=42)
    plt.scatter(inlier_sample['longitude'], inlier_sample['latitude'], 
                color='blue', s=2, alpha=0.3, transform=ccrs.Geodetic(), label='Normal Points (Sample)')

    # Plot all anomalies
    plt.scatter(anomalies['longitude'], anomalies['latitude'], 
                color='red', s=10, transform=ccrs.Geodetic(), label='Anomalous Points')

    plt.title('Geographic Distribution of Anomalous Data Points')
    plt.legend()
    plt.show()

def plot_profile_comparison(df_with_anomalies, num_to_plot=3):
    """
    Selects random anomalies and plots their profiles against nearby normal profiles.
    """
    anomalies = df_with_anomalies[df_with_anomalies['anomaly'] == -1]
    inliers = df_with_anomalies[df_with_anomalies['anomaly'] == 1]

    if anomalies.empty:
        logging.warning("No anomalies found to plot.")
        return
        
    logging.info(f"Plotting profile comparisons for {num_to_plot} random anomalies...")
    
    # Use a BallTree for efficient nearest neighbor search on a sphere
    # Note: BallTree expects coordinates in radians
    inliers_rad = np.deg2rad(inliers[['latitude', 'longitude']].values)
    tree = BallTree(inliers_rad, metric='haversine')

    for i, anomaly_index in enumerate(anomalies.sample(n=min(len(anomalies), num_to_plot)).index):
        anomaly_profile = df_with_anomalies.loc[anomaly_index]
        ano_wmo = anomaly_profile['wmo_id']
        ano_cycle = anomaly_profile['cycle_number']
        ano_coords_rad = np.deg2rad([[anomaly_profile['latitude'], anomaly_profile['longitude']]])

        # Find the 5 nearest inlier profiles
        dist, ind = tree.query(ano_coords_rad, k=5)
        neighbor_indices = inliers.iloc[ind[0]].index
        
        # Get full profiles for the anomaly and its neighbors
        anomaly_full_profile = df_with_anomalies[(df_with_anomalies['wmo_id'] == ano_wmo) & (df_with_anomalies['cycle_number'] == ano_cycle)]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), sharey=True)
        fig.suptitle(f'Anomaly Comparison for Float {ano_wmo}, Cycle {ano_cycle}', fontsize=16)

        # Plot neighbor profiles in the background
        for neighbor_idx in neighbor_indices:
            neighbor_profile_meta = df_with_anomalies.loc[neighbor_idx]
            neighbor_full_profile = df_with_anomalies[(df_with_anomalies['wmo_id'] == neighbor_profile_meta['wmo_id']) & (df_with_anomalies['cycle_number'] == neighbor_profile_meta['cycle_number'])]
            ax1.plot(neighbor_full_profile['temp'], neighbor_full_profile['pressure'], color='gray', alpha=0.5, linewidth=1)
            ax2.plot(neighbor_full_profile['psal'], neighbor_full_profile['pressure'], color='gray', alpha=0.5, linewidth=1)

        # Plot the anomalous profile on top
        ax1.plot(anomaly_full_profile['temp'], anomaly_full_profile['pressure'], color='red', linewidth=2, label='Anomalous Profile')
        ax2.plot(anomaly_full_profile['psal'], anomaly_full_profile['pressure'], color='red', linewidth=2)
        
        ax1.set_xlabel('Temperature (°C)')
        ax1.set_ylabel('Pressure (dbar)')
        ax1.set_title('Temperature Profile')
        ax1.grid(True)
        ax1.legend()
        
        ax2.set_xlabel('Salinity (psu)')
        ax2.set_title('Salinity Profile')
        ax2.grid(True)

        plt.gca().invert_yaxis()
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

def main():
    """Main function to run the anomaly detection project."""
    df, df_scaled, features = load_and_prepare_data(CSV_FILE_PATH)
    
    if df is not None:
        predictions = train_and_predict(df_scaled)
        df['anomaly'] = predictions
        
        # We need the full profiles for plotting, so we merge the anomaly flag back
        # based on a unique profile identifier.
        profile_anomalies = df.groupby(['wmo_id', 'cycle_number'])['anomaly'].min().reset_index()
        profile_anomalies.rename(columns={'anomaly': 'profile_anomaly_flag'}, inplace=True)
        
        # Load the original data again to get full profiles
        full_df, _, _ = load_and_prepare_data(CSV_FILE_PATH)
        
        # This gives us a flag for each entire profile if any of its points were anomalous
        final_df = pd.merge(full_df, profile_anomalies, on=['wmo_id', 'cycle_number'])
        
        plot_anomaly_map(final_df.rename(columns={'profile_anomaly_flag': 'anomaly'}))
        plot_profile_comparison(final_df.rename(columns={'profile_anomaly_flag': 'anomaly'}))

if __name__ == "__main__":
    main()
