# --- Modified Code ---
import streamlit as st
import pandas as pd
import chromadb
import requests
import json
import os
from sqlalchemy import create_engine, text
import logging
from agentic_workflow.core.config import OLLAMA_CONFIG

# --- Configuration ---
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "argo_data")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "argo_profiles")
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "chroma_db")
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
OLLAMA_MODEL = OLLAMA_CONFIG.general_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Caching for Performance ---
@st.cache_resource
def get_db_engine():
    """Legacy direct database access is disabled."""
    return None

@st.cache_resource
def get_chroma_collection():
    """Legacy direct vector access is disabled."""
    return None

# --- Core RAG Functions ---
def find_relevant_profiles(query, collection, n_results=10):
    """
    Finds the most relevant profiles in ChromaDB based on a user query.
    Relies on Chroma's internal embedding function.
    """
    if collection is None:
        logging.warning("Chroma collection is None in find_relevant_profiles.")
        return pd.DataFrame()
    
    try:
        # Perform the query. Chroma handles the embedding of 'query' internally.
        results = collection.query(
            query_texts=[query], # Pass the raw text query
            n_results=n_results
        )
        
        # Check if results are valid
        if not results or not results.get('ids') or not results['ids'][0]:
            logging.info("No results found in ChromaDB for the query.")
            return pd.DataFrame()
            
        # Construct a DataFrame from the results
        df_data = {
            'profile_id': [int(id) for id in results['ids'][0]],
            'document': results['documents'][0] if results.get('documents') else [""] * len(results['ids'][0]),
            'distance': results['distances'][0] if results.get('distances') else [0.0] * len(results['ids'][0])
            # Metadatas are available if needed: results['metadatas'][0]
        }
        logging.info(f"Found {len(df_data['profile_id'])} relevant profiles.")
        return pd.DataFrame(df_data)
        
    except Exception as e:
        st.error(f"An error occurred during the ChromaDB query: {e}")
        logging.error(f"ChromaDB query error: {e}")
        return pd.DataFrame()


def generate_llm_response(query, context):
    """Sends the query and context to a local Ollama LLM and streams the response."""
    prompt = f"""
    You are an expert oceanographer's assistant.
    Answer the following question based ONLY on the context provided below.
    The context consists of several summaries of ARGO float profiles.
    Synthesize the information from all relevant summaries to form a coherent answer.
    If the context does not contain enough information to answer the question, you MUST state: 
    "I do not have enough information in the provided context to answer this question."
    Do not make up any information or answer from your own knowledge.

    CONTEXT:
    ---
    {context}
    ---

    QUESTION:
    {query}

    ANSWER:
    """
    
    try:
        payload = {
            "model": OLLAMA_MODEL, # Use the specified Ollama model
            "prompt": prompt,
            "stream": True
        }
        # Stream the response from Ollama
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                # Parse the JSON line
                json_line = json.loads(line)
                # Extract the 'response' part
                chunk = json_line.get("response", "")
                full_response += chunk
                # Yield the chunk for streaming display
                yield chunk

        # Optional: Log the full response after streaming is complete
        # logging.debug(f"Full LLM Response: {full_response}")

    except requests.exceptions.ConnectionError as e:
        error_message = f"Error connecting to Ollama: {e}. Is the Ollama server running and accessible at {OLLAMA_URL}?"
        st.error(error_message)
        logging.error(error_message)
        yield "" # Yield empty string on error
    except requests.exceptions.RequestException as e:
        error_message = f"Error requesting from Ollama: {e}."
        st.error(error_message)
        logging.error(error_message)
        yield ""
    except json.JSONDecodeError as e:
        error_message = f"Error decoding JSON response from Ollama: {e}. Response line: {line.decode('utf-8') if 'line' in locals() else 'N/A'}"
        st.error(error_message)
        logging.error(error_message)
        yield ""
    except Exception as e: # Catch any other unexpected errors
        error_message = f"An unexpected error occurred while calling Ollama: {e}"
        st.error(error_message)
        logging.error(error_message)
        yield ""


# --- Streamlit User Interface ---
st.set_page_config(layout="wide", page_title="OceanAI Explorer")

st.title("🌊 OceanAI Explorer (with Local LLM)")
st.markdown("Ask a question in natural language to query the ARGO float database.")
st.info("This legacy UI is offline. Run the canonical Python API and Next.js client.")

# Load resources (using cached functions)
engine = get_db_engine()
collection = get_chroma_collection()
# Note: The embedding model is no longer loaded or used directly for retrieval

# User input
user_query = st.text_input("Enter your question:", "Compare profiles in the Arabian Sea and the Bay of Bengal")

if st.button("Search"):
    if not user_query:
        st.warning("Please enter a question.")
    elif engine is None or collection is None:
        # Check if essential services are available
        st.error("Backend services (Database or Vector Store) are not available. Please check the logs and ensure they are running correctly.")
    else:
        # 1. Retrieval
        with st.spinner("Searching for relevant profiles using ChromaDB..."):
            relevant_profiles_df = find_relevant_profiles(user_query, collection)

        if relevant_profiles_df.empty:
            st.warning("No relevant profiles found for your query in the vector store.")
        else:
            st.success(f"Found {len(relevant_profiles_df)} relevant profiles to build context.")
            
            # 2. Context Assembly
            context = "\n---\n".join(relevant_profiles_df['document'])
            
            # 3. Generation
            st.subheader("AI Assistant's Answer:")
            with st.chat_message("assistant"):
                # Stream the response from the LLM
                st.write_stream(generate_llm_response(user_query, context))

            # 4. Show Sources
            with st.expander("Show sources used by the AI"):
                st.dataframe(relevant_profiles_df[['profile_id', 'document', 'distance']], use_container_width=True)
