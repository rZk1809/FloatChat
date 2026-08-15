import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import chromadb
import requests
import json
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Configuration ---
# Database and Model Settings
import os

DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "argo_data")
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "chroma_db")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "argo_profiles_ollama")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "")
OLLAMA_QA_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "")
_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_URL = f"{_OLLAMA_BASE_URL}/api/embeddings"
OLLAMA_GENERATE_URL = f"{_OLLAMA_BASE_URL}/api/generate"
MAX_CONTEXT_LENGTH = 2000

def is_oceanographic_query(query):
    """Check if query is actually about oceanographic data."""
    query_lower = query.lower()
    
    # Simple greetings and non-oceanographic queries
    simple_queries = ["hi", "hello", "hey", "thanks", "thank you", "ok", "okay"]
    if query_lower.strip() in simple_queries:
        return False
    
    # Oceanographic keywords
    ocean_keywords = [
        "temperature", "temp", "salinity", "psal", "pressure", "depth",
        "profile", "float", "argo", "ocean", "sea", "marine", "water",
        "latitude", "longitude", "location", "atlantic", "pacific", "indian",
        "degrees", "depth", "meter", "dbar"
    ]
    
    return any(keyword in query_lower for keyword in ocean_keywords)

def generate_simple_response(query):
    """Generate simple responses for non-oceanographic queries."""
    query_lower = query.lower().strip()
    
    if query_lower in ["hi", "hello", "hey"]:
        return "Hello! I'm FloatChat, your oceanographic data assistant. Ask me about ARGO float data, temperature profiles, salinity measurements, or ocean locations!"
    elif query_lower in ["thanks", "thank you"]:
        return "You're welcome! Feel free to ask me more questions about oceanographic data."
    else:
        return "I'm specialized in oceanographic data analysis. Please ask me about ARGO floats, temperature, salinity, pressure measurements, or ocean locations!"

def fix_sql_schema(sql_query):
    """Fix common SQL schema issues."""
    # Fix the profile_id reference issue
    sql_query = sql_query.replace("p.profile_id", "p.id")
    sql_query = sql_query.replace("ON p.profile_id", "ON p.id")
    
    # Fix geography syntax issues
    sql_query = sql_query.replace("location = ANY (GEOGRAPHY)", "location IS NOT NULL")
    sql_query = sql_query.replace("WHERE location = ANY", "WHERE location IS NOT NULL AND")
    
    # Ensure proper joins
    if "JOIN measurements m" in sql_query:
        sql_query = sql_query.replace("JOIN measurements m ON p.id = m.profile_id", 
                                    "JOIN measurements m ON p.id = m.profile_id")
    
    return sql_query

# --- XAI Decision Trail Class ---
class XAIDecisionTrail:
    """Tracks all decisions and reasoning steps for explainability."""
    
    def __init__(self, query):
        self.query = query
        self.timestamp = datetime.now()
        self.steps = []
        self.confidence_scores = {}
        self.reasoning_chain = []
        self.data_lineage = []
        self.assumptions = []
        
    def add_step(self, step_name, description, data=None, confidence=None):
        """Add a processing step with optional confidence score."""
        step = {
            "name": step_name,
            "description": description,
            "timestamp": datetime.now(),
            "data": data,
            "confidence": confidence
        }
        self.steps.append(step)
        if confidence is not None:
            self.confidence_scores[step_name] = confidence
            
    def add_reasoning(self, component, reasoning, evidence=None):
        """Add reasoning for a specific component."""
        self.reasoning_chain.append({
            "component": component,
            "reasoning": reasoning,
            "evidence": evidence,
            "timestamp": datetime.now()
        })
        
    def add_data_source(self, source_type, source_id, relevance_score=None, selection_criteria=None):
        """Track data lineage and source selection."""
        self.data_lineage.append({
            "source_type": source_type,
            "source_id": source_id,
            "relevance_score": relevance_score,
            "selection_criteria": selection_criteria,
            "timestamp": datetime.now()
        })
        
    def add_assumption(self, assumption, impact=None):
        """Document assumptions made during processing."""
        self.assumptions.append({
            "assumption": assumption,
            "impact": impact,
            "timestamp": datetime.now()
        })

# --- Caching for Performance ---
@st.cache_resource
def get_db_engine():
    """Legacy database access is intentionally disabled."""
    return None

@st.cache_resource
def get_chroma_collection():
    """Legacy live-store access is intentionally disabled."""
    return None

