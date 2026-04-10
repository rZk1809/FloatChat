import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
# Import seaborn for the pairplot
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    print("Warning: Seaborn not found. Pairplot will be skipped. Install with 'pip install seaborn'.")

from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (silhouette_score, calinski_harabasz_score,
                             davies_bouldin_score)
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

# Ensure plots directory exists
os.makedirs('plots', exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_prepare_data(file_path):
    """Loads the 8-column CSV and prepares it for clustering."""
    logging.info(f"Loading data from '{file_path}'...")
    try:
        # Load only the features needed for clustering
        df = pd.read_csv(file_path, usecols=['latitude', 'longitude', 'temp', 'psal'])
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None, None
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None, None

    # --- Preprocessing ---
    initial_shape = df.shape
    df.dropna(subset=['temp', 'psal'], inplace=True)
    logging.info(f"Data shape after dropping NaNs (temp, psal): {df.shape} (Dropped {initial_shape[0] - df.shape[0]} rows)")

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
    silhouette_scores = []
    ch_scores = []
    db_scores = []

    for k in tqdm(K_RANGE, desc="Testing k values"):
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, n_init='auto', batch_size=1024)
        cluster_labels = kmeans.fit_predict(data_sample)
        inertias.append(kmeans.inertia_)

        # Calculate metrics if k > 1
        if k > 1:
            sil_score = silhouette_score(data_sample, cluster_labels, sample_size=min(sample_size, len(data_sample)))
            silhouette_scores.append(sil_score)

            ch_score = calinski_harabasz_score(data_sample, cluster_labels)
            ch_scores.append(ch_score)

            db_score = davies_bouldin_score(data_sample, cluster_labels)
            db_scores.append(db_score)
        else:
            # Append None or np.nan for k=1 as these metrics are not defined
            silhouette_scores.append(np.nan)
            ch_scores.append(np.nan)
            db_scores.append(np.nan)

    # --- Plotting the Elbow Method ---
    plt.figure(figsize=(10, 6))
    plt.plot(K_RANGE, inertias, 'bo-', label='Inertia')
    plt.xlabel('Number of clusters (k)')
    plt.ylabel('Inertia (Sum of squared distances)')
    plt.title('Elbow Method For Optimal k')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join('plots', 'elbow_method.png'))
    logging.info("Elbow method plot saved to 'plots/elbow_method.png'")
    plt.show()

    # --- Plotting Additional Metrics ---
    if any(not np.isnan(score) for score in silhouette_scores):
        plt.figure(figsize=(18, 5))

        plt.subplot(1, 3, 1)
        plt.plot(K_RANGE, silhouette_scores, 'go-')
        plt.xlabel('Number of clusters (k)')
        plt.ylabel('Silhouette Score')
        plt.title('Silhouette Score vs. k')
        plt.grid(True)

        plt.subplot(1, 3, 2)
        plt.plot(K_RANGE, ch_scores, 'ro-')
        plt.xlabel('Number of clusters (k)')
        plt.ylabel('Calinski-Harabasz Score')
        plt.title('Calinski-Harabasz Score vs. k')
        plt.grid(True)

        plt.subplot(1, 3, 3)
        plt.plot(K_RANGE, db_scores, 'mo-')
        plt.xlabel('Number of clusters (k)')
        plt.ylabel('Davies-Bouldin Score')
        plt.title('Davies-Bouldin Score vs. k')
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(os.path.join('plots', 'clustering_metrics.png'))
        logging.info("Clustering metrics plot saved to 'plots/clustering_metrics.png'")
        plt.show()


