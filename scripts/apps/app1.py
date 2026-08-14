# chatbot_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import chromadb
from sqlalchemy import create_engine, text
import requests
import json
import logging
from datetime import datetime
import re
import os
from agentic_workflow.core.config import OLLAMA_CONFIG

# --- Configuration ---
# PostgreSQL Credentials (for fetching detailed data if needed for plots)
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASSWORD = os.environ.get("PGPASSWORD", "")
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "argo_data")
# ChromaDB Configuration
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "chroma_db")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "argo_profiles_ollama")
# Ollama Configuration
OLLAMA_CHAT_MODEL = OLLAMA_CONFIG.general_model
OLLAMA_EMBED_MODEL = OLLAMA_CONFIG.embedding_model
_OLLAMA_BASE_URL = OLLAMA_CONFIG.base_url
OLLAMA_URL = f"{_OLLAMA_BASE_URL}/api/generate"  # For chat/generate
OLLAMA_EMBED_URL = f"{_OLLAMA_BASE_URL}/api/embeddings"  # For embeddings

# Configure logging (Streamlit handles this, but good practice)
logging.basicConfig(level=logging.INFO)

# --- Helper Functions ---

@st.cache_resource
def get_db_engine():
    """Legacy direct database access is disabled."""
    return None

@st.cache_resource
def get_chroma_collection():
    """Legacy direct vector access is disabled."""
    return None

def get_embedding_from_ollama(text):
    """Gets an embedding for a text query from Ollama."""
    try:
        payload = {"model": OLLAMA_EMBED_MODEL, "prompt": text}
        response = requests.post(OLLAMA_EMBED_URL, json=payload)
        response.raise_for_status()
        return response.json().get("embedding")
    except Exception as e:
        logging.warning(f"Failed to get embedding from Ollama: {e}")
        return None

def find_relevant_profiles(query_text, collection, n_results=5):
    """Finds relevant profiles in ChromaDB based on a text query."""
    if collection is None:
        return []
    try:
        # Option 1: Use Chroma's internal embedding (simpler)
        # results = collection.query(query_texts=[query_text], n_results=n_results)

        # Option 2: Use Ollama embedding (potentially more consistent if used during ingestion)
        # Requires the embedding model used for ingestion
        query_embedding = get_embedding_from_ollama(query_text)
        if not query_embedding:
            return []
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

        if not results or not results['ids'][0]:
            return []

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        return formatted_results
    except Exception as e:
        st.error(f"Error querying ChromaDB: {e}")
        logging.error(f"ChromaDB query error: {e}")
        return []

def format_context_for_llm(relevant_profiles):
    """Formats the retrieved profiles into a context string for the LLM."""
    if not relevant_profiles:
        return "No relevant profiles were found in the database for the query."
    context_parts = []
    for profile in relevant_profiles:
        doc = profile.get('document', 'No summary available.')
        meta = profile.get('metadata', {})
        # Add metadata for better understanding by the LLM
        meta_str = f" (Profile ID: {meta.get('profile_id', 'N/A')}, WMO ID: {meta.get('wmo_id', 'N/A')})"
        context_parts.append(doc + meta_str)
    return "\n---\n".join(context_parts)

