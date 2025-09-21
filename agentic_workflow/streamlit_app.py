"""
Streamlit Web Application for Agentic AI RAG Workflow System.
Provides a modern web interface for oceanographic data analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import traceback
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import zipfile
import tempfile
import os

# Configure page
st.set_page_config(
    page_title="🌊 Agentic AI ARGO Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import workflow components
try:
    from core.workflow_engine import WorkflowEngine
    from core.config import config
    from utils.logger import setup_logging
except ImportError as e:
    st.error(f"Failed to import workflow components: {e}")
    st.stop()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize session state
if 'workflow_engine' not in st.session_state:
    try:
        st.session_state.workflow_engine = WorkflowEngine()
        st.session_state.query_history = []
        st.session_state.current_results = None
        st.session_state.plots = []
    except Exception as e:
        st.error(f"Failed to initialize workflow engine: {e}")
        st.stop()

def display_system_status():
    """Display system status in the sidebar."""
    st.sidebar.header("🔌 System Status")
    
    try:
        connections = config.validate_connections()
        
        # Overall status
        all_connected = all(connections.values())
        status_color = "🟢" if all_connected else "🟡"
        st.sidebar.markdown(f"{status_color} **Overall Status**: {'Ready' if all_connected else 'Partial'}")
        
        # Individual services
        service_icons = {
            'postgresql': '🐘',
            'chromadb': '🔍', 
            'ollama': '🤖'
        }
        
        for service, status in connections.items():
            icon = service_icons.get(service, '⚙️')
            status_icon = "✅" if status else "❌"
            st.sidebar.markdown(f"{icon} {service.title()}: {status_icon}")
            
    except Exception as e:
        st.sidebar.error(f"Status check failed: {e}")

def display_query_history():
    """Display query history in the sidebar."""
    st.sidebar.header("📝 Query History")
    
    if st.session_state.query_history:
        for i, query_info in enumerate(reversed(st.session_state.query_history[-5:])):
            with st.sidebar.expander(f"Query {len(st.session_state.query_history) - i}"):
                st.write(f"**Query**: {query_info['query'][:50]}...")
                st.write(f"**Time**: {query_info['timestamp']}")
                st.write(f"**Status**: {query_info['status']}")
                if st.button(f"Rerun", key=f"rerun_{i}"):
                    st.session_state.current_query = query_info['query']
                    st.rerun()
    else:
        st.sidebar.info("No queries yet")

def create_progress_placeholder():
    """Create progress tracking placeholders."""
    progress_container = st.container()
    
    with progress_container:
        st.subheader("🔄 Processing Status")
        progress_bar = st.progress(0)
        status_text = st.empty()
        stage_info = st.empty()
        
    return progress_bar, status_text, stage_info

def update_progress(progress_bar, status_text, stage_info, stage: str, progress: float, details: str = ""):
    """Update progress indicators."""
    progress_bar.progress(progress)
    status_text.text(f"Current Stage: {stage}")
    if details:
        stage_info.info(details)

def format_analysis_results(results: Dict[str, Any]) -> None:
    """Format and display analysis results."""
    if not results:
        st.warning("No results to display")
        return
    
    # Main results section
    st.header("📊 Analysis Results")
    
    # Summary section
    if 'summary' in results:
        st.subheader("💡 Summary")
        st.markdown(results['summary'])
    
    # Data summary
    if 'data_summary' in results:
        st.subheader("📈 Data Summary")
        data_summary = results['data_summary']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Profiles Analyzed", data_summary.get('profiles_analyzed', 'N/A'))
        with col2:
            st.metric("Total Measurements", data_summary.get('total_measurements', 'N/A'))
        with col3:
            st.metric("Execution Time", f"{data_summary.get('execution_time', 0):.2f}s")
    
    # Recommendations
    if 'recommendations' in results:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(results['recommendations'], 1):
            st.markdown(f"{i}. {rec}")
    
    # Raw data preview
    if 'raw_data' in results and results['raw_data'] is not None:
        st.subheader("🔍 Data Preview")
        df = pd.DataFrame(results['raw_data'])
        st.dataframe(df.head(100), use_container_width=True)
        
        # Download button for full data
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Dataset (CSV)",
            data=csv,
            file_name=f"argo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def export_plot_as_image(fig, format_type: str, width: int = 1200, height: int = 800, scale: int = 2) -> bytes:
    """Export plot as image in specified format."""
    try:
        if format_type.lower() == 'pdf':
            return fig.to_image(format="pdf", width=width, height=height, scale=scale)
        elif format_type.lower() == 'png':
            return fig.to_image(format="png", width=width, height=height, scale=scale)
        elif format_type.lower() == 'jpeg':
            return fig.to_image(format="jpeg", width=width, height=height, scale=scale)
        elif format_type.lower() == 'svg':
            return fig.to_image(format="svg", width=width, height=height, scale=scale)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    except Exception as e:
        st.error(f"Failed to export plot as {format_type}: {e}")
        return None

def create_export_options():
    """Create export options sidebar."""
    st.sidebar.header("📥 Export Options")

    export_format = st.sidebar.selectbox(
        "Export Format",
        ["PNG", "PDF", "JPEG", "SVG"],
        help="Choose the format for plot export"
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        export_width = st.number_input("Width (px)", min_value=400, max_value=3000, value=1200, step=100)
    with col2:
        export_height = st.number_input("Height (px)", min_value=300, max_value=2000, value=800, step=100)

    export_dpi = st.sidebar.slider("DPI/Scale", min_value=1, max_value=4, value=2, help="Higher values = better quality")

    return export_format, export_width, export_height, export_dpi

def display_plots_with_export(plots: List[Dict[str, Any]]):
    """Display plots with export functionality."""
    if not plots:
        return

    st.header("📈 Visualizations")

    # Export options
    export_format, export_width, export_height, export_dpi = create_export_options()

    # Bulk export button
    if len(plots) > 1:
        if st.button("📦 Export All Plots", help="Download all plots as a ZIP file"):
            export_all_plots(plots, export_format, export_width, export_height, export_dpi)

    # Display individual plots
    for i, plot_data in enumerate(plots):
        plot_title = plot_data.get('title', f'Visualization {i+1}')
        st.subheader(f"Plot {i+1}: {plot_title}")

        # Display the plot
        fig = plot_data['figure']
        st.plotly_chart(fig, use_container_width=True)

        # Export buttons for individual plot
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"📥 PNG", key=f"png_{i}"):
                export_single_plot(fig, plot_title, "PNG", export_width, export_height, export_dpi)

        with col2:
            if st.button(f"📄 PDF", key=f"pdf_{i}"):
                export_single_plot(fig, plot_title, "PDF", export_width, export_height, export_dpi)

        with col3:
            if st.button(f"🖼️ JPEG", key=f"jpeg_{i}"):
                export_single_plot(fig, plot_title, "JPEG", export_width, export_height, export_dpi)

        with col4:
            if st.button(f"🎨 SVG", key=f"svg_{i}"):
                export_single_plot(fig, plot_title, "SVG", export_width, export_height, export_dpi)

        st.divider()

def export_single_plot(fig, title: str, format_type: str, width: int, height: int, scale: int):
    """Export a single plot."""
    try:
        image_bytes = export_plot_as_image(fig, format_type, width, height, scale)

        if image_bytes:
            filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type.lower()}"

            st.download_button(
                label=f"⬇️ Download {format_type}",
                data=image_bytes,
                file_name=filename,
                mime=f"image/{format_type.lower()}" if format_type != "PDF" else "application/pdf",
                key=f"download_{title}_{format_type}_{datetime.now().timestamp()}"
            )
    except Exception as e:
        st.error(f"Failed to export plot: {e}")

def export_all_plots(plots: List[Dict[str, Any]], format_type: str, width: int, height: int, scale: int):
    """Export all plots as a ZIP file."""
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "plots.zip")

            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for i, plot_data in enumerate(plots):
                    plot_title = plot_data.get('title', f'Plot_{i+1}').replace(' ', '_')
                    fig = plot_data['figure']

                    # Export plot
                    image_bytes = export_plot_as_image(fig, format_type, width, height, scale)

                    if image_bytes:
                        filename = f"{plot_title}_{i+1}.{format_type.lower()}"
                        zip_file.writestr(filename, image_bytes)

            # Read the ZIP file
            with open(zip_path, 'rb') as zip_file:
                zip_bytes = zip_file.read()

            # Provide download
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_bytes,
                file_name=f"argo_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                key=f"download_all_{datetime.now().timestamp()}"
            )

    except Exception as e:
        st.error(f"Failed to create ZIP file: {e}")

def create_analysis_report(results: Dict[str, Any], plots: List[Dict[str, Any]] = None) -> bytes:
    """Create a PDF report with analysis results and plots."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph("ARGO Oceanographic Data Analysis Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Timestamp
        timestamp = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        story.append(timestamp)
        story.append(Spacer(1, 12))

        # Summary
        if 'summary' in results:
            summary_title = Paragraph("Analysis Summary", styles['Heading2'])
            story.append(summary_title)
            summary_text = Paragraph(results['summary'], styles['Normal'])
            story.append(summary_text)
            story.append(Spacer(1, 12))

        # Data Summary
        if 'data_summary' in results:
            data_title = Paragraph("Data Summary", styles['Heading2'])
            story.append(data_title)

            data_summary = results['data_summary']
            for key, value in data_summary.items():
                item = Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal'])
                story.append(item)

            story.append(Spacer(1, 12))

        # Recommendations
        if 'recommendations' in results:
            rec_title = Paragraph("Recommendations", styles['Heading2'])
            story.append(rec_title)

            for i, rec in enumerate(results['recommendations'], 1):
                rec_text = Paragraph(f"{i}. {rec}", styles['Normal'])
                story.append(rec_text)

            story.append(Spacer(1, 12))

        # Add plots if available
        if plots:
            plots_title = Paragraph("Visualizations", styles['Heading2'])
            story.append(plots_title)

            for i, plot_data in enumerate(plots):
                plot_title = plot_data.get('title', f'Plot {i+1}')
                plot_heading = Paragraph(f"{i+1}. {plot_title}", styles['Heading3'])
                story.append(plot_heading)

                # Convert plot to image and add to PDF
                try:
                    fig = plot_data['figure']
                    img_bytes = export_plot_as_image(fig, "PNG", 800, 600, 2)

                    if img_bytes:
                        img_buffer = io.BytesIO(img_bytes)
                        img = Image(img_buffer, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))

                except Exception as e:
                    error_text = Paragraph(f"Error embedding plot: {e}", styles['Normal'])
                    story.append(error_text)
                    story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        st.error(f"Failed to create PDF report: {e}")
        return None

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🌊 Agentic AI ARGO Data Explorer")
    st.markdown("*An intelligent system for analyzing oceanographic data from ARGO floats*")
    
    # Sidebar
    display_system_status()
    display_query_history()
    
    # Main interface
    st.header("🔍 Natural Language Query Interface")
    
    # Query input
    query_examples = [
        "Show temperature statistics for Bay of Bengal profiles",
        "Create a temperature vs depth plot for profiles in the Arabian Sea", 
        "Analyze salinity trends in the Indian Ocean over the last year",
        "Plot temperature profile for Mediterranean Sea and show T-S diagram",
        "Compare temperature variations between Pacific and Atlantic profiles"
    ]
    
    # Example queries dropdown
    selected_example = st.selectbox(
        "💡 Try an example query:",
        [""] + query_examples,
        help="Select an example query to get started"
    )
    
    # Query input field
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    if selected_example:
        st.session_state.current_query = selected_example
    
    user_query = st.text_area(
        "Enter your query about ARGO oceanographic data:",
        value=st.session_state.current_query,
        height=100,
        help="Ask questions in natural language about temperature, salinity, pressure, or geographic regions"
    )
    
    # Query options
    col1, col2 = st.columns([3, 1])
    with col1:
        technical_mode = st.checkbox("Technical Mode", help="Show detailed technical information")
    with col2:
        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            if user_query.strip():
                process_query(user_query, technical_mode)
            else:
                st.warning("Please enter a query")
    
    # Display current results
    if st.session_state.current_results:
        format_analysis_results(st.session_state.current_results)

        # Export full report button
        if st.button("📋 Export Full Report (PDF)", help="Download complete analysis report with plots"):
            plots = st.session_state.current_results.get('plots', [])
            report_bytes = create_analysis_report(st.session_state.current_results, plots)

            if report_bytes:
                st.download_button(
                    label="⬇️ Download Report",
                    data=report_bytes,
                    file_name=f"argo_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key=f"report_download_{datetime.now().timestamp()}"
                )

    # Display plots with export functionality
    if st.session_state.current_results and 'plots' in st.session_state.current_results:
        display_plots_with_export(st.session_state.current_results['plots'])

