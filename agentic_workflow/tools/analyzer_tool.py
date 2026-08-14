"""
Data Analysis Tool for ARGO float data processing and calculations.
Provides oceanographic analysis functions and statistical computations.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=RuntimeWarning)

class AnalyzerTool:
    """Tool for analyzing ARGO oceanographic data."""
    
    def __init__(self):
        pass
    
    def calculate_potential_density(self, 
                                  temperature: np.ndarray, 
                                  salinity: np.ndarray, 
                                  pressure: np.ndarray,
                                  reference_pressure: float = 0.0,
                                  longitude: Optional[np.ndarray] = None,
                                  latitude: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Calculate potential density with the TEOS-10 Gibbs SeaWater library.
        
        Args:
            temperature: Temperature in Celsius
            salinity: Practical salinity
            pressure: Pressure in dbar
            reference_pressure: Reference pressure for potential density
            
        Returns:
            Potential density in kg/m³
        """
        if longitude is None or latitude is None:
            raise ValueError("longitude and latitude are required for TEOS-10 density")

        import gsw

        temperature = np.asarray(temperature, dtype=float)
        salinity = np.asarray(salinity, dtype=float)
        pressure = np.asarray(pressure, dtype=float)
        longitude = np.broadcast_to(np.asarray(longitude, dtype=float), temperature.shape)
        latitude = np.broadcast_to(np.asarray(latitude, dtype=float), temperature.shape)
        absolute_salinity = gsw.SA_from_SP(salinity, pressure, longitude, latitude)
        return gsw.pot_rho_t_exact(
            absolute_salinity,
            temperature,
            pressure,
            float(reference_pressure),
        )
    
    def calculate_mixed_layer_depth(self, 
                                   temperature: np.ndarray, 
                                   pressure: np.ndarray,
                                   threshold: float = 0.2) -> float:
        """
        Calculate mixed layer depth based on temperature criterion.
        
        Args:
            temperature: Temperature profile
            pressure: Pressure profile (depth proxy)
            threshold: Temperature difference threshold in °C
            
        Returns:
            Mixed layer depth in dbar
        """
        try:
            T = np.asarray(temperature)
            P = np.asarray(pressure)
            
            if len(T) < 2 or len(P) < 2:
                return np.nan
            
            # Sort by pressure (depth)
            sort_idx = np.argsort(P)
            T_sorted = T[sort_idx]
            P_sorted = P[sort_idx]
            
            # Reference temperature (near surface)
            T_ref = T_sorted[0]
            
            # Find first depth where temperature differs by threshold
            for i, (t, p) in enumerate(zip(T_sorted, P_sorted)):
                if abs(t - T_ref) > threshold:
                    return p
            
            # If no MLD found, return maximum depth
            return P_sorted[-1] if len(P_sorted) > 0 else np.nan
            
        except Exception as e:
            logger.error(f"Failed to calculate mixed layer depth: {e}")
            return np.nan
    
    def calculate_profile_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for temperature and salinity profiles.
        
        Args:
            df: DataFrame with columns: temp, psal, pressure
            
        Returns:
            Dictionary with statistical summaries
        """
        try:
            if df.empty:
                return {"error": "Empty dataset"}
            
            stats_dict = {
                "profile_count": len(df.groupby(['wmo_id', 'cycle_number'])),
                "measurement_count": len(df),
                "depth_range": {
                    "min": float(df['pressure'].min()),
                    "max": float(df['pressure'].max()),
                    "mean": float(df['pressure'].mean())
                },
                "temperature": {
                    "min": float(df['temp'].min()),
                    "max": float(df['temp'].max()),
                    "mean": float(df['temp'].mean()),
                    "std": float(df['temp'].std()),
                    "median": float(df['temp'].median())
                },
                "salinity": {
                    "min": float(df['psal'].min()),
                    "max": float(df['psal'].max()),
                    "mean": float(df['psal'].mean()),
                    "std": float(df['psal'].std()),
                    "median": float(df['psal'].median())
                }
            }
            
            # Calculate potential density statistics
            if len(df) > 0 and {"longitude", "latitude"}.issubset(df.columns):
                pot_density = self.calculate_potential_density(
                    df['temp'].values, 
                    df['psal'].values, 
                    df['pressure'].values,
                    longitude=df['longitude'].values,
                    latitude=df['latitude'].values,
                )
                
                if len(pot_density) > 0:
                    stats_dict["potential_density"] = {
                        "min": float(np.nanmin(pot_density)),
                        "max": float(np.nanmax(pot_density)),
                        "mean": float(np.nanmean(pot_density)),
                        "std": float(np.nanstd(pot_density))
                    }
            else:
                stats_dict["potential_density"] = {
                    "status": "unavailable",
                    "reason": "TEOS-10 density requires longitude and latitude",
                }
            
            return stats_dict
            
        except Exception as e:
            logger.error(f"Failed to calculate profile statistics: {e}")
            return {"error": str(e)}
    
    def calculate_average_profile(self, df: pd.DataFrame, 
                                 depth_bins: Optional[np.ndarray] = None) -> pd.DataFrame:
        """
        Calculate average temperature and salinity profiles across multiple profiles.
        
        Args:
            df: DataFrame with measurements from multiple profiles
            depth_bins: Optional depth bins for averaging (default: 0-2000m in 10m steps)
            
        Returns:
            DataFrame with averaged profiles
        """
        try:
            if df.empty:
                return pd.DataFrame()
            
            if depth_bins is None:
                depth_bins = np.arange(0, 2000, 10)  # 0 to 2000 dbar in 10 dbar steps
            
            # Initialize result arrays
            avg_temp = []
            avg_sal = []
            std_temp = []
            std_sal = []
            count_per_bin = []
            
            for i in range(len(depth_bins) - 1):
                depth_min = depth_bins[i]
                depth_max = depth_bins[i + 1]
                
                # Filter data within depth bin
                mask = (df['pressure'] >= depth_min) & (df['pressure'] < depth_max)
                bin_data = df[mask]
                
                if len(bin_data) > 0:
                    avg_temp.append(bin_data['temp'].mean())
                    avg_sal.append(bin_data['psal'].mean())
                    std_temp.append(bin_data['temp'].std())
                    std_sal.append(bin_data['psal'].std())
                    count_per_bin.append(len(bin_data))
                else:
                    avg_temp.append(np.nan)
                    avg_sal.append(np.nan)
                    std_temp.append(np.nan)
                    std_sal.append(np.nan)
                    count_per_bin.append(0)
            
            result_df = pd.DataFrame({
                'depth_min': depth_bins[:-1],
                'depth_max': depth_bins[1:],
                'depth_center': (depth_bins[:-1] + depth_bins[1:]) / 2,
                'avg_temperature': avg_temp,
                'avg_salinity': avg_sal,
                'std_temperature': std_temp,
                'std_salinity': std_sal,
                'measurement_count': count_per_bin
            })
            
            # Remove bins with no data
            result_df = result_df[result_df['measurement_count'] > 0]
            
            logger.info(f"Calculated average profile with {len(result_df)} depth bins")
            return result_df
            
        except Exception as e:
            logger.error(f"Failed to calculate average profile: {e}")
            return pd.DataFrame()
    
    def compare_regions(self, region1_df: pd.DataFrame, 
                       region2_df: pd.DataFrame,
                       region1_name: str = "Region 1",
                       region2_name: str = "Region 2") -> Dict[str, Any]:
        """
        Compare oceanographic properties between two regions.
        
        Args:
            region1_df: DataFrame with measurements from first region
            region2_df: DataFrame with measurements from second region
            region1_name: Name of first region
            region2_name: Name of second region
            
        Returns:
            Dictionary with comparison results
        """
        try:
            if region1_df is region2_df:
                raise ValueError("Region comparison inputs must be independent datasets")

            comparison = {
                "regions": {
                    region1_name: self.calculate_profile_statistics(region1_df),
                    region2_name: self.calculate_profile_statistics(region2_df)
                },
                "differences": {}
            }
            
            names = {region1_name, region2_name}
            if "Indian Ocean" in names and names & {"Bay of Bengal", "Arabian Sea"}:
                comparison["warning"] = (
                    "The requested regions overlap hierarchically; inferential "
                    "significance is not reported."
                )
                return comparison

            # Treat profiles, not correlated depth rows, as sampling units.
            if not region1_df.empty and not region2_df.empty:
                group_columns = ['wmo_id', 'cycle_number']
                if not set(group_columns).issubset(region1_df.columns) or not set(
                    group_columns
                ).issubset(region2_df.columns):
                    comparison["warning"] = (
                        "Profile identifiers are required for independent-sample comparison."
                    )
                    return comparison
                region1_profiles = region1_df.groupby(group_columns)[['temp', 'psal']].mean()
                region2_profiles = region2_df.groupby(group_columns)[['temp', 'psal']].mean()
                if len(region1_profiles) < 2 or len(region2_profiles) < 2:
                    comparison["warning"] = (
                        "At least two independent profiles per region are required."
                    )
                    return comparison

                # Temperature comparison
                temp_ttest = stats.ttest_ind(
                    region1_profiles['temp'].dropna(),
                    region2_profiles['temp'].dropna(),
                    equal_var=False,
                )
                
                # Salinity comparison
                sal_ttest = stats.ttest_ind(
                    region1_profiles['psal'].dropna(),
                    region2_profiles['psal'].dropna(),
                    equal_var=False,
                )
                
                comparison["differences"] = {
                    "temperature": {
                        "mean_diff": float(region1_profiles['temp'].mean() - region2_profiles['temp'].mean()),
                        "t_statistic": float(temp_ttest.statistic),
                        "p_value": float(temp_ttest.pvalue),
                        "significant": temp_ttest.pvalue < 0.05
                    },
                    "salinity": {
                        "mean_diff": float(region1_profiles['psal'].mean() - region2_profiles['psal'].mean()),
                        "t_statistic": float(sal_ttest.statistic),
                        "p_value": float(sal_ttest.pvalue),
                        "significant": sal_ttest.pvalue < 0.05
                    }
                }
                comparison["limitations"] = [
                    "Welch tests use one vertically averaged value per profile.",
                    "Depth-matched and season-matched analyses are required for scientific claims.",
                ]
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare regions: {e}")
            return {"error": str(e)}