# --- Enhanced XAI Functions ---
def get_embedding_from_ollama(doc, model_name, trail=None):
    """Gets a vector embedding with XAI tracking."""
    try:
        if trail:
            trail.add_step("embedding_generation", 
                          f"Converting query to vector using {model_name}", 
                          {"input_length": len(doc), "model": model_name})
        
        payload = {"model": model_name, "prompt": doc}
        response = requests.post(OLLAMA_EMBED_URL, json=payload)
        response.raise_for_status()
        embedding = response.json().get("embedding")
        
        if trail and embedding:
            trail.add_step("embedding_success", 
                          f"Generated {len(embedding)}-dimensional embedding",
                          {"embedding_dim": len(embedding)},
                          confidence=0.95)
            
        return embedding
    except Exception as e:
        if trail:
            trail.add_step("embedding_error", f"Failed to generate embedding: {e}", confidence=0.0)
        logging.error(f"Failed to get embedding: {e}")
        return None

def retrieve_relevant_profiles(query, collection, n_results=10, trail=None):
    """Optimized retrieval with performance improvements."""
    if not query or not collection: 
        return [], "", []
    
    # Limit query length for faster embedding generation
    query_truncated = query[:500] if len(query) > 500 else query
    
    if trail:
        trail.add_reasoning("retrieval_strategy", 
                          f"Using semantic similarity search with top-{n_results} results",
                          f"Query length: {len(query_truncated)} characters (truncated from {len(query)})")
    
    query_embedding = get_embedding_from_ollama(query_truncated, OLLAMA_EMBED_MODEL, trail)
    if not query_embedding: 
        return [], "", []
    
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    
    # Limit context length for performance
    documents = results.get('documents', [[]])[0]
    context_docs = "\n".join(documents)
    if len(context_docs) > MAX_CONTEXT_LENGTH:
        context_docs = context_docs[:MAX_CONTEXT_LENGTH] + "..."
    
    distances = results.get('distances', [[]])[0]
    
    # Simplified XAI tracking for performance
    if trail:
        profile_ids = results.get('ids', [[]])[0]
        avg_relevance = np.mean([1.0 - d for d in distances]) if distances else 0
        trail.add_step("context_retrieval", 
                      f"Retrieved {len(profile_ids)} relevant profiles (fast mode)",
                      {"avg_relevance": avg_relevance, "context_length": len(context_docs)},
                      confidence=min(avg_relevance * 1.2, 1.0))
    
    return results.get('ids', [[]])[0], context_docs, distances

def analyze_sql_complexity(sql_query):
    """Analyze SQL query complexity for XAI insights."""
    complexity_indicators = {
        "joins": sql_query.lower().count("join"),
        "subqueries": sql_query.lower().count("select") - 1,
        "aggregations": sum([sql_query.lower().count(func) for func in ["count", "sum", "avg", "max", "min"]]),
        "conditions": sql_query.lower().count("where") + sql_query.lower().count("having"),
        "ordering": sql_query.lower().count("order by"),
        "grouping": sql_query.lower().count("group by")
    }
    
    total_complexity = sum(complexity_indicators.values())
    return complexity_indicators, total_complexity

def generate_sql_from_query(query, context_docs, trail=None):
    """Refuse the retired free-form text-to-SQL path.

    The canonical API converts user input into validated filters and executes
    trusted query templates. A model-generated SQL string must never cross the
    database boundary.
    """
    if trail:
        trail.add_step(
            "sql_generation_blocked",
            "Free-form text-to-SQL is disabled; use the canonical API",
            confidence=1.0,
        )
    return None

def execute_sql_query(sql_query, engine, trail=None):
    """Never execute SQL supplied as text by a model or caller."""
    if trail:
        trail.add_step(
            "sql_execution_blocked",
            "Arbitrary SQL execution is disabled; use trusted query templates",
            confidence=1.0,
        )
    return None, "This legacy text-to-SQL interface is disabled.", {}

