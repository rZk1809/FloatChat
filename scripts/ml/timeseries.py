import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Import necessary for ACF/PACF plots
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

# --- Configuration ---
CSV_FILE_PATH = "argo_data_export_full.csv"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_prepare_data(file_path):
    """
    Loads the full dataset and identifies the best float for time series analysis
    by finding the one with the longest surface data record.
    """
    logging.info(f"Loading data from '{file_path}'...")
    try:
        # Ensure column names match your actual CSV
        use_cols = ['PLATFORM_NUMBER', 'JULD', 'PRES_ADJUSTED', 'TEMP_ADJUSTED']
        df = pd.read_csv(file_path, usecols=use_cols)
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None, None
    except Exception as e:
        logging.error(f"An error occurred while reading the CSV: {e}")
        return None, None

    # --- Pre-filter for all surface data first ---
    logging.info("Filtering for all available surface data (pressure < 10 dbar)...")
    surface_df_all = df[df['PRES_ADJUSTED'] < 10].copy()

    # --- Find the float with the most SURFACE data points ---
    logging.info("Identifying the best float for time series analysis based on surface data...")
    float_counts = surface_df_all['PLATFORM_NUMBER'].value_counts()
    if float_counts.empty:
        logging.error("No surface data found in the CSV.")
        return None, None

    best_float_id = float_counts.index[0]
    logging.info(f"Selected float with the most SURFACE data points: WMO ID {best_float_id} ({float_counts.iloc[0]} points)")

    # --- Filter data for the selected float ---
    float_df = surface_df_all[surface_df_all['PLATFORM_NUMBER'] == best_float_id].copy()

    # --- Preprocess the data for time series ---
    logging.info("Preprocessing data for the selected float...")

    float_df['JULD'] = pd.to_datetime(float_df['JULD'], errors='coerce')
    float_df.dropna(subset=['JULD'], inplace=True)
    float_df.sort_values('JULD', inplace=True)

    float_df.set_index('JULD', inplace=True)

    # Resample to a consistent daily frequency
    ts_data = float_df['TEMP_ADJUSTED'].resample('D').mean() # .ffill() removed to avoid artificial data points
    ts_data.dropna(inplace=True) # Drop days with no data

    if ts_data.empty:
        logging.error("Time series is empty after preprocessing.")
        return None, None

    logging.info(f"Prepared time series with {len(ts_data)} daily data points from {ts_data.index.min().date()} to {ts_data.index.max().date()}.")
    return ts_data, best_float_id

