"""
Plotting Agent for the Agentic AI RAG System.
Automatically generates visualizations based on analysis results and query intent.
"""

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class PlottingAgent:
    """Agent responsible for automatic visualization generation."""
    
    def __init__(self):
        self.plot_styles = {
            'template': 'plotly_white',
            'color_palette': px.colors.qualitative.Set3,
            'font_family': 'Arial, sans-serif',
            'title_size': 16,
            'axis_title_size': 14,
            'tick_size': 12
        }
        
        # Plot type detection patterns
        self.plot_patterns = {
            'temperature_depth': [
                r'temperature.*depth', r'temp.*depth', r'depth.*temperature',
                r'temperature.*profile', r'temp.*profile', r'profile.*temperature'
            ],
            'ts_diagram': [
                r't-s.*diagram', r'temperature.*salinity.*diagram', 
                r'temp.*sal.*diagram', r'ts.*plot'
            ],
            'time_series': [
                r'time.*series', r'temporal.*trend', r'over.*time',
                r'trend.*time', r'seasonal', r'monthly', r'yearly'
            ],
            'geographic': [
                r'map', r'geographic', r'spatial', r'location',
                r'latitude.*longitude', r'regional'
            ],
            'statistical': [
                r'histogram', r'distribution', r'statistics', r'stats',
                r'box.*plot', r'violin.*plot'
            ],
            'comparison': [
                r'compare', r'comparison', r'versus', r'vs', r'between'
            ]
        }
    
    def should_generate_plots(self, query: str, results: Dict[str, Any]) -> bool:
        """Determine if plots should be generated based on query and results."""
        try:
            # Check if query explicitly requests visualization
            viz_keywords = ['plot', 'chart', 'graph', 'visualiz', 'show', 'display', 'diagram']
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in viz_keywords):
                return True
            
            # Check if results contain plottable data
            if 'raw_data' in results and results['raw_data']:
                df = pd.DataFrame(results['raw_data'])
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                return len(numeric_cols) >= 2  # Need at least 2 numeric columns
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining plot necessity: {e}")
            return False
    
    def detect_plot_types(self, query: str, data: pd.DataFrame) -> List[str]:
        """Detect appropriate plot types based on query and data."""
        plot_types = []
        query_lower = query.lower()
        
        try:
            # Check query patterns
            for plot_type, patterns in self.plot_patterns.items():
                if any(re.search(pattern, query_lower) for pattern in patterns):
                    plot_types.append(plot_type)
            
            # Data-driven plot type detection
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            
            # Temperature-depth profile detection
            if any('temp' in col.lower() for col in numeric_cols) and \
               any(col.lower() in ['pressure', 'depth'] for col in numeric_cols):
                if 'temperature_depth' not in plot_types:
                    plot_types.append('temperature_depth')
            
            # T-S diagram detection
            if any('temp' in col.lower() for col in numeric_cols) and \
               any('sal' in col.lower() for col in numeric_cols):
                if 'ts_diagram' not in plot_types:
                    plot_types.append('ts_diagram')
            
            # Geographic plot detection
            if 'latitude' in data.columns and 'longitude' in data.columns:
                if 'geographic' not in plot_types:
                    plot_types.append('geographic')
            
            # Default to statistical if no specific type detected
            if not plot_types and len(numeric_cols) > 0:
                plot_types.append('statistical')
            
            return plot_types
            
        except Exception as e:
            logger.error(f"Error detecting plot types: {e}")
            return ['statistical']  # Fallback
    
    def create_temperature_depth_plot(self, data: pd.DataFrame, title: str = "") -> go.Figure:
        """Create temperature vs depth profile plot."""
        try:
            # Find temperature and pressure/depth columns
            temp_col = None
            depth_col = None
            
            for col in data.columns:
                if 'temp' in col.lower() and temp_col is None:
                    temp_col = col
                if col.lower() in ['pressure', 'depth'] and depth_col is None:
                    depth_col = col
            
            if not temp_col or not depth_col:
                raise ValueError("Temperature or depth column not found")
            
            # Create subplot for multiple profiles if available
            if 'wmo_id' in data.columns or 'profile_id' in data.columns:
                profile_col = 'wmo_id' if 'wmo_id' in data.columns else 'profile_id'
                unique_profiles = data[profile_col].unique()[:10]  # Limit to 10 profiles
                
                fig = go.Figure()
                
                for i, profile in enumerate(unique_profiles):
                    profile_data = data[data[profile_col] == profile]
                    fig.add_trace(go.Scatter(
                        x=profile_data[temp_col],
                        y=-profile_data[depth_col],  # Negative for depth
                        mode='lines+markers',
                        name=f'Profile {profile}',
                        line=dict(color=self.plot_styles['color_palette'][i % len(self.plot_styles['color_palette'])]),
                        marker=dict(size=4)
                    ))
            else:
                # Single profile
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data[temp_col],
                    y=-data[depth_col],  # Negative for depth
                    mode='lines+markers',
                    name='Temperature Profile',
                    line=dict(color=self.plot_styles['color_palette'][0]),
                    marker=dict(size=4)
                ))
            
            # Update layout
            fig.update_layout(
                title=title or "Temperature vs Depth Profile",
                xaxis_title="Temperature (°C)",
                yaxis_title="Depth (m)",
                template=self.plot_styles['template'],
                font=dict(family=self.plot_styles['font_family']),
                showlegend=True,
                hovermode='closest'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating temperature-depth plot: {e}")
            return self.create_error_plot(f"Failed to create temperature-depth plot: {e}")
    
    def create_ts_diagram(self, data: pd.DataFrame, title: str = "") -> go.Figure:
        """Create Temperature-Salinity (T-S) diagram."""
        try:
            # Find temperature and salinity columns
            temp_col = None
            sal_col = None
            
            for col in data.columns:
                if 'temp' in col.lower() and temp_col is None:
                    temp_col = col
                if 'sal' in col.lower() and sal_col is None:
                    sal_col = col
            
            if not temp_col or not sal_col:
                raise ValueError("Temperature or salinity column not found")
            
            # Create scatter plot
            fig = go.Figure()
            
            if 'wmo_id' in data.columns:
                # Color by profile
                unique_profiles = data['wmo_id'].unique()[:10]
                for i, profile in enumerate(unique_profiles):
                    profile_data = data[data['wmo_id'] == profile]
                    fig.add_trace(go.Scatter(
                        x=profile_data[sal_col],
                        y=profile_data[temp_col],
                        mode='markers',
                        name=f'Profile {profile}',
                        marker=dict(
                            color=self.plot_styles['color_palette'][i % len(self.plot_styles['color_palette'])],
                            size=6,
                            opacity=0.7
                        )
                    ))
            else:
                # Single color
                fig.add_trace(go.Scatter(
                    x=data[sal_col],
                    y=data[temp_col],
                    mode='markers',
                    name='T-S Data',
                    marker=dict(
                        color=self.plot_styles['color_palette'][0],
                        size=6,
                        opacity=0.7
                    )
                ))
            
            # Update layout
            fig.update_layout(
                title=title or "Temperature-Salinity Diagram",
                xaxis_title="Salinity (PSU)",
                yaxis_title="Temperature (°C)",
                template=self.plot_styles['template'],
                font=dict(family=self.plot_styles['font_family']),
                showlegend=True,
                hovermode='closest'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating T-S diagram: {e}")
            return self.create_error_plot(f"Failed to create T-S diagram: {e}")
    
    def create_geographic_plot(self, data: pd.DataFrame, title: str = "") -> go.Figure:
        """Create geographic scatter plot."""
        try:
            if 'latitude' not in data.columns or 'longitude' not in data.columns:
                raise ValueError("Latitude or longitude columns not found")
            
            # Determine color variable
            color_col = None
            if 'temp' in data.columns:
                color_col = 'temp'
            elif any('temp' in col.lower() for col in data.columns):
                color_col = next(col for col in data.columns if 'temp' in col.lower())
            
            fig = go.Figure()
            
            if color_col:
                fig.add_trace(go.Scattergeo(
                    lon=data['longitude'],
                    lat=data['latitude'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=data[color_col],
                        colorscale='Viridis',
                        colorbar=dict(title=color_col.title()),
                        opacity=0.8
                    ),
                    text=data[color_col].round(2) if color_col else None,
                    hovertemplate=f'<b>Lat:</b> %{{lat}}<br><b>Lon:</b> %{{lon}}<br><b>{color_col.title()}:</b> %{{text}}<extra></extra>'
                ))
            else:
                fig.add_trace(go.Scattergeo(
                    lon=data['longitude'],
                    lat=data['latitude'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=self.plot_styles['color_palette'][0],
                        opacity=0.8
                    )
                ))
            
            fig.update_layout(
                title=title or "Geographic Distribution of Profiles",
                geo=dict(
                    projection_type='natural earth',
                    showland=True,
                    landcolor='lightgray',
                    showocean=True,
                    oceancolor='lightblue'
                ),
                template=self.plot_styles['template'],
                font=dict(family=self.plot_styles['font_family'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating geographic plot: {e}")
            return self.create_error_plot(f"Failed to create geographic plot: {e}")
    
    def create_statistical_plot(self, data: pd.DataFrame, title: str = "") -> go.Figure:
        """Create statistical distribution plot."""
        try:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                raise ValueError("No numeric columns found for statistical plot")
            
            # Choose primary variable (prefer temperature)
            primary_col = None
            for col in numeric_cols:
                if 'temp' in col.lower():
                    primary_col = col
                    break
            
            if not primary_col:
                primary_col = numeric_cols[0]
            
            # Create histogram with box plot
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=[f'{primary_col.title()} Distribution', f'{primary_col.title()} Box Plot'],
                vertical_spacing=0.1
            )
            
            # Histogram
            fig.add_trace(
                go.Histogram(
                    x=data[primary_col],
                    nbinsx=30,
                    name='Distribution',
                    marker_color=self.plot_styles['color_palette'][0],
                    opacity=0.7
                ),
                row=1, col=1
            )
            
            # Box plot
            fig.add_trace(
                go.Box(
                    y=data[primary_col],
                    name='Box Plot',
                    marker_color=self.plot_styles['color_palette'][1]
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                title=title or f"Statistical Analysis of {primary_col.title()}",
                template=self.plot_styles['template'],
                font=dict(family=self.plot_styles['font_family']),
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating statistical plot: {e}")
            return self.create_error_plot(f"Failed to create statistical plot: {e}")
    
    def create_error_plot(self, error_message: str) -> go.Figure:
        """Create an error plot when visualization fails."""
        fig = go.Figure()
        fig.add_annotation(
            text=f"Visualization Error:<br>{error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="Visualization Error",
            template=self.plot_styles['template'],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def generate_plots(self, query: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate appropriate plots based on query and results."""
        plots = []
        
        try:
            if not self.should_generate_plots(query, results):
                logger.info("No plots needed for this query")
                return plots
            
            # Extract data
            if 'raw_data' not in results or not results['raw_data']:
                logger.warning("No raw data available for plotting")
                return plots
            
            data = pd.DataFrame(results['raw_data'])
            
            if data.empty:
                logger.warning("Empty dataset for plotting")
                return plots
            
            # Detect plot types
            plot_types = self.detect_plot_types(query, data)
            logger.info(f"Detected plot types: {plot_types}")
            
            # Generate plots
            for plot_type in plot_types:
                try:
                    if plot_type == 'temperature_depth':
                        fig = self.create_temperature_depth_plot(data)
                        plots.append({
                            'type': 'temperature_depth',
                            'title': 'Temperature vs Depth Profile',
                            'figure': fig
                        })
                    
                    elif plot_type == 'ts_diagram':
                        fig = self.create_ts_diagram(data)
                        plots.append({
                            'type': 'ts_diagram',
                            'title': 'Temperature-Salinity Diagram',
                            'figure': fig
                        })
                    
                    elif plot_type == 'geographic':
                        fig = self.create_geographic_plot(data)
                        plots.append({
                            'type': 'geographic',
                            'title': 'Geographic Distribution',
                            'figure': fig
                        })
                    
                    elif plot_type == 'statistical':
                        fig = self.create_statistical_plot(data)
                        plots.append({
                            'type': 'statistical',
                            'title': 'Statistical Analysis',
                            'figure': fig
                        })
                
                except Exception as e:
                    logger.error(f"Error creating {plot_type} plot: {e}")
                    continue
            
            logger.info(f"Generated {len(plots)} plots")
            return plots
            
        except Exception as e:
            logger.error(f"Error in plot generation: {e}")
            return plots
