import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# Import necessary modules for new plots
from scipy import stats
try:
    from sklearn.inspection import PartialDependenceDisplay
    PDP_AVAILABLE = True
except ImportError:
    PDP_AVAILABLE = False
    print("Warning: sklearn.inspection.PartialDependenceDisplay not available. PDP plots will be skipped. Consider updating scikit-learn.")

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

# --- Configuration ---
CSV_FILE_PATH = "argo_data_export.csv"
# Use a smaller sample for faster development, set to None to use the full dataset
SAMPLE_SIZE = 500000 
TEST_SET_SIZE = 0.2
RANDOM_STATE = 42

# Ensure plots directory exists
os.makedirs('plots', exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_prepare_data(file_path):
    """Loads and preprocesses the ARGO data for SST prediction."""
    logging.info(f"Loading data from '{file_path}'...")
    try:
        df = pd.read_csv(file_path, usecols=['profile_date', 'latitude', 'longitude', 'pressure', 'temp'])
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None

    # --- Preprocessing ---
    logging.info("Preprocessing data...")
    # Filter for Sea Surface Temperature (SST) - pressure < 5 dbar
    df_sst = df[df['pressure'] < 5].copy()
    initial_count = len(df_sst)
    
    # Clean up
    df_sst.dropna(subset=['temp', 'latitude', 'longitude', 'profile_date'], inplace=True)
    
    # Convert date column
    df_sst['profile_date'] = pd.to_datetime(df_sst['profile_date'], errors='coerce')
    df_sst.dropna(subset=['profile_date'], inplace=True)

    final_count = len(df_sst)
    if SAMPLE_SIZE and final_count > SAMPLE_SIZE:
        logging.info(f"Subsampling data from {final_count} to {SAMPLE_SIZE} points for faster processing.")
        df_sst = df_sst.sample(n=SAMPLE_SIZE, random_state=RANDOM_STATE)
        final_count = len(df_sst)
        
    logging.info(f"Prepared dataset with {final_count} surface data points (Dropped {initial_count - final_count} rows during cleaning).")
    return df_sst

def feature_engineering(df):
    """Creates numerical features from raw data for the model."""
    logging.info("Performing feature engineering...")
    df_featured = df.copy()
    
    # --- Time-based features ---
    df_featured['day_of_year'] = df_featured['profile_date'].dt.dayofyear
    df_featured['month'] = df_featured['profile_date'].dt.month
    df_featured['year'] = df_featured['profile_date'].dt.year

    # --- Cyclical Feature Transformation ---
    # This helps the model understand cyclical nature (e.g., Dec 31st is close to Jan 1st)
    df_featured['day_sin'] = np.sin(2 * np.pi * df_featured['day_of_year'] / 365.25)
    df_featured['day_cos'] = np.cos(2 * np.pi * df_featured['day_of_year'] / 365.25)
    
    # Longitude is also cyclical
    df_featured['lon_sin'] = np.sin(2 * np.pi * df_featured['longitude'] / 360.0)
    df_featured['lon_cos'] = np.cos(2 * np.pi * df_featured['longitude'] / 360.0)

    # --- Final Feature Selection ---
    features = ['latitude', 'year', 'month', 'day_sin', 'day_cos', 'lon_sin', 'lon_cos']
    target = 'temp'
    
    X = df_featured[features]
    y = df_featured[target]
    
    logging.info(f"Created features: {features}")
    return X, y

def train_and_evaluate_model(X, y):
    """Splits data, trains an XGBoost model, and evaluates its performance."""
    logging.info("Splitting data into training and testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SET_SIZE, random_state=RANDOM_STATE)

    logging.info(f"Training XGBoost Regressor model on {len(X_train)} data points...")
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        early_stopping_rounds=50 # Stop training if performance doesn't improve
    )

    # Fit the model, using eval_set for early stopping
    # We don't use the callback anymore to ensure compatibility
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    logging.info(f"Model training complete. Best iteration: {model.best_iteration}.")

    # --- In-depth Model Evaluation ---
    logging.info("Evaluating model performance on the test set...")
    
    # Predictions for evaluation
    y_pred = model.predict(X_test)

    # --- Calculate Metrics ---
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    residuals = y_test - y_pred
    me = np.mean(residuals) # Mean Error / Bias
    # Handle potential division by zero in MAPE
    mape = np.mean(np.abs((y_test - y_pred) / np.where(y_test != 0, y_test, 1e-8))) * 100

    logging.info("--- Model Performance Metrics ---")
    logging.info(f"R-squared (R²):                {r2:.6f}")
    logging.info(f"Mean Absolute Error (MAE):     {mae:.6f} °C")
    logging.info(f"Root Mean Squared Error (RMSE): {rmse:.6f} °C")
    logging.info(f"Mean Error (Bias):             {me:.6f} °C")
    logging.info(f"Mean Absolute Percentage Error (MAPE): {mape:.4f} %")

    # Store results for plotting
    results = {
        'model': model,
        'X_test': X_test,
        'y_test': y_test,
        'y_pred': y_pred,
        'residuals': residuals
        # eval_result is removed as we don't capture it this way anymore
    }
    return results

def plot_and_save_results(results):
    """Generates and saves visualizations for model interpretation."""
    model = results['model']
    X_test = results['X_test']
    y_test = results['y_test']
    y_pred = results['y_pred']
    residuals = results['residuals']
    # eval_result is no longer available

    logging.info("Generating and saving result plots...")
    
    # --- 1. Predicted vs. Actual (Scatter) ---
    plt.figure(figsize=(10, 10))
    plt.scatter(y_test, y_pred, alpha=0.3, s=1)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--r', linewidth=2, label='Perfect Prediction')
    plt.xlabel('Actual Temperature (°C)')
    plt.ylabel('Predicted Temperature (°C)')
    plt.title('Predicted vs. Actual Sea Surface Temperature (Scatter)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join('plots', 'predicted_vs_actual_scatter.png'))
    logging.info("Scatter plot saved to 'plots/predicted_vs_actual_scatter.png'")
    plt.show()

    # --- 2. Predicted vs. Actual (Hexbin) ---
    plt.figure(figsize=(10, 10))
    hb = plt.hexbin(y_test, y_pred, gridsize=50, cmap='Blues')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--r', linewidth=2, label='Perfect Prediction')
    plt.xlabel('Actual Temperature (°C)')
    plt.ylabel('Predicted Temperature (°C)')
    plt.title('Predicted vs. Actual Sea Surface Temperature (Hexbin)')
    plt.legend()
    plt.grid(True)
    plt.colorbar(hb, label='Count')
    plt.savefig(os.path.join('plots', 'predicted_vs_actual_hexbin.png'))
    logging.info("Hexbin plot saved to 'plots/predicted_vs_actual_hexbin.png'")
    plt.show()

    # --- 3. Feature Importance Plot ---
    feature_importances = pd.DataFrame({'feature': model.feature_names_in_, 'importance': model.feature_importances_})
    feature_importances = feature_importances.sort_values('importance', ascending=False)
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x='importance', y='feature', data=feature_importances, palette='viridis')
    plt.title('Feature Importance for SST Prediction')
    plt.xlabel('Importance Score')
    plt.ylabel('Feature')
    plt.tight_layout()
    plt.savefig(os.path.join('plots', 'feature_importance.png'))
    logging.info("Feature importance plot saved to 'plots/feature_importance.png'")
    plt.show()
    
    # --- 4. Residuals Plot (vs Predicted) ---
    plt.figure(figsize=(12, 7))
    plt.scatter(y_pred, residuals, alpha=0.3, s=1)
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2, label='Zero Error')
    plt.xlabel('Predicted Temperature (°C)')
    plt.ylabel('Residuals (Actual - Predicted)')
    plt.title('Residuals vs. Predicted Values')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join('plots', 'residuals_vs_predicted.png'))
    logging.info("Residuals vs Predicted plot saved to 'plots/residuals_vs_predicted.png'")
    plt.show()

    # --- 5. Residuals Plot (vs Actual) ---
    plt.figure(figsize=(12, 7))
    plt.scatter(y_test, residuals, alpha=0.3, s=1)
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2, label='Zero Error')
    plt.xlabel('Actual Temperature (°C)')
    plt.ylabel('Residuals (Actual - Predicted)')
    plt.title('Residuals vs. Actual Values')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join('plots', 'residuals_vs_actual.png'))
    logging.info("Residuals vs Actual plot saved to 'plots/residuals_vs_actual.png'")
    plt.show()

    # --- 6. Residuals Histogram ---
    plt.figure(figsize=(12, 7))
    plt.hist(residuals, bins=100, edgecolor='black', alpha=0.7)
    plt.xlabel('Residuals (°C)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Residuals')
    plt.grid(True)
    plt.savefig(os.path.join('plots', 'residuals_histogram.png'))
    logging.info("Residuals histogram saved to 'plots/residuals_histogram.png'")
    plt.show()

    # --- 7. Q-Q Plot ---
    plt.figure(figsize=(10, 10))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title('Q-Q Plot of Residuals')
    plt.grid(True)
    plt.savefig(os.path.join('plots', 'residuals_qq_plot.png'))
    logging.info("Q-Q plot saved to 'plots/residuals_qq_plot.png'")
    plt.show()

    # --- 8. Partial Dependence Plots (if available) ---
    if PDP_AVAILABLE:
        # Select top N features for PDPs (e.g., top 4)
        feature_importances_df = pd.DataFrame({'feature': model.feature_names_in_, 'importance': model.feature_importances_})
        feature_importances_df = feature_importances_df.sort_values('importance', ascending=False)
        top_n = min(4, len(feature_importances_df))
        top_features = feature_importances_df.head(top_n)['feature'].tolist()
        logging.info(f"Generating Partial Dependence Plots for top {top_n} features: {top_features}")
        
        try:
            # Example for one feature (latitude)
            fig, ax = plt.subplots(figsize=(10, 8))
            PartialDependenceDisplay.from_estimator(model, X_test, ['latitude'], ax=ax)
            plt.title('Partial Dependence of SST on Latitude')
            plt.savefig(os.path.join('plots', 'pdp_latitude.png'))
            logging.info("PDP for Latitude saved to 'plots/pdp_latitude.png'")
            plt.show()

            # Example for a cyclical feature (day_sin)
            if 'day_sin' in X_test.columns:
                 fig, ax = plt.subplots(figsize=(10, 8))
                 PartialDependenceDisplay.from_estimator(model, X_test, ['day_sin'], ax=ax)
                 plt.title('Partial Dependence of SST on Day of Year (Sin Component)')
                 plt.savefig(os.path.join('plots', 'pdp_day_sin.png'))
                 logging.info("PDP for Day Sin saved to 'plots/pdp_day_sin.png'")
                 plt.show()
                 
        except Exception as e:
            logging.error(f"Error generating PDPs: {e}")
    else:
        logging.info("Skipping Partial Dependence Plots as required module is not available or outdated.")


def main():
    """Main function to run the SST prediction project."""
    df = load_and_prepare_data(CSV_FILE_PATH)
    
    if df is not None:
        X, y = feature_engineering(df)
        results = train_and_evaluate_model(X, y)
        plot_and_save_results(results)
        logging.info("--- SST Prediction Analysis Complete ---")

if __name__ == "__main__":
    main()