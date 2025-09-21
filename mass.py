import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from tqdm import tqdm
import logging

# --- Configuration ---
CSV_FILE_PATH = "argo_data_export.csv"
# We'll use a subsample of the data for EDA and plotting to keep it fast and clear.
# The model will be trained on the full dataset.
SAMPLE_SIZE = 200000 
# The range of cluster numbers to test for the Elbow Method
K_RANGE = range(2, 11) 
# The optimal number of clusters found from the Elbow plot (adjust if your plot suggests a different number)
OPTIMAL_K = 4 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_prepare_data(file_path):
    """Loads the 8-column CSV and prepares it for clustering."""
    logging.info(f"Loading data from '{file_path}'...")
    try:
        df = pd.read_csv(file_path, usecols=['latitude', 'longitude', 'temp', 'psal'])
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None, None

    # --- Preprocessing ---
    df.dropna(subset=['temp', 'psal'], inplace=True)
    logging.info(f"Data shape after dropping NaNs: {df.shape}")

    if df.empty:
        logging.error("No data left after cleaning.")
        return None, None

    # --- Feature Scaling ---
    # K-Means is sensitive to feature scales, so we standardize the data.
    logging.info("Scaling temperature and salinity features...")
    features = ['temp', 'psal']
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[features])
    
    return df, df_scaled

def find_optimal_clusters(data_scaled, sample_size):
    """
    Uses the Elbow Method to find the optimal number of clusters (k).
    """
    logging.info("Finding optimal number of clusters using the Elbow Method...")
    
    # Use a sample for speed
    if len(data_scaled) > sample_size:
        sample_indices = np.random.choice(data_scaled.shape[0], sample_size, replace=False)
        data_sample = data_scaled[sample_indices, :]
    else:
        data_sample = data_scaled

    inertias = []
    for k in tqdm(K_RANGE, desc="Testing k values"):
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, n_init='auto')
        kmeans.fit(data_sample)
        inertias.append(kmeans.inertia_)

    # --- Plotting the Elbow Method ---
    plt.figure(figsize=(10, 6))
    plt.plot(K_RANGE, inertias, 'bo-')
    plt.xlabel('Number of clusters (k)')
    plt.ylabel('Inertia (Sum of squared distances)')
    plt.title('Elbow Method For Optimal k')
    plt.grid(True)
    
    # Save the plot
    if not os.path.exists('plots'):
        os.makedirs('plots')
    plt.savefig('plots/elbow_method.png')
    logging.info("Elbow method plot saved to 'plots/elbow_method.png'")
    plt.show()

def train_kmeans_and_evaluate(data_scaled, data_original):
    """
    Trains the K-Means model with the optimal k and evaluates its performance.
    """
    logging.info(f"Training MiniBatchKMeans model with k={OPTIMAL_K} on the full dataset...")
    kmeans = MiniBatchKMeans(n_clusters=OPTIMAL_K, random_state=42, n_init='auto', batch_size=2048)
    # Fit on the full scaled dataset
    clusters = kmeans.fit_predict(data_scaled)
    data_original['cluster'] = clusters
    logging.info("Model training and cluster assignment complete.")

    # --- In-depth Model Evaluation ---
    logging.info("Calculating performance metrics...")
    # Use a sample for metrics calculation as it can be very slow on millions of points
    if len(data_scaled) > SAMPLE_SIZE:
        sample_indices = np.random.choice(data_scaled.shape[0], SAMPLE_SIZE, replace=False)
        data_sample = data_scaled[sample_indices, :]
        clusters_sample = clusters[sample_indices]
    else:
        data_sample = data_scaled
        clusters_sample = clusters

    # 1. Silhouette Score
    sil_score = silhouette_score(data_sample, clusters_sample)
    logging.info(f"Silhouette Score: {sil_score:.3f}")
    logging.info("(Measures how distinct the clusters are. Closer to +1 is better.)")

    # 2. Calinski-Harabasz Score
    ch_score = calinski_harabasz_score(data_sample, clusters_sample)
    logging.info(f"Calinski-Harabasz Score: {ch_score:.3f}")
    logging.info("(Ratio of between-cluster to within-cluster dispersion. Higher is better.)")
    
    # 3. Davies-Bouldin Score
    db_score = davies_bouldin_score(data_sample, clusters_sample)
    logging.info(f"Davies-Bouldin Score: {db_score:.3f}")
    logging.info("(Average similarity between each cluster and its most similar one. Lower is better, minimum is 0.)")

    return data_original

def plot_results(df_with_clusters):
    """
    Generates and saves visualizations of the clustering results.
    """
    logging.info("Generating visualizations...")
    
    # Use a sample for plotting to avoid over-cluttering
    df_sample = df_with_clusters.sample(n=min(len(df_with_clusters), SAMPLE_SIZE), random_state=42)

    # --- 1. Temperature-Salinity (T-S) Diagram ---
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(df_sample['psal'], df_sample['temp'], c=df_sample['cluster'], cmap='viridis', s=5, alpha=0.7)
    plt.xlabel('Salinity (psu)')
    plt.ylabel('Temperature (°C)')
    plt.title('Water Mass Clusters on a Temperature-Salinity (T-S) Diagram')
    plt.grid(True)
    plt.legend(handles=scatter.legend_elements()[0], labels=[f'Water Mass {i}' for i in range(OPTIMAL_K)])
    plt.savefig('plots/ts_diagram_clusters.png')
    logging.info("T-S Diagram saved to 'plots/ts_diagram_clusters.png'")
    plt.show()

    # --- 2. Geospatial Distribution of Water Masses ---
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.stock_img()

    scatter_map = ax.scatter(df_sample['longitude'], df_sample['latitude'], c=df_sample['cluster'],
                             cmap='viridis', s=5, alpha=0.7, transform=ccrs.Geodetic())
    
    plt.title('Geographic Distribution of Water Mass Clusters')
    plt.legend(handles=scatter_map.legend_elements()[0], labels=[f'Water Mass {i}' for i in range(OPTIMAL_K)])
    plt.savefig('plots/map_clusters.png')
    logging.info("Geospatial map of clusters saved to 'plots/map_clusters.png'")
    plt.show()

def main():
    """Main function to run the water mass clustering project."""
    df, df_scaled = load_and_prepare_data(CSV_FILE_PATH)
    
    if df is not None:
        find_optimal_clusters(df_scaled, SAMPLE_SIZE)
        df_with_clusters = train_kmeans_and_evaluate(df_scaled, df)
        plot_results(df_with_clusters)

if __name__ == "__main__":
    main()