def train_kmeans_and_evaluate(data_scaled, data_original):
    """
    Trains the K-Means model with the optimal k and evaluates its performance.
    """
    if OPTIMAL_K not in K_RANGE:
        logging.warning(f"OPTIMAL_K ({OPTIMAL_K}) is not within the tested K_RANGE ({list(K_RANGE)}). "
                        f"Using K={min(K_RANGE)} for evaluation.")
        k_to_use = min(K_RANGE)
    else:
        k_to_use = OPTIMAL_K

    logging.info(f"Training MiniBatchKMeans model with k={k_to_use} on the full dataset...")
    kmeans = MiniBatchKMeans(n_clusters=k_to_use, random_state=42, n_init='auto', batch_size=2048)
    # Fit on the full scaled dataset and predict
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
    sil_score = silhouette_score(data_sample, clusters_sample, sample_size=min(SAMPLE_SIZE, len(data_sample)))
    logging.info(f"Silhouette Score (k={k_to_use}): {sil_score:.4f}")
    logging.info("(Measures how distinct the clusters are. Closer to +1 is better.)")

    # 2. Calinski-Harabasz Score
    ch_score = calinski_harabasz_score(data_sample, clusters_sample)
    logging.info(f"Calinski-Harabasz Score (k={k_to_use}): {ch_score:.2f}")
    logging.info("(Ratio of between-cluster to within-cluster dispersion. Higher is better.)")
    
    # 3. Davies-Bouldin Score
    db_score = davies_bouldin_score(data_sample, clusters_sample)
    logging.info(f"Davies-Bouldin Score (k={k_to_use}): {db_score:.4f}")
    logging.info("(Average similarity between each cluster and its most similar one. Lower is better, minimum is 0.)")

    # 4. Cluster Sizes
    unique, counts = np.unique(clusters, return_counts=True)
    cluster_sizes = dict(zip(unique, counts))
    logging.info(f"Cluster Sizes (k={k_to_use}): {cluster_sizes}")

    # 5. Cluster Centroids (Mean of original features)
    scaler = StandardScaler()
    scaler.fit(data_original[['temp', 'psal']]) # Fit scaler on original data to inverse transform
    centroids_scaled = kmeans.cluster_centers_
    centroids_original = scaler.inverse_transform(centroids_scaled)
    centroid_df = pd.DataFrame(centroids_original, columns=['temp', 'psal'])
    centroid_df.index.name = 'cluster'
    logging.info(f"Cluster Centroids (Original Scale):\n{centroid_df}")

    # Add centroids to results for plotting
    results = {
        'data_with_clusters': data_original,
        'cluster_sizes': cluster_sizes,
        'centroids': centroid_df
    }
    return results

