import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import BallTree
from sklearn.metrics import silhouette_score # <-- Import the metric
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
        return None, None, None

    # --- Feature Engineering & Cleaning ---
    df.dropna(inplace=True)
    logging.info(f"Data shape after dropping NaNs: {df.shape}")

    if df.empty:
        logging.error("No data left after dropping missing values.")
        return None, None, None

    # Using a smaller sample for faster metric calculation if the dataset is huge
    if len(df) > 200000:
        logging.info("Subsampling data to 200,000 points for efficient metric calculation...")
        df = df.sample(n=200000, random_state=42)

    features = ['latitude', 'longitude', 'pressure', 'temp', 'psal']
    
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

    inlier_sample = inliers.sample(n=min(len(inliers), 50000), random_state=42)
    plt.scatter(inlier_sample['longitude'], inlier_sample['latitude'], 
                color='blue', s=2, alpha=0.3, transform=ccrs.Geodetic(), label='Normal Points (Sample)')

    plt.scatter(anomalies['longitude'], anomalies['latitude'], 
                color='red', s=10, transform=ccrs.Geodetic(), label='Anomalous Points')

    plt.title('Geographic Distribution of Anomalous Data Points')
    plt.legend()
    plt.show()

def plot_profile_comparison(df_with_anomalies, num_to_plot=3):
    """
    Selects random anomalies and plots their profiles against nearby normal profiles.
    """
    # Create a unique identifier for each profile
    df_with_anomalies['profile_id'] = df_with_anomalies['wmo_id'].astype(str) + '_' + df_with_anomalies['cycle_number'].astype(str)
    
    # Get the unique IDs of the anomalous profiles
    anomalous_profile_ids = df_with_anomalies[df_with_anomalies['anomaly'] == -1]['profile_id'].unique()
    
    if len(anomalous_profile_ids) == 0:
        logging.warning("No anomalies found to plot.")
        return

    # Select random profiles to plot
    profiles_to_plot = np.random.choice(anomalous_profile_ids, size=min(len(anomalous_profile_ids), num_to_plot), replace=False)

    # Separate inliers for the nearest neighbor search
    inliers = df_with_anomalies[df_with_anomalies['anomaly'] == 1]
    inliers_rad = np.deg2rad(inliers[['latitude', 'longitude']].values)
    tree = BallTree(inliers_rad, metric='haversine')

    for profile_id in profiles_to_plot:
        anomaly_full_profile = df_with_anomalies[df_with_anomalies['profile_id'] == profile_id]
        
        # Take the location from the first point of the anomalous profile
        anomaly_profile_meta = anomaly_full_profile.iloc[0]
        ano_wmo = int(anomaly_profile_meta['wmo_id'])
        ano_cycle = int(anomaly_profile_meta['cycle_number'])
        ano_coords_rad = np.deg2rad([[anomaly_profile_meta['latitude'], anomaly_profile_meta['longitude']]])

        # Find the 5 nearest inlier points (which will belong to neighbor profiles)
        dist, ind = tree.query(ano_coords_rad, k=5)
        neighbor_points = inliers.iloc[ind[0]]
        neighbor_profile_ids = neighbor_points['profile_id'].unique()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), sharey=True)
        fig.suptitle(f'Anomaly Comparison for Float {ano_wmo}, Cycle {ano_cycle}', fontsize=16)

        # Plot neighbor profiles in the background
        for neighbor_id in neighbor_profile_ids:
            neighbor_full_profile = df_with_anomalies[df_with_anomalies['profile_id'] == neighbor_id]
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
        
        # --- Quantitative Evaluation: Silhouette Score ---
        logging.info("Calculating Silhouette Score to measure anomaly separation...")
        # A sample is used here because calculating silhouette score on millions of points is very slow.
        score = silhouette_score(df_scaled, predictions, metric='euclidean')
        logging.info(f"--- Model Performance ---")
        logging.info(f"Silhouette Score: {score:.3f}")
        logging.info("(A score closer to +1 indicates well-separated anomalies, while a score near 0 indicates overlapping clusters).")
        
        # --- Visual Evaluation ---
        # The main logic for plotting remains the same, but we'll use the modified df
        plot_anomaly_map(df)
        plot_profile_comparison(df)

if __name__ == "__main__":
    main()