def process_query(query: str, technical_mode: bool = False):
    """Process a user query through the workflow engine."""
    
    # Create progress tracking
    progress_bar, status_text, stage_info = create_progress_placeholder()
    
    try:
        # Update progress - Planning
        update_progress(progress_bar, status_text, stage_info, "Planning", 0.1, "Analyzing query and generating execution plan...")
        
        # Process query
        results = st.session_state.workflow_engine.process_query(
            user_query=query,
            session_id=None,
            include_technical_details=technical_mode
        )
        
        # Update progress - Execution
        update_progress(progress_bar, status_text, stage_info, "Execution", 0.5, "Executing analysis steps...")
        
        # Simulate progress updates (in real implementation, this would come from workflow engine)
        time.sleep(1)
        
        # Update progress - Synthesis
        update_progress(progress_bar, status_text, stage_info, "Synthesis", 0.8, "Generating final response...")
        time.sleep(1)
        
        # Complete
        update_progress(progress_bar, status_text, stage_info, "Complete", 1.0, "Analysis completed successfully!")
        
        # Store results
        st.session_state.current_results = results
        
        # Add to history
        st.session_state.query_history.append({
            'query': query,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Success',
            'results': results
        })
        
        # Success message
        st.success("✅ Analysis completed successfully!")
        
        # Clear progress after a moment
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        logger.error(traceback.format_exc())
        
        # Update progress - Error
        update_progress(progress_bar, status_text, stage_info, "Error", 0.0, f"Analysis failed: {str(e)}")
        
        st.error(f"❌ Analysis failed: {str(e)}")
        
        # Add to history
        st.session_state.query_history.append({
            'query': query,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Failed',
            'error': str(e)
        })

if __name__ == "__main__":
    main()