def ask_ollama(question, context, conversation_history):
    """
    Sends the question, context, and history to Ollama and streams the response.
    Includes logic to detect plot commands within the LLM's response.

    Args:
        question (str): The user's current question.
        context (str): The retrieved context from the knowledge base (ChromaDB).
        conversation_history (str): The string representation of the prior conversation.

    Yields:
        str: Chunks of the LLM's response text.
        dict: A final message containing the full response and any detected plot command.
              Format: {"full_response": "...", "plot_info": {...} or None}
    """
    # --- Enhanced Prompt Construction ---
    # Providing a clear system role and structure can help the LLM perform better.
    system_prompt = f"""
    <|im_start|>system
    You are OceanBot, an expert oceanographer and data analyst assistant.
    
    **Your Primary Role:**
    - Answer user questions about ARGO float data for the Indian Ocean.
    - Your knowledge is strictly limited to the provided "Context (ARGO Profiles)".
    - Prioritize information from the context over general knowledge.
    - If the context lacks sufficient information, clearly state: "I cannot answer that question based on the provided context."
    - Do not speculate or make up information.
    - Your responses will be part of a data-driven application, so accuracy is paramount.
    
    **Data Interpretation:**
    - Profile summaries include WMO ID, Cycle Number, Date, and Location.
    - Use these details to reason about regions, time series, and spatial distribution.
    
    **Plotting Capability (IMPORTANT):**
    - You can instruct the application to generate plots.
    - To do this, embed a specific command within your answer using the following format:
      [PLOT_REQUEST: action="ACTION_NAME", parameters="key1=value1,key2=value2,..."]
    - Available actions:
      - `temp_vs_pressure`: Plots temperature against pressure for a single profile.
        - Requires parameter: `profile_id` (e.g., "1902194_207")
      - `ts_diagram`: Plots a Temperature-Salinity diagram for a set of measurements (future implementation detail).
        - Might require parameters like a list of profile IDs or a region filter (implementation pending).
    - Example for plotting: "The profile shows interesting stratification. [PLOT_REQUEST: action=\"temp_vs_pressure\", parameters=\"profile_id=1902194_207\"] This plot visualizes the temperature change with depth."
    - Place the command logically within your response where the plot is relevant.
    - Ensure the `profile_id` used matches exactly with the IDs provided in the context.
    <|im_end|>
    """

    user_prompt = f"""
    <|im_start|>user
    My question is: {question}
    <|im_end|>
    <|im_start|>assistant
    """
    
    # The full prompt combines system instructions, history, context, and the user's question.
    # Note: The conversation history should already include 'User: ...' and 'Assistant: ...' prefixes.
    full_prompt = f"{system_prompt}\n{conversation_history}\nContext (ARGO Profiles):\n{context}\n{user_prompt}"

    # --- Logging the prompt (useful for debugging, but be careful with sensitive data) ---
    # logging.debug(f"Sending prompt to Ollama:\n{full_prompt}")

    try:
        payload = {
            "model": OLLAMA_CHAT_MODEL,
            "prompt": full_prompt,
            "stream": True,
            # Optional: Adjust parameters for the model's generation
            # "temperature": 0.7, # Controls randomness
            # "top_p": 0.9,
            # "repeat_penalty": 1.1
        }
        
        logging.info(f"Sending request to Ollama model '{OLLAMA_CHAT_MODEL}' at {OLLAMA_URL}")
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300) # 5-minute timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        full_response_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line)
                    # Extract the text chunk generated by the model
                    chunk = json_line.get("response", "")
                    full_response_text += chunk
                    # Yield the chunk for streaming display in the UI
                    yield chunk
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON line from Ollama response: {e}")
                    yield f"[Error: Could not process part of the response]"

        # --- Post-Processing: Extract Plot Command ---
        # After the full response is received, check for the plot command marker.
        plot_info = extract_plot_info(full_response_text)

        # --- Yield the final message ---
        # Send a final signal containing the complete text and plot info.
        # This allows the calling function to handle the full response and any actions.
        yield {
            "full_response": full_response_text,
            "plot_info": plot_info
        }
        logging.info("Received complete response from Ollama.")

    except requests.exceptions.ConnectionError as e:
        error_message = f"I'm sorry, I couldn't reach the Ollama server to generate a response. Please make sure Ollama is running and the model '{OLLAMA_CHAT_MODEL}' is available. Error details: {e}"
        logging.error(f"Ollama Connection Error: {e}")
        yield {"full_response": error_message, "plot_info": None}

    except requests.exceptions.Timeout as e:
        error_message = f"The request to Ollama timed out. The model might be taking too long to respond. Please try again later. Error details: {e}"
        logging.error(f"Ollama Timeout Error: {e}")
        yield {"full_response": error_message, "plot_info": None}

    except requests.exceptions.RequestException as e:
        # Catches other HTTP-related errors (e.g., 404, 500)
        error_message = f"An error occurred while communicating with Ollama: {e}"
        logging.error(f"Ollama Request Error: {e}")
        yield {"full_response": error_message, "plot_info": None}

    except Exception as e:
        # Catches any other unexpected errors
        error_message = f"An unexpected error occurred while generating the response: {e}"
        logging.error(f"Unexpected Error in ask_ollama: {e}", exc_info=True) # exc_info logs the full traceback
        yield {"full_response": error_message, "plot_info": None}