def plot_results(results):
    """
    Generates and saves visualizations of the clustering results.
    """
    df_with_clusters = results['data_with_clusters']
    cluster_sizes = results['cluster_sizes']
    centroids = results['centroids']
    k_value = len(centroids) # Get k from centroids

    logging.info("Generating visualizations...")
    
    # Use a sample for plotting to avoid over-cluttering
    df_sample = df_with_clusters.sample(n=min(len(df_with_clusters), SAMPLE_SIZE), random_state=42)

    # --- 1. Temperature-Salinity (T-S) Diagram ---
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(df_sample['psal'], df_sample['temp'], c=df_sample['cluster'], cmap='tab10', s=5, alpha=0.7)
    # Add centroids
    plt.scatter(centroids['psal'], centroids['temp'], c=centroids.index, cmap='tab10', marker='x', s=200, linewidths=3, label='Centroids')
    plt.xlabel('Salinity (psu)')
    plt.ylabel('Temperature (°C)')
    plt.title(f'Water Mass Clusters on a T-S Diagram (k={k_value})')
    plt.grid(True)
    plt.legend(*scatter.legend_elements(), title="Clusters")
    plt.savefig(os.path.join('plots', 'ts_diagram_clusters.png'))
    logging.info("T-S Diagram saved to 'plots/ts_diagram_clusters.png'")
    plt.show()

    # --- 2. Geospatial Distribution of Water Masses ---
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
    ax.stock_img()

    scatter_map = ax.scatter(df_sample['longitude'], df_sample['latitude'], c=df_sample['cluster'],
                             cmap='tab10', s=5, alpha=0.7, transform=ccrs.PlateCarree()) # Use PlateCarree for transform
    
    plt.title(f'Geographic Distribution of Water Mass Clusters (k={k_value})')
    plt.legend(*scatter_map.legend_elements(), title="Clusters")
    plt.savefig(os.path.join('plots', 'map_clusters.png'))
    logging.info("Geospatial map of clusters saved to 'plots/map_clusters.png'")
    plt.show()

    # --- 3. Cluster Size Bar Chart ---
    plt.figure(figsize=(10, 6))
    clusters_list = list(cluster_sizes.keys())
    counts_list = list(cluster_sizes.values())
    bars = plt.bar(clusters_list, counts_list, color=plt.cm.tab10(clusters_list))
    plt.xlabel('Cluster ID')
    plt.ylabel('Number of Data Points')
    plt.title(f'Size of Each Water Mass Cluster (k={k_value})')
    plt.xticks(clusters_list)
    # Add count labels on bars
    for bar, count in zip(bars, counts_list):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01 * max(counts_list),
                 f'{count}', ha='center', va='bottom')
    plt.grid(axis='y')
    plt.savefig(os.path.join('plots', 'cluster_sizes.png'))
    logging.info("Cluster size bar chart saved to 'plots/cluster_sizes.png'")
    plt.show()

    # --- 4. Pairplot (if seaborn is available) ---
    if SEABORN_AVAILABLE and len(df_sample.columns) >= 4:
        plt.figure(figsize=(12, 10))
        # Use a smaller sample for pairplot due to computational intensity
        df_pairplot_sample = df_sample[['latitude', 'longitude', 'temp', 'psal', 'cluster']].sample(n=min(10000, len(df_sample)), random_state=42)
        sns_plot = sns.pairplot(df_pairplot_sample, hue='cluster', palette='tab10', plot_kws={'alpha': 0.6, 's': 10})
        sns_plot.fig.suptitle(f'Pairplot of Features by Cluster (k={k_value})', y=1.02)
        sns_plot.savefig(os.path.join('plots', 'pairplot_clusters.png'))
        logging.info("Pairplot saved to 'plots/pairplot_clusters.png'")
        plt.show()
    elif not SEABORN_AVAILABLE:
        logging.info("Skipping pairplot as Seaborn is not available.")
    else:
        logging.info("Skipping pairplot as data does not have enough features.")


    # --- 5. Individual Histograms for Temp and Salinity per Cluster ---
    # Determine number of clusters for subplots
    n_clusters = len(centroids)
    n_cols = 3
    n_rows = int(np.ceil(n_clusters / n_cols))

    # Temperature Histograms
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
    axes = axes.flatten() if n_clusters > 1 else [axes]
    for i in range(n_clusters):
        cluster_data = df_with_clusters[df_with_clusters['cluster'] == i]
        axes[i].hist(cluster_data['temp'], bins=50, alpha=0.7, color=plt.cm.tab10(i), edgecolor='black', linewidth=0.5)
        axes[i].set_title(f'Cluster {i} (n={cluster_sizes.get(i, 0)})')
        axes[i].set_xlabel('Temperature (°C)')
        axes[i].set_ylabel('Frequency')
        axes[i].grid(True, alpha=0.3)
    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    plt.suptitle(f'Distribution of Temperature within Clusters (k={k_value})')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join('plots', 'temp_histograms_per_cluster.png'))
    logging.info("Temperature histograms per cluster saved to 'plots/temp_histograms_per_cluster.png'")
    plt.show()

    # Salinity Histograms
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
    axes = axes.flatten() if n_clusters > 1 else [axes]
    for i in range(n_clusters):
        cluster_data = df_with_clusters[df_with_clusters['cluster'] == i]
        axes[i].hist(cluster_data['psal'], bins=50, alpha=0.7, color=plt.cm.tab10(i), edgecolor='black', linewidth=0.5)
        axes[i].set_title(f'Cluster {i} (n={cluster_sizes.get(i, 0)})')
        axes[i].set_xlabel('Salinity (psu)')
        axes[i].set_ylabel('Frequency')
        axes[i].grid(True, alpha=0.3)
    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    plt.suptitle(f'Distribution of Salinity within Clusters (k={k_value})')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join('plots', 'salinity_histograms_per_cluster.png'))
    logging.info("Salinity histograms per cluster saved to 'plots/salinity_histograms_per_cluster.png'")
    plt.show()

def main():
    """Main function to run the water mass clustering project."""
    df, df_scaled = load_and_prepare_data(CSV_FILE_PATH)
    
    if df is not None and df_scaled is not None:
        find_optimal_clusters(df_scaled, SAMPLE_SIZE)
        results = train_kmeans_and_evaluate(df_scaled, df)
        plot_results(results)
        logging.info("--- Analysis Complete ---")

if __name__ == "__main__":
    main()