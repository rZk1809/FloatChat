# 🌊 FloatChat — Intelligent Oceanographic Data Analysis

<div align="center">

![FloatChat Banner](web/public/plots/ts_diagram_clusters.png)

**AI-powered ARGO float data analysis through natural language queries**

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![SIH 2025](https://img.shields.io/badge/SIH-2025-orange.svg)](https://sih.gov.in)

[🚀 Live Demo](#live-demo) · [📖 Docs](agentic_workflow/README.md) · [🐛 Issues](https://github.com/rZk1809/FloatChat/issues)

</div>

---

## What is FloatChat?

FloatChat is a **multi-agent AI system** for analyzing ARGO oceanographic float data. It enables researchers to ask questions in plain English and receive comprehensive analyses complete with visualizations — no SQL or coding required.

Built for **SIH 2025 (Smart India Hackathon)**, FloatChat covers strategic Indian Ocean regions critical to climate science and monsoon prediction.

---

## System Architecture

```
User Natural Language Query
         │
         ▼
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│  Planner Agent  │────▶│ Parse intent · Identify region/time · Plan   │
└─────────────────┘     └──────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│ Executor Agent  │────▶│ ChromaDB search · PostgreSQL query · Analyze │
└─────────────────┘     └──────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐  ┌──────────────────────────────────────────────┐
│ Synthesizer Agent   │─▶│ LLM (Ollama qwen2:1.5b) → Natural language   │
└─────────────────────┘  └──────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│ Plotting Agent  │────▶│ Auto-detect viz type · Generate Plotly chart  │
└─────────────────┘     └──────────────────────────────────────────────┘
         │
         ▼
    Complete Analysis Output
```

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-Agent AI** | 4 specialized agents working in sequence (Planner → Executor → Synthesizer → Plotter) |
| **Hybrid RAG** | ChromaDB vector search + PostgreSQL structured queries over 4,922 ARGO profiles |
| **Auto Visualization** | Query-intent detection generates the right chart automatically |
| **ML Analytics** | K-Means clustering, XGBoost prediction (R²=0.97), Isolation Forest anomaly detection |
| **XAI Logging** | SHAP values, PDP plots, structured audit logs for every decision |
| **Multi-format Export** | PNG, PDF, JPEG, SVG, CSV, ZIP, full analysis reports |

---

## Visualizations

All 17 visualizations below were generated automatically by FloatChat from real ARGO data:

### Clustering Analysis

| T-S Diagram | Geographic Distribution | Cluster Sizes |
|---|---|---|
| ![T-S Diagram](plots/ts_diagram_clusters.png) | ![Map](plots/map_clusters.png) | ![Sizes](plots/cluster_sizes.png) |

| Clustering Metrics | Elbow Method | Pairplot |
|---|---|---|
| ![Metrics](plots/clustering_metrics.png) | ![Elbow](plots/elbow_method.png) | ![Pairplot](plots/pairplot_clusters.png) |

### Statistical Distributions

| Temperature Histograms | Salinity Histograms |
|---|---|
| ![Temp](plots/temp_histograms_per_cluster.png) | ![Salinity](plots/salinity_histograms_per_cluster.png) |

### XGBoost ML Model (Temperature Prediction, R²=0.97)

| Feature Importance | Predicted vs Actual | Hexbin Density |
|---|---|---|
| ![FI](plots/feature_importance.png) | ![Scatter](plots/predicted_vs_actual_scatter.png) | ![Hexbin](plots/predicted_vs_actual_hexbin.png) |

| Residuals Histogram | Q-Q Plot | Residuals vs Actual |
|---|---|---|
| ![Hist](plots/residuals_histogram.png) | ![QQ](plots/residuals_qq_plot.png) | ![RvA](plots/residuals_vs_actual.png) |

### Explainable AI (XAI)

| PDP — Latitude | PDP — Day (sin) |
|---|---|
| ![Lat](plots/pdp_latitude.png) | ![Day](plots/pdp_day_sin.png) |

---

## Repository Structure

```
FloatChat/
├── agentic_workflow/          # Production multi-agent system
│   ├── main.py                # CLI entry point
│   ├── streamlit_app.py       # Streamlit web UI (port 8501)
│   ├── agents/                # 4 specialized AI agents
│   │   ├── planner_agent.py
│   │   ├── executor_agent.py
│   │   ├── synthesizer_agent.py
│   │   └── plotting_agent.py
│   ├── tools/                 # Data access & analysis tools
│   │   ├── retriever_tool.py  # ChromaDB semantic search
│   │   ├── sql_executor_tool.py  # PostgreSQL queries
│   │   ├── analyzer_tool.py   # Oceanographic calculations
│   │   └── visualizer_tool.py # Matplotlib/Plotly charts
│   ├── core/
│   │   ├── config.py          # Centralized configuration
│   │   └── workflow_engine.py # Pipeline orchestration
│   ├── ui/cli_interface.py    # Rich CLI interface
│   ├── utils/logger.py        # XAI audit logging
│   └── requirements.txt
│
├── web/                       # Next.js web app (Vercel deployment)
│   ├── src/app/               # App Router pages & API routes
│   ├── src/components/        # React components
│   ├── public/plots/          # Static visualizations
│   └── package.json
│
├── scripts/                   # Data pipeline scripts
│   ├── data/                  # ARGO data acquisition & ingestion
│   ├── database/              # PostgreSQL operations
│   ├── vector_store/          # ChromaDB operations
│   ├── ml/                    # ML model training
│   └── analysis/              # Analysis & XAI scripts
│
├── plots/                     # Generated visualizations (17 PNG files)
└── README.md
```

---

## Quick Start — Local (Full System)

### Prerequisites

- Python 3.10+
- PostgreSQL with database `argo_data`
- [Ollama](https://ollama.ai) running with models:
  - `ollama pull embeddinggemma:300m`
  - `ollama pull qwen2:1.5b`

### Install & Run

```bash
# Clone
git clone https://github.com/rZk1809/FloatChat.git
cd FloatChat/agentic_workflow

# Install dependencies
pip install -r requirements.txt

# Run interactive CLI
python main.py

# Or launch web UI (port 8501)
streamlit run streamlit_app.py
```

### Example Queries

```
🌊 Show temperature statistics for Bay of Bengal profiles
🌊 Create a temperature vs depth plot for Arabian Sea
🌊 Analyze salinity trends in the Indian Ocean over the last year
🌊 Plot T-S diagram and show water mass clusters
🌊 Detect anomalous profiles in the dataset
```

---

## Quick Start — Web App (Vercel)

The `web/` directory contains a Next.js app deployable to Vercel with a live Claude AI demo.

```bash
cd web
npm install
cp .env.example .env.local
# Add your ANTHROPIC_API_KEY to .env.local
npm run dev
```

Deploy to Vercel:
1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Set Root Directory to `web/`
3. Add environment variable: `ANTHROPIC_API_KEY`
4. Deploy 🚀

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **AI / LLM** | Ollama (qwen2:1.5b, embeddinggemma:300m), Claude API (web demo) |
| **Vector DB** | ChromaDB (4,922 ARGO profile embeddings) |
| **Relational DB** | PostgreSQL (measurements, profiles, floats tables) |
| **ML Models** | XGBoost, K-Means, Isolation Forest, ARIMA/SARIMA |
| **Data Science** | pandas, numpy, scipy, scikit-learn, statsmodels |
| **Visualization** | Plotly, Matplotlib, Seaborn, Cartopy |
| **XAI** | SHAP, Partial Dependence Plots, Feature Importance |
| **Web UI** | Streamlit (local), Next.js 14 + Tailwind (Vercel) |
| **Export** | ReportLab (PDF), Kaleido (static images), CSV |

---

## Ocean Coverage

| Region | Bounds | Key Dynamics |
|---|---|---|
| Bay of Bengal | 5-25°N, 80-100°E | Monsoon influence, freshwater flux, barrier layer |
| Arabian Sea | 5-25°N, 60-80°E | Warm pool, high evaporation, upwelling zones |
| Indian Ocean | 60°S-30°N, 20-120°E | Full basin thermocline, monsoon circulation |
| Southern Ocean | 80-40°S, global | Deep water formation, carbon sink, ACC |

---

## Author

**Rohith Ganesh Kanchi (RGK1809)**  
Smart India Hackathon 2025  
[GitHub](https://github.com/rZk1809) · [rohithgankan@gmail.com](mailto:rohithgankan@gmail.com)

---

## License

MIT © 2025 Rohith Ganesh Kanchi