def generate_final_answer(query, context_summary, trail=None):
    """Enhanced answer generation with confidence tracking."""
    if trail:
        trail.add_step("answer_generation", "Generating natural language response from query results")
    
    prompt = f"""
    You are an expert oceanographer's assistant. Your task is to answer the user's question based *only* on the provided data context.
    Do not use any prior knowledge. If the context does not contain the answer, state that the information is not available in the retrieved data.
    Be concise, clear, and mention any limitations or uncertainties in the data.
    
    DATA CONTEXT:
    {context_summary}
    
    USER'S QUESTION:
    {query}
    
    ANSWER:
    """
    
    payload = {"model": OLLAMA_QA_MODEL, "prompt": prompt, "stream": True}
    try:
        response = requests.post(OLLAMA_GENERATE_URL, json=payload, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                try:
                    json_chunk = json.loads(chunk.decode('utf-8'))
                    chunk_text = json_chunk.get("response", "")
                    full_response += chunk_text
                    yield chunk_text
                except json.JSONDecodeError: 
                    continue
        
        # Analyze answer quality for XAI
        if trail:
            answer_length = len(full_response)
            has_uncertainty = any(phrase in full_response.lower() for phrase in 
                                ["not available", "limited", "uncertain", "approximately", "may", "might"])
            
            confidence = 0.8 if has_uncertainty else 0.9
            trail.add_step("answer_completion", 
                          f"Generated {answer_length}-character response",
                          {"length": answer_length, "contains_uncertainty": has_uncertainty},
                          confidence=confidence)
                          
    except requests.exceptions.RequestException as e:
        if trail:
            trail.add_step("answer_generation_error", f"Failed to generate answer: {e}", confidence=0.0)
        yield f"\n\n**Error:** Could not connect to Ollama. Details: {e}"

def create_xai_dashboard(trail, result_stats):
    """Create comprehensive XAI dashboard."""
    
    # Overall confidence score
    confidence_scores = list(trail.confidence_scores.values())
    overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
    
    # Create tabs for different XAI aspects
    xai_tab1, xai_tab2, xai_tab3, xai_tab4 = st.tabs([
        "🔍 Decision Trail", 
        "📊 Data Lineage", 
        "🧠 Reasoning Chain", 
        "⚠️ Assumptions & Limitations"
    ])
    
    with xai_tab1:
        st.subheader("Processing Steps & Confidence")
        
        # Confidence gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = overall_confidence * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Confidence (%)"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75, 'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Steps timeline
        for i, step in enumerate(trail.steps):
            with st.expander(f"Step {i+1}: {step['name']}", expanded=i==0):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Description:** {step['description']}")
                    st.write(f"**Timestamp:** {step['timestamp'].strftime('%H:%M:%S')}")
                    if step['data']:
                        st.json(step['data'])
                with col2:
                    if step['confidence'] is not None:
                        confidence_color = "green" if step['confidence'] > 0.8 else "orange" if step['confidence'] > 0.5 else "red"
                        st.markdown(f"<div style='text-align: center; color: {confidence_color}; font-size: 24px; font-weight: bold'>{step['confidence']:.2f}</div>", unsafe_allow_html=True)
                        st.markdown("<div style='text-align: center; font-size: 12px'>Confidence</div>", unsafe_allow_html=True)
    
    with xai_tab2:
        st.subheader("Data Sources & Selection")
        if trail.data_lineage:
            df_lineage = pd.DataFrame(trail.data_lineage)
            
            # Relevance score histogram
            if 'relevance_score' in df_lineage.columns and df_lineage['relevance_score'].notna().any():
                fig_hist = px.histogram(df_lineage, x='relevance_score', 
                                       title="Distribution of Source Relevance Scores",
                                       labels={'relevance_score': 'Relevance Score', 'count': 'Number of Sources'})
                st.plotly_chart(fig_hist, use_container_width=True)
            
            # Data sources table
            st.dataframe(df_lineage, use_container_width=True)
        else:
            st.info("No data lineage information available.")
    
    with xai_tab3:
        st.subheader("AI Reasoning Process")
        for i, reasoning in enumerate(trail.reasoning_chain):
            with st.expander(f"Reasoning {i+1}: {reasoning['component']}", expanded=i==0):
                st.write(f"**Logic:** {reasoning['reasoning']}")
                if reasoning['evidence']:
                    st.write(f"**Evidence:** {reasoning['evidence']}")
                st.write(f"**Time:** {reasoning['timestamp'].strftime('%H:%M:%S')}")
    
    with xai_tab4:
        st.subheader("System Assumptions & Limitations")
        
        # System limitations
        st.warning("""
        **Known Limitations:**
        - Text-to-SQL conversion may misinterpret complex queries
        - Semantic search depends on embedding quality
        - Results limited to available data in the database
        - Time-series analysis may be affected by irregular sampling
        """)
        
        # Query-specific assumptions
        if trail.assumptions:
            st.write("**Query-Specific Assumptions:**")
            for i, assumption in enumerate(trail.assumptions):
                st.write(f"{i+1}. **{assumption['assumption']}**")
                if assumption['impact']:
                    st.write(f"   *Impact:* {assumption['impact']}")
        
        # Data quality metrics
        if result_stats and result_stats.get('row_count', 0) > 0:
            st.write("**Data Quality Metrics:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Completeness", 
                         f"{(1 - sum(result_stats.get('null_counts', {}).values()) / (result_stats.get('row_count', 1) * result_stats.get('column_count', 1))) * 100:.1f}%")
            with col2:
                st.metric("Records Retrieved", result_stats.get('row_count', 0))
            with col3:
                st.metric("Memory Usage", f"{result_stats.get('memory_usage', 0) / 1024:.1f} KB")

# --- Enhanced Streamlit UI ---
st.set_page_config(page_title="FloatChat XAI", layout="wide", initial_sidebar_state="expanded")

# Sidebar for XAI settings
with st.sidebar:
    st.title("🔍 XAI Settings")
    
    show_confidence = st.checkbox("Show Confidence Scores", value=True)
    show_reasoning = st.checkbox("Show AI Reasoning", value=True)
    n_results = st.slider("Retrieval Results", min_value=5, max_value=20, value=10)
    
    st.divider()
    st.subheader("📊 System Status")
    engine = None
    collection = None
    st.caption("Legacy data access is disabled. Use the canonical Python API.")
    
    db_status = "✅ Connected" if engine else "❌ Disconnected"
    vector_status = "✅ Connected" if collection else "❌ Disconnected"
    
    st.write(f"**Database:** {db_status}")
    st.write(f"**Vector Store:** {vector_status}")

st.title("🌊 FloatChat: Explainable OceanAI Explorer")
st.markdown("*An XAI-powered system for transparent oceanographic data analysis*")

# Initialize chat history with XAI trails
if "messages" not in st.session_state:
    st.session_state.messages = []
if "xai_trails" not in st.session_state:
    st.session_state.xai_trails = []

# Display chat messages with enhanced XAI components
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "xai_trail" in message and show_reasoning:
            trail = message["xai_trail"]
            result_stats = message.get("result_stats", {})
            
            st.divider()
            create_xai_dashboard(trail, result_stats)
        
        if "plot_data" in message and message["plot_data"] is not None:
            st.divider()
            st.subheader("📈 Data Visualization")
            
            plot_data = message["plot_data"]
            fig = px.line(plot_data, x='value', y='pressure', color='variable',
                         title="Oceanographic Profile Data",
                         labels={'value': 'Measurement Value', 'pressure': 'Pressure (dbar)', 'variable': 'Parameter'})
            fig.update_yaxis(autorange="reversed")  # Pressure increases with depth
            st.plotly_chart(fig, use_container_width=True)

# Main chat input
if prompt := st.chat_input("Ask me about oceanographic data... (e.g., 'Show me temperature profiles from the North Atlantic')"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Check if it's a simple/non-oceanographic query
        if not is_oceanographic_query(prompt):
            simple_response = generate_simple_response(prompt)
            st.markdown(simple_response)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": simple_response
            })
        else:
            # Full XAI processing for oceanographic queries
            with st.spinner("🔍 Analyzing your query with full transparency..."):
                
                # Initialize XAI decision trail
                trail = XAIDecisionTrail(prompt)
                
                # 1. Enhanced Retrieval with XAI
                trail.add_step("query_analysis", f"Processing oceanographic query: '{prompt}'", 
                              {"query_length": len(prompt), "query_type": "oceanographic"})
                
                profile_ids, context_docs, distances = retrieve_relevant_profiles(
                    prompt, collection, n_results, trail)
                
                # 2. Enhanced Text-to-SQL with XAI
                sql_query = generate_sql_from_query(prompt, context_docs, trail)
                
                # 3. Enhanced SQL Execution with XAI
                df_data, context_summary, result_stats = execute_sql_query(sql_query, engine, trail)

                # 4. Enhanced Answer Generation with XAI
                response_generator = generate_final_answer(prompt, context_summary, trail)
                full_response = st.write_stream(response_generator)
                
                # Prepare visualization data
                plot_data = None
                if df_data is not None and not df_data.empty:
                    plot_vars = [col for col in ['temp', 'psal'] if col in df_data.columns]
                    if 'pressure' in df_data.columns and plot_vars:
                        plot_data = df_data.melt(id_vars=['pressure'], value_vars=plot_vars,
                                               var_name='variable', value_name='value')
                        trail.add_step("visualization", f"Created plot with {len(plot_data)} data points", 
                                      {"variables": plot_vars, "data_points": len(plot_data)})

                # Display XAI dashboard
                if show_reasoning:
                    st.divider()
                    create_xai_dashboard(trail, result_stats)
                
                # Display plot
                if plot_data is not None:
                    st.divider()
                    st.subheader("📈 Data Visualization")
                    
                    fig = px.line(plot_data, x='value', y='pressure', color='variable',
                                 title="Oceanographic Profile Data",
                                 labels={'value': 'Measurement Value', 'pressure': 'Pressure (dbar)', 'variable': 'Parameter'})
                    fig.update_yaxis(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)

                # Store complete message with XAI trail
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "xai_trail": trail,
                    "result_stats": result_stats,
                    "plot_data": plot_data
                })
                st.session_state.xai_trails.append(trail)

# Footer with XAI information
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px'>
🔍 <strong>Explainable AI System</strong> | All decisions are transparent and traceable | 
Confidence scores indicate system certainty | Data lineage shows source selection process
</div>
""", unsafe_allow_html=True)
