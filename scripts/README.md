# Scripts

This directory contains all root-level utility and experimental scripts, organized by purpose.

## Subdirectories

### `data/`
Scripts for data acquisition, ingestion, and loading.
- `scrapper.py` — Web scraper for collecting raw data from external sources
- `ingestion.py` — Data ingestion pipeline for processing and importing data
- `loading.py` — Utilities for loading datasets into memory or downstream components

### `database/`
Scripts for database setup, population, and data persistence.
- `postgres.py` — PostgreSQL connection and query utilities
- `populate.py` — Populates the database with initial or seed data
- `save.py` — Saves processed records to the database
- `full_save.py` — Full-batch save operation for bulk database writes

### `vector_store/`
Scripts related to vector database management and embedding storage.
- `chroma.py` — ChromaDB integration for storing and querying vector embeddings
- `chrom.py` — Alternate/experimental ChromaDB script
- `vector.py` — General vector store utilities and embedding helpers

### `ml/`
Machine learning model scripts covering clustering, anomaly detection, and forecasting.
- `clustering.py` — Clustering algorithms applied to the dataset
- `anomaly.py` — Anomaly detection (first approach)
- `anomaly2.py` — Anomaly detection (second/refined approach)
- `xg.py` — XGBoost model training and evaluation
- `timeseries.py` — Time-series analysis and forecasting models

### `analysis/`
Exploratory data analysis, visualization, and explainability scripts.
- `xai.py` — Explainable AI (XAI) techniques for model interpretability
- `vis.py` — Data visualizations and charting utilities
- `peek.py` — Quick data inspection and summary statistics
- `s1.py` — Standalone analysis/experiment script (session 1)
- `mass.py` — Mass/bulk analysis across the dataset

### `apps/`
Application entry points and Streamlit/web app scripts.
- `app.py` — Primary application interface
- `app1.py` — Alternate or experimental application interface

## Test Files
- `test.py` — General test script
- `test1.py` — Additional test script
