# 🌊 Agentic AI RAG Workflow System for ARGO Float Data

A comprehensive intelligent system for analyzing oceanographic data from ARGO floats using retrieval-augmented generation and multi-agent workflows.

## 🎯 Overview

This system provides natural language querying capabilities for ARGO float oceanographic data, combining:
- **Vector Retrieval**: Semantic search through ChromaDB for relevant profiles
- **SQL Execution**: Detailed data extraction from PostgreSQL database
- **Intelligent Analysis**: Oceanographic calculations and statistical analysis
- **Automated Visualization**: Plot generation for data interpretation
- **Natural Language Synthesis**: AI-powered response generation

## 🏗️ Architecture

The system follows a multi-agent architecture:

```
User Query → Planner Agent → Executor Agent → Synthesizer Agent → Response
                ↓              ↓               ↓
            Parse Query    Execute Tools   Generate Response
            Generate Plan  - Retriever     - Natural Language
                          - SQL Executor   - Technical Details
                          - Analyzer       - Recommendations
                          - Visualizer
```

## 📁 Directory Structure

```
agentic_workflow/
├── agents/                 # AI agents
│   ├── planner_agent.py   # Query understanding & planning
│   ├── executor_agent.py  # Tool execution & orchestration
│   └── synthesizer_agent.py # Response generation
├── tools/                 # Data access & processing tools
│   ├── retriever_tool.py  # ChromaDB vector search
│   ├── sql_executor_tool.py # PostgreSQL queries
│   ├── analyzer_tool.py   # Oceanographic analysis
│   └── visualizer_tool.py # Plot generation
├── core/                  # Core system components
│   ├── config.py         # Configuration management
│   └── workflow_engine.py # Main orchestration engine
├── ui/                   # User interfaces
│   └── cli_interface.py  # Command-line interface
├── utils/                # Utilities
│   └── logger.py         # XAI logging system
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

1. **PostgreSQL Database**: Running with `argo_data` database
2. **ChromaDB**: Persistent client at `./chroma_db` with `argo_profiles_ollama` collection
3. **Ollama**: Running on `http://localhost:11434` with models:
   - `embeddinggemma:300m` (embeddings)
   - `qwen2:1.5b` (text generation)

### Installation

1. Navigate to the agentic workflow directory:
```bash
cd agentic_workflow
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify system status:
```bash
python main.py --info
```

### Usage

#### Interactive CLI Mode (Default)
```bash
python main.py
```

#### Single Query Mode
```bash
python main.py --query "Analyze temperature profiles in the Bay of Bengal for January 2024"
```

#### Batch Processing
```bash
python main.py --batch queries.txt --output results.json
```

#### JSON Output
```bash
python main.py --query "Compare salinity in Arabian Sea vs Bay of Bengal" --format json
```

## 📝 Example Queries

- "Analyze the average temperature profile in the Bay of Bengal for January 2024 and plot it"
- "Compare temperature and salinity profiles between Arabian Sea and Bay of Bengal"
- "Show me temperature-salinity diagrams for profiles in the Indian Ocean"
- "Find ARGO profiles with unusual temperature patterns in the Southern Ocean"
- "Calculate statistics for all profiles in the Bay of Bengal during 2024"

## 🔧 Configuration

The system configuration is managed in `core/config.py`:

```python
# Database settings
DATABASE_CONFIG.user = "rgk"
DATABASE_CONFIG.password = "rgk"
DATABASE_CONFIG.host = "localhost"
DATABASE_CONFIG.port = "5432"
DATABASE_CONFIG.name = "argo_data"

# ChromaDB settings
CHROMADB_CONFIG.db_path = "./chroma_db"
CHROMADB_CONFIG.collection_name = "argo_profiles_ollama"

# Ollama settings
OLLAMA_CONFIG.base_url = "http://localhost:11434"
OLLAMA_CONFIG.embedding_model = "embeddinggemma:300m"
OLLAMA_CONFIG.general_model = "qwen2:1.5b"
```

## 🛠️ System Components

### Agents

1. **PlannerAgent**: Parses natural language queries and generates execution plans
2. **ExecutorAgent**: Executes plans using available tools and manages data flow
3. **SynthesizerAgent**: Generates natural language responses from results

### Tools

1. **RetrieverTool**: Semantic search through ChromaDB vector store
2. **SQLExecutorTool**: SQL query execution against PostgreSQL database
3. **AnalyzerTool**: Oceanographic analysis and statistical calculations
4. **VisualizerTool**: Plot generation for data visualization

### Core

1. **WorkflowEngine**: Main orchestration engine managing agent interactions
2. **Config**: Centralized configuration management with validation

## 📊 Data Sources

- **PostgreSQL Tables**:
  - `floats`: ARGO float metadata
  - `profiles`: Profile locations and timestamps
  - `measurements`: Temperature, salinity, pressure data

- **ChromaDB Collection**:
  - `argo_profiles_ollama`: Vector embeddings of profile summaries

## 🔍 Explainable AI (XAI)

The system includes comprehensive XAI logging:
- Query parsing decisions
- Data access operations
- Analysis method selection
- Response synthesis reasoning

Logs are stored in `xai_audit.log` and `agentic_workflow.log`.

## 🚨 Error Handling

The system includes robust error handling:
- Service availability validation
- Graceful degradation when services are unavailable
- Detailed error reporting with context
- Automatic retry mechanisms for transient failures

## 🧪 Testing

Run system validation:
```bash
python main.py --info
```

Test with example query:
```bash
python main.py --query "Show temperature statistics for Bay of Bengal" --technical
```

## 📈 Performance

- **Concurrent Processing**: Tools execute in parallel where possible
- **Caching**: Database connections and ChromaDB collections are cached
- **Streaming**: Large result sets are processed incrementally
- **Resource Management**: Configurable limits for memory and processing

## 🔒 Security

- **Input Validation**: All user inputs are validated and sanitized
- **SQL Injection Prevention**: Parameterized queries only
- **Resource Limits**: Configurable quotas for queries and results
- **Audit Logging**: Complete audit trail of all operations

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive docstrings and type hints
3. Include error handling and logging
4. Test with various query types and edge cases
5. Update documentation for new features

## 📄 License

This project is part of the SIH 2025 initiative for intelligent oceanographic data analysis.

## 🆘 Support

For issues or questions:
1. Check system status: `python main.py --info`
2. Review logs: `agentic_workflow.log` and `xai_audit.log`
3. Validate data sources are accessible
4. Ensure all required models are available in Ollama