def extract_plot_info(response_text):
    """
    A simple heuristic to detect if the LLM wants to plot.
    Looks for a specific marker or keyword in the response.
    The LLM should be instructed to output something like:
    [PLOT_REQUEST: action="plot_type", parameters="param1=value1,param2=value2"]
    """
    # This regex looks for the marker [PLOT_REQUEST: ...]
    # It's made slightly more robust to handle spaces.
    plot_marker_pattern = r"\[PLOT_REQUEST:\s*action\s*=\s*\"([^\"]+)\"(?:\s*,\s*parameters\s*=\s*\"([^\"]*)\")?\s*\]"
    match = re.search(plot_marker_pattern, response_text)
    if match:
        action = match.group(1).strip()
        parameters_str = match.group(2).strip() if match.group(2) else ""
        # Parse parameters string like "type=temp_vs_pressure,id=1902194_207"
        params = {}
        if parameters_str:
            for param in parameters_str.split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key.strip()] = value.strip()
        logging.info(f"Plot command detected: action='{action}', parameters={params}")
        return {"action": action, "parameters": params}
    return None

def execute_plot_action(plot_info, engine):
    """Executes the plotting action based on extracted info."""
    action = plot_info.get("action")
    params = plot_info.get("parameters", {})
    
    if action == "temp_vs_pressure":
        profile_id = params.get("profile_id") or params.get("id")
        if not profile_id:
            st.error("Plot action 'temp_vs_pressure' requires a 'profile_id' or 'id' parameter.")
            return

        try:
            # Query PostgreSQL for detailed measurement data
            sql = text("""
                SELECT m.pressure, m.temp
                FROM measurements m
                JOIN profiles p ON m.profile_id = p.id
                WHERE p.id = :profile_id OR p.id::text = :profile_id
                ORDER BY m.pressure ASC
            """)
            df = pd.read_sql(sql, engine, params={"profile_id": profile_id})
            
            if df.empty:
                 # Try with the string profile_id format (e.g., '1902194_207')
                 sql_alt = text("""
                    SELECT m.pressure, m.temp
                    FROM measurements m
                    JOIN profiles pr ON m.profile_id = pr.id
                    JOIN floats f ON pr.float_id = f.id
                    WHERE CONCAT(f.wmo_id, '_', pr.cycle_number) = :profile_id
                    ORDER BY m.pressure ASC
                 """)
                 df = pd.read_sql(sql_alt, engine, params={"profile_id": profile_id})

            if df.empty:
                st.warning(f"No measurement data found for profile ID '{profile_id}'.")
                return

            # Drop rows with NaN in pressure or temp
            df.dropna(subset=['pressure', 'temp'], inplace=True)
            if df.empty:
                st.warning(f"No valid pressure/temperature data found for profile ID '{profile_id}'.")
                return

            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(df['temp'], df['pressure'], marker='o', linestyle='-', color='b')
            ax.set_xlabel('Temperature (°C)')
            ax.set_ylabel('Pressure (dbar)')
            ax.set_title(f'Temperature vs Pressure - Profile {profile_id}')
            ax.invert_yaxis() # Pressure increases downwards
            ax.grid(True, linestyle='--', alpha=0.5)
            
            st.pyplot(fig)
            plt.close(fig) # Important to prevent memory leaks in Streamlit

        except Exception as e:
            st.error(f"Error generating plot: {e}")
            logging.error(f"Plot generation error: {e}")

    elif action == "map_profiles":
        # Example: Plot profiles from a list of IDs or based on a filter
        # This is a placeholder. You'd need to define how the LLM specifies which profiles.
        # For now, let's plot the profiles found in the last context.
        st.info("Map plot action triggered (implementation details for filtering needed).")
        # A full implementation would require getting profile locations (lat/lon)
        # from the database based on IDs or other criteria provided by the LLM.
        # This is more complex and would need careful LLM instruction.
        # For demonstration, we'll skip detailed implementation here.
        st.warning("Map plotting logic needs more specific parameters from the LLM.")
        
    else:
        st.warning(f"Unknown plot action requested: {action}")