def perform_eda(ts_data, float_id):
    """
    Performs and plots Exploratory Data Analysis on the time series.
    """
    logging.info("Performing Exploratory Data Analysis (EDA)...")

    # 1. Plot the full time series
    plt.figure(figsize=(14, 5))
    plt.plot(ts_data.index, ts_data.values, marker='o', linestyle='-', markersize=3, alpha=0.7)
    plt.title(f'Sea Surface Temperature (SST) Time Series for ARGO Float {float_id}')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    # 2. Autocorrelation (ACF) and Partial Autocorrelation (PACF) plots
    # These help identify potential AR and MA terms for ARIMA models
    if len(ts_data) > 20: # Need sufficient points for meaningful ACF/PACF
        logging.info("Plotting Autocorrelation (ACF) and Partial Autocorrelation (PACF)...")
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        plot_acf(ts_data, lags=min(40, len(ts_data)//2 - 1), ax=axes[0])
        axes[0].set_title(f'Autocorrelation Function (ACF) - Float {float_id}')

        plot_pacf(ts_data, lags=min(40, len(ts_data)//2 - 1), ax=axes[1], method='ywm') # 'ywm' is often more robust
        axes[1].set_title(f'Partial Autocorrelation Function (PACF) - Float {float_id}')

        plt.tight_layout()
        plt.show()
    else:
        logging.warning("Insufficient data points for meaningful ACF/PACF plots.")

    # 3. Histogram of values
    plt.figure(figsize=(10, 5))
    plt.hist(ts_data.values, bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Frequency')
    plt.title(f'Distribution of Daily Mean SST - Float {float_id}')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def train_and_evaluate_model(ts_data):
    """
    Splits data, trains a time series model (ARIMA/SARIMA), and evaluates its performance.
    Simplified for short time series.
    """
    if len(ts_data) < 10:
        logging.error("Insufficient data points (<10) for time series modeling. Aborting.")
        return None, None, None, None

    # Simple split: Use last 30% for testing
    split_index = int(len(ts_data) * 0.7)
    if split_index == len(ts_data):
         split_index = len(ts_data) - 1 # Ensure at least one test point
    train, test = ts_data.iloc[:split_index], ts_data.iloc[split_index:]
    logging.info(f"Data split: {len(train)} training points and {len(test)} testing points.")

    if len(test) == 0:
        logging.error("No data points available for testing after split.")
        return train, None, None, None

    model_fitted = None
    forecast_mean = None
    forecast_ci = None

    # --- Attempt to fit a model ---
    logging.info("Attempting to fit a time series model...")
    try:
        # Try a simple ARIMA model first, as SARIMA might be overkill or unstable for very short series
        # The order (p,d,q) needs to be chosen. We'll start with a common simple one.
        # A more robust approach would involve grid search or auto_arima, but let's keep it simple.
        model = sm.tsa.ARIMA(train, order=(1, 1, 1)) # (p=1, d=1, q=1)
        model_fitted = model.fit()
        logging.info("Simple ARIMA(1,1,1) model fitted successfully.")
        logging.info("\n" + str(model_fitted.summary()))

    except Exception as e1:
        logging.warning(f"Failed to fit ARIMA(1,1,1) model: {e1}")
        try:
            # Fallback: Try a simpler AR model (ARIMA(p,1,0))
            model = sm.tsa.ARIMA(train, order=(1, 1, 0))
            model_fitted = model.fit()
            logging.info("Fallback ARIMA(1,1,0) model fitted successfully.")
            logging.info("\n" + str(model_fitted.summary()))
        except Exception as e2:
             logging.error(f"Failed to fit fallback ARIMA(1,1,0) model: {e2}")
             logging.error("Could not fit any ARIMA model to the data.")
             return train, test, None, None

    # --- Generate forecast ---
    if model_fitted is not None:
        try:
            steps_ahead = len(test)
            logging.info(f"Generating forecast for {steps_ahead} steps ahead...")
            forecast_result = model_fitted.get_forecast(steps=steps_ahead)
            forecast_mean = forecast_result.predicted_mean
            forecast_ci = forecast_result.conf_int()
            logging.info("Forecast generated successfully.")
        except Exception as e:
            logging.error(f"An error occurred during forecast generation: {e}")
            return train, test, None, None
    else:
        return train, test, None, None

    return train, test, forecast_mean, forecast_ci

def evaluate_and_plot_results(train, test, forecast_mean, forecast_ci, float_id):
    """
    Calculates metrics and plots the results.
    """
    if forecast_mean is None or test is None:
        logging.warning("Cannot evaluate or plot results due to missing forecast or test data.")
        return

    # Align forecast with test index if lengths match
    if len(forecast_mean) == len(test):
        forecast_mean.index = test.index
        if forecast_ci is not None:
            forecast_ci.index = test.index
    else:
        logging.warning("Forecast and test set lengths do not match. Plotting might be misaligned.")
        # Truncate to the shorter length for evaluation
        min_len = min(len(forecast_mean), len(test))
        test_eval = test.iloc[:min_len]
        forecast_eval = forecast_mean.iloc[:min_len]
        forecast_ci_eval = forecast_ci.iloc[:min_len] if forecast_ci is not None else None
    # Use aligned data for evaluation
    test_eval = test
    forecast_eval = forecast_mean
    forecast_ci_eval = forecast_ci

    # --- Evaluation Metrics ---
    try:
        # Ensure indices match for evaluation
        common_index = test_eval.index.intersection(forecast_eval.index)
        if len(common_index) == 0:
            raise ValueError("No common dates between test and forecast for evaluation.")

        test_aligned = test_eval.loc[common_index]
        forecast_aligned = forecast_eval.loc[common_index]

        r2 = r2_score(test_aligned, forecast_aligned)
        mae = mean_absolute_error(test_aligned, forecast_aligned)
        mse = mean_squared_error(test_aligned, forecast_aligned)
        rmse = np.sqrt(mse)
        residuals = test_aligned - forecast_aligned
        me = np.mean(residuals) # Mean Error / Bias
        # Handle potential division by zero in MAPE
        mape = np.mean(np.abs((test_aligned - forecast_aligned) / np.where(test_aligned != 0, test_aligned, 1e-8))) * 100

        logging.info("--- Model Evaluation Metrics ---")
        logging.info(f"R-squared (R²):                {r2:.4f}")
        logging.info(f"Mean Absolute Error (MAE):     {mae:.4f} °C")
        logging.info(f"Root Mean Squared Error (RMSE): {rmse:.4f} °C")
        logging.info(f"Mean Error (Bias):             {me:.4f} °C")
        logging.info(f"Mean Absolute Percentage Error (MAPE): {mape:.2f} %")

    except Exception as e:
        logging.error(f"Error calculating evaluation metrics: {e}")
        r2 = mae = rmse = me = mape = np.nan

    # --- Plotting Results ---
    plt.figure(figsize=(14, 7))
    plt.plot(train.index, train.values, label='Training Data', color='blue')
    plt.plot(test_eval.index, test_eval.values, label='Actual Test Data', color='orange', marker='o')
    plt.plot(forecast_eval.index, forecast_eval.values, label='Forecast', color='green', marker='s')

    if forecast_ci_eval is not None:
        plt.fill_between(forecast_ci_eval.index,
                         forecast_ci_eval.iloc[:, 0],
                         forecast_ci_eval.iloc[:, 1],
                         color='green', alpha=0.2, label='95% Confidence Interval')

    plt.title(f'SST Forecast vs Actuals for ARGO Float {float_id}')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    # --- Residuals Plot ---
    if not np.isnan(me): # Only plot if metrics were calculated
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.scatter(forecast_aligned, residuals, alpha=0.7)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Predicted Temperature (°C)')
        plt.ylabel('Residuals (Actual - Predicted)')
        plt.title('Residuals vs Predicted')
        plt.grid(True, linestyle='--', alpha=0.5)

        plt.subplot(1, 2, 2)
        plt.hist(residuals, bins=15, edgecolor='black', alpha=0.7)
        plt.xlabel('Residuals (°C)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Residuals')
        plt.grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.show()

        # --- Actual vs Predicted Scatter ---
        plt.figure(figsize=(8, 6))
        plt.scatter(test_aligned, forecast_aligned, alpha=0.7)
        # Perfect prediction line
        min_val = min(test_aligned.min(), forecast_aligned.min())
        max_val = max(test_aligned.max(), forecast_aligned.max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
        plt.xlabel('Actual Temperature (°C)')
        plt.ylabel('Predicted Temperature (°C)')
        plt.title('Actual vs Predicted SST')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()


def main():
    """Main function to run the time series forecasting project."""
    ts_data, float_id = load_and_prepare_data(CSV_FILE_PATH)

    if ts_data is not None and not ts_data.empty:
        perform_eda(ts_data, float_id)
        train, test, forecast_mean, forecast_ci = train_and_evaluate_model(ts_data)
        evaluate_and_plot_results(train, test, forecast_mean, forecast_ci, float_id)
        logging.info("--- Time Series Analysis Complete ---")
    else:
        logging.error("Could not load or prepare time series data. Exiting.")

if __name__ == "__main__":
    main()