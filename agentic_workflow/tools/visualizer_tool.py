"""
Visualization Tool for ARGO float data plotting and chart generation.
Creates oceanographic plots including T-S diagrams, profile plots, and maps.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import Dict, Any, List, Optional, Tuple
import io
import base64
from datetime import datetime

logger = logging.getLogger(__name__)

class VisualizerTool:
    """Tool for creating oceanographic visualizations."""
    
    def __init__(self):
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configure matplotlib for better plots
        plt.rcParams['figure.figsize'] = (10, 8)
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
    
    def plot_temperature_salinity_diagram(self, 
                                        df: pd.DataFrame,
                                        title: str = "Temperature-Salinity Diagram",
                                        save_path: Optional[str] = None) -> str:
        """
        Create a Temperature-Salinity (T-S) diagram.
        
        Args:
            df: DataFrame with temp, psal, and pressure columns
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Base64 encoded plot image or file path
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Filter valid data
            valid_data = df.dropna(subset=['temp', 'psal', 'pressure'])
            
            if valid_data.empty:
                logger.warning("No valid data for T-S diagram")
                return ""
            
            # Create scatter plot colored by depth (pressure)
            scatter = ax.scatter(
                valid_data['psal'], 
                valid_data['temp'],
                c=valid_data['pressure'],
                cmap='viridis_r',
                alpha=0.6,
                s=20
            )
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Pressure (dbar)', rotation=270, labelpad=20)
            
            # Add density contours (simplified)
            sal_range = np.linspace(valid_data['psal'].min(), valid_data['psal'].max(), 50)
            temp_range = np.linspace(valid_data['temp'].min(), valid_data['temp'].max(), 50)
            SAL, TEMP = np.meshgrid(sal_range, temp_range)
            
            # Simplified density calculation for contours
            DENSITY = 1000 + 0.8 * (SAL - 35) - 0.2 * TEMP
            
            contours = ax.contour(SAL, TEMP, DENSITY, colors='gray', alpha=0.5, linewidths=0.5)
            ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f')
            
            ax.set_xlabel('Practical Salinity')
            ax.set_ylabel('Temperature (°C)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                # Return base64 encoded image
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return image_base64
                
        except Exception as e:
            logger.error(f"Failed to create T-S diagram: {e}")
            return ""
    
    def plot_profile_comparison(self, 
                              df: pd.DataFrame,
                              variable: str = 'temp',
                              title: str = "Profile Comparison",
                              save_path: Optional[str] = None) -> str:
        """
        Plot vertical profiles of temperature or salinity.
        
        Args:
            df: DataFrame with measurements
            variable: Variable to plot ('temp' or 'psal')
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Base64 encoded plot image or file path
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 12))
            
            # Group by profile
            profiles = df.groupby(['wmo_id', 'cycle_number'])
            
            colors = plt.cm.tab10(np.linspace(0, 1, min(len(profiles), 10)))
            
            for i, ((wmo_id, cycle), profile_data) in enumerate(profiles):
                if i >= 10:  # Limit to 10 profiles for clarity
                    break
                
                # Sort by pressure
                profile_data = profile_data.sort_values('pressure')
                
                ax.plot(
                    profile_data[variable], 
                    profile_data['pressure'],
                    color=colors[i],
                    label=f'Float {wmo_id}, Cycle {cycle}',
                    linewidth=1.5,
                    alpha=0.8
                )
            
            ax.invert_yaxis()  # Depth increases downward
            ax.set_ylabel('Pressure (dbar)')
            
            if variable == 'temp':
                ax.set_xlabel('Temperature (°C)')
            elif variable == 'psal':
                ax.set_xlabel('Practical Salinity')
            
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            if len(profiles) <= 10:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return image_base64
                
        except Exception as e:
            logger.error(f"Failed to create profile plot: {e}")
            return ""
    
    def plot_average_profile(self, 
                           avg_df: pd.DataFrame,
                           variable: str = 'avg_temperature',
                           title: str = "Average Profile",
                           save_path: Optional[str] = None) -> str:
        """
        Plot average profile with error bars.
        
        Args:
            avg_df: DataFrame from analyzer_tool.calculate_average_profile()
            variable: Variable to plot ('avg_temperature' or 'avg_salinity')
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Base64 encoded plot image or file path
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 12))
            
            if avg_df.empty:
                logger.warning("No data for average profile plot")
                return ""
            
            # Determine error column
            if variable == 'avg_temperature':
                error_col = 'std_temperature'
                xlabel = 'Temperature (°C)'
            elif variable == 'avg_salinity':
                error_col = 'std_salinity'
                xlabel = 'Practical Salinity'
            else:
                error_col = None
                xlabel = variable
            
            # Plot average profile with error bars
            if error_col and error_col in avg_df.columns:
                ax.errorbar(
                    avg_df[variable], 
                    avg_df['depth_center'],
                    xerr=avg_df[error_col],
                    fmt='o-',
                    capsize=3,
                    capthick=1,
                    linewidth=2,
                    markersize=4,
                    alpha=0.8
                )
            else:
                ax.plot(
                    avg_df[variable], 
                    avg_df['depth_center'],
                    'o-',
                    linewidth=2,
                    markersize=4
                )
            
            ax.invert_yaxis()
            ax.set_ylabel('Depth (dbar)')
            ax.set_xlabel(xlabel)
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return image_base64
                
        except Exception as e:
            logger.error(f"Failed to create average profile plot: {e}")
            return ""
    
    def plot_geographic_distribution(self, 
                                   df: pd.DataFrame,
                                   title: str = "ARGO Float Locations",
                                   save_path: Optional[str] = None) -> str:
        """
        Plot geographic distribution of ARGO floats.
        
        Args:
            df: DataFrame with latitude and longitude columns
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Base64 encoded plot image or file path
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Create scatter plot
            scatter = ax.scatter(
                df['longitude'], 
                df['latitude'],
                c=df.index if 'profile_date' not in df.columns else pd.to_datetime(df['profile_date']).astype(int),
                cmap='viridis',
                alpha=0.6,
                s=30
            )
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            if 'profile_date' in df.columns:
                cbar.set_label('Time', rotation=270, labelpad=20)
            else:
                cbar.set_label('Profile Index', rotation=270, labelpad=20)
            
            ax.set_xlabel('Longitude (°E)')
            ax.set_ylabel('Latitude (°N)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # Add coastline approximation (very basic)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3, linewidth=0.5)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3, linewidth=0.5)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return image_base64
                
        except Exception as e:
            logger.error(f"Failed to create geographic plot: {e}")
            return ""