# --- Streamlit App ---

st.set_page_config(page_title="OceanBot - ARGO RAG Chat", layout="wide")
st.title("🤖 OceanBot: ARGO Data Chat Assistant")
st.markdown("Ask questions about ARGO float data. I can retrieve information and generate plots!")
st.info("This legacy UI is offline. Run the canonical Python API and Next.js client.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ""

# Load resources
engine = get_db_engine()
collection = get_chroma_collection()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "plot_info" in message:
            # If the message contains plot info, display the plot
            if engine:
                execute_plot_action(message["plot_info"], engine)
            else:
                st.error("Cannot display plot: Database connection failed.")
        else:
            st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question about ARGO data..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to conversation history string
    st.session_state.conversation_history += f"User: {prompt}\n"

    # Get response from the RAG system
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 1. Retrieve relevant profiles
            relevant_profiles = find_relevant_profiles(prompt, collection, n_results=5)
            
            # 2. Format context
            context = format_context_for_llm(relevant_profiles)
            
            # 3. Generate response with Ollama
            response_placeholder = st.empty()
            response_text = ""
            plot_info = None
            
            response_stream = ask_ollama(prompt, context, st.session_state.conversation_history)
            for chunk in response_stream:
                # Check if the final chunk contains the full response
                if isinstance(chunk, dict) and "full_response" in chunk:
                    response_text = chunk["full_response"]
                    # 4. Check for plot command in the full response
                    plot_info = extract_plot_info(response_text)
                    break
                else:
                    # Stream the response
                    response_text += chunk
                    response_placeholder.markdown(response_text + "▌")
            
            # Clear the streaming placeholder and show final text
            response_placeholder.markdown(response_text)
            
            # 5. If a plot command was found, execute it
            if plot_info:
                st.subheader("📊 Generated Plot:")
                if engine:
                    execute_plot_action(plot_info, engine)
                else:
                    st.error("Cannot generate plot: Database connection failed.")
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "plot_info": plot_info # Store plot info for potential re-display
            })
            
            # Add assistant response to conversation history
            st.session_state.conversation_history += f"Assistant: {response_text}\n"
            if plot_info:
                st.session_state.conversation_history += f"[Plot generated: {plot_info}]\n"

# Sidebar for information
with st.sidebar:
    st.header("About OceanBot")
    st.write("This chatbot uses Retrieval Augmented Generation (RAG) to answer questions about ARGO float data.")
    st.write("**Data Source:**")
    st.write("- ChromaDB (`argo_profiles_ollama`)")
    st.write("- PostgreSQL (`argo_data`)")
    st.write("**LLM:** Exact local model configured by the canonical API")
    st.write("**Capabilities:**")
    st.write("- Natural language Q&A")
    st.write("- Context-aware responses")
    st.write("- Plot generation (e.g., T-S diagrams)")
    st.write("**Instructions for Plotting:**")
    st.write("Ask the bot to plot data. It might respond with a command like:")
    st.code('[PLOT_REQUEST: action="temp_vs_pressure", parameters="profile_id=1902194_207"]')
    st.write("If you see this, the plot should appear automatically.")
