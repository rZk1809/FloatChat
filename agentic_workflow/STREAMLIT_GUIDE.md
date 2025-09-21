# 🌊 Streamlit Web Application Guide

## Overview

The Agentic AI RAG Workflow System now includes a modern web interface built with Streamlit, providing an intuitive way to analyze ARGO oceanographic data through natural language queries.

## Features

### 🔍 **Natural Language Query Interface**
- Enter queries in plain English about oceanographic data
- Example queries provided for quick start
- Real-time processing with progress indicators
- Query history tracking and rerun capability

### 📊 **Automatic Visualization Generation**
- **PlottingAgent** automatically detects when visualizations would be helpful
- Supports multiple plot types:
  - Temperature vs Depth profiles
  - Temperature-Salinity (T-S) diagrams
  - Geographic distribution maps
  - Statistical distribution plots
  - Time series analysis
  - Comparison plots

### 📥 **Advanced Export Functionality**
- **Individual Plot Export**: PNG, PDF, JPEG, SVG formats
- **Bulk Export**: Download all plots as ZIP file
- **Full Report Export**: Complete PDF report with analysis and embedded plots
- **Customizable Export Options**: Resolution, DPI, dimensions
- **Data Export**: Download raw analysis data as CSV

### 🔌 **System Monitoring**
- Real-time service status (PostgreSQL, ChromaDB, Ollama)
- Connection health indicators
- Performance metrics and execution timing

## Installation and Setup

### 1. Install Dependencies

```bash
cd agentic_workflow
pip install -r requirements.txt
```

### 2. Verify System Requirements

Ensure the following services are running:
- **PostgreSQL**: Database with ARGO data (`argo_data` database)
- **ChromaDB**: Vector database with profile embeddings
- **Ollama**: Local LLM service with required models
  - `embeddinggemma:300m` for embeddings
  - `qwen2:1.5b` for text generation

### 3. Launch the Web Application

```bash
streamlit run streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage Guide

### Getting Started

1. **Check System Status**: The sidebar shows connection status for all services
2. **Try Example Queries**: Use the dropdown to select pre-built example queries
3. **Enter Custom Query**: Type your question in natural language
4. **Enable Technical Mode**: Check the box for detailed technical information
5. **Click Analyze**: Process your query through the multi-agent system

### Example Queries

```
"Show temperature statistics for Bay of Bengal profiles"
"Create a temperature vs depth plot for profiles in the Arabian Sea"
"Analyze salinity trends in the Indian Ocean over the last year"
"Plot temperature profile for Mediterranean Sea and show T-S diagram"
"Compare temperature variations between Pacific and Atlantic profiles"
```

### Understanding Results

The system provides:
- **Summary**: Natural language explanation of findings
- **Data Metrics**: Number of profiles, measurements, execution time
- **Recommendations**: Actionable insights for further analysis
- **Raw Data Preview**: Tabular view of underlying data
- **Visualizations**: Automatically generated plots when appropriate

### Export Options

#### Plot Export
- **Individual Plots**: Click format buttons (PNG, PDF, JPEG, SVG) below each plot
- **Bulk Export**: Use "Export All Plots" button for ZIP download
- **Custom Settings**: Adjust resolution, dimensions, and DPI in sidebar

#### Report Export
- **Full Report**: Click "Export Full Report (PDF)" for complete analysis document
- **Data Export**: Download raw data as CSV from data preview section

### Advanced Features

#### Query History
- View last 5 queries in sidebar
- Rerun previous queries with one click
- Track success/failure status

#### Technical Mode
- Detailed execution information
- Performance metrics
- Debug information for troubleshooting

#### Progress Tracking
- Real-time progress indicators
- Stage-by-stage execution updates
- Error reporting and recovery

## Architecture

### Multi-Agent Workflow
```
User Query → Planner Agent → Executor Agent → Synthesizer Agent → Plotting Agent → Results
```

### Components

1. **PlannerAgent**: Parses natural language and creates execution plans
2. **ExecutorAgent**: Orchestrates tool execution and data retrieval
3. **SynthesizerAgent**: Generates natural language responses
4. **PlottingAgent**: Creates appropriate visualizations automatically
5. **WorkflowEngine**: Coordinates all agents and manages workflow

### Data Flow

1. **Query Processing**: Natural language parsing and intent detection
2. **Plan Generation**: Create structured execution plan
3. **Data Retrieval**: Access PostgreSQL and ChromaDB
4. **Analysis**: Statistical and oceanographic calculations
5. **Synthesis**: Generate comprehensive response
6. **Visualization**: Automatic plot generation when beneficial
7. **Export**: Multiple format options for results and plots

## Troubleshooting

### Common Issues

#### Service Connection Errors
- **PostgreSQL**: Check database credentials and connection
- **ChromaDB**: Verify database path and collection exists
- **Ollama**: Ensure service is running and models are available

#### Plot Generation Issues
- **Missing Data**: Ensure query returns sufficient numeric data
- **Format Errors**: Check data types and column names
- **Export Failures**: Verify sufficient disk space and permissions

#### Performance Issues
- **Slow Queries**: Large datasets may take time to process
- **Memory Usage**: Complex visualizations require adequate RAM
- **Network Timeouts**: Ollama API calls may timeout on slow connections

### Debug Mode

Enable technical mode for detailed information:
- Execution timing for each stage
- Data retrieval statistics
- Error messages and stack traces
- Service connection details

## Configuration

### Environment Variables
```bash
# Database configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=argo_data
POSTGRES_USER=rgk
POSTGRES_PASSWORD=rgk

# ChromaDB configuration
CHROMADB_PATH=../chroma_db
CHROMADB_COLLECTION=argo_profiles_ollama

# Ollama configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
EMBEDDING_MODEL=embeddinggemma:300m
LLM_MODEL=qwen2:1.5b
```

### Customization

#### Plot Styling
Modify `plotting_agent.py` to customize:
- Color palettes
- Font families and sizes
- Plot templates and themes
- Default dimensions

#### Export Settings
Adjust default export parameters:
- Image resolution and DPI
- PDF page sizes and layouts
- Compression settings
- File naming conventions

## API Integration

The web application can be extended with API endpoints:

```python
# Example API endpoint
@st.cache_data
def process_api_query(query: str, format: str = "json"):
    results = workflow_engine.process_query(query)
    if format == "json":
        return results
    elif format == "pdf":
        return create_analysis_report(results)
```

## Performance Optimization

### Caching
- Query results cached for repeated requests
- Plot generation cached for identical data
- Database connections pooled for efficiency

### Scalability
- Stateless design for horizontal scaling
- Configurable resource limits
- Background processing for large queries

## Security Considerations

- Input validation for all user queries
- SQL injection prevention
- File upload restrictions
- Session management and timeouts
- Secure export file handling

---

**For technical support or feature requests, please refer to the main project documentation or contact the development team.**
