"""
Synthesizer Agent for the Agentic AI RAG Workflow.
Responsible for generating final natural language responses from execution results.
"""

import logging
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from ..core.config import OLLAMA_CONFIG, SYSTEM_CONFIG

logger = logging.getLogger(__name__)

class SynthesizerAgent:
    """Agent responsible for synthesizing final responses from execution results."""
    
    def __init__(self):
        self.model = OLLAMA_CONFIG.general_model
        self.generate_url = OLLAMA_CONFIG.generate_url
    
    def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama API for text generation."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": SYSTEM_CONFIG.temperature,
                    "num_ctx": SYSTEM_CONFIG.max_context_length
                }
            }
            
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Failed to call Ollama: {e}")
            return ""
    
    def synthesize_response(self, 
                          user_query: str,
                          execution_context: Dict[str, Any],
                          include_technical_details: bool = False) -> Dict[str, Any]:
        """
        Generate a comprehensive natural language response from execution results.
        
        Args:
            user_query: Original user query
            execution_context: Results from executor agent
            include_technical_details: Whether to include technical execution details
            
        Returns:
            Dictionary with synthesized response and metadata
        """
        try:
            logger.info("Synthesizing final response")
            
            # Extract key information from execution context
            final_results = execution_context.get("final_results", {})
            execution_summary = self._create_execution_summary(execution_context)
            
            # Generate main response
            main_response = self._generate_main_response(user_query, final_results)
            
            # Generate technical summary if requested
            technical_summary = ""
            if include_technical_details:
                technical_summary = self._generate_technical_summary(execution_context)
            
            # Compile final response
            response = {
                "user_query": user_query,
                "main_response": main_response,
                "technical_summary": technical_summary,
                "execution_summary": execution_summary,
                "data_summary": self._create_data_summary(final_results),
                "visualizations": final_results.get("visualizations", []),
                "recommendations": self._generate_recommendations(final_results),
                "raw_data": self._extract_raw_data(execution_context),  # Add raw data for plotting
                "metadata": {
                    "timestamp": execution_context.get("timestamp"),
                    "total_steps": len(execution_context.get("steps", {})),
                    "successful_steps": sum(1 for step in execution_context.get("steps", {}).values()
                                          if step.get("success")),
                    "data_sources": ["ChromaDB", "PostgreSQL", "ARGO Float Database"]
                }
            }
            
            logger.info("Response synthesis completed")
            return response
            
        except Exception as e:
            logger.error(f"Failed to synthesize response: {e}")
            return {
                "user_query": user_query,
                "error": f"Failed to synthesize response: {str(e)}",
                "execution_context": execution_context
            }
    
    def _generate_main_response(self, user_query: str, final_results: Dict[str, Any]) -> str:
        """Generate the main natural language response."""
        try:
            system_prompt = """You are an expert oceanographer and data analyst. Generate a comprehensive, natural language response to the user's query based on the analysis results. 

Focus on:
1. Directly answering the user's question
2. Highlighting key findings and insights
3. Providing context and interpretation
4. Using clear, accessible language
5. Mentioning data sources and methodology briefly

Be concise but informative. Avoid technical jargon unless necessary."""
            
            # Prepare context information
            context_info = self._format_results_for_llm(final_results)
            
            prompt = f"""User Query: "{user_query}"

Analysis Results:
{context_info}

Generate a comprehensive response that directly answers the user's question based on these results. Include key findings, insights, and interpretations."""
            
            response = self._call_ollama(prompt, system_prompt)
            
            if not response:
                return self._generate_fallback_response(user_query, final_results)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate main response: {e}")
            return self._generate_fallback_response(user_query, final_results)
    
    def _generate_technical_summary(self, execution_context: Dict[str, Any]) -> str:
        """Generate technical summary of the execution process."""
        try:
            system_prompt = """You are a technical analyst. Provide a concise technical summary of the data analysis process, including methods used, data sources accessed, and any limitations or assumptions."""
            
            steps_info = []
            for step_key, step_data in execution_context.get("steps", {}).items():
                if step_data.get("success"):
                    steps_info.append(f"- {step_data.get('description', 'Unknown step')}")
                else:
                    steps_info.append(f"- {step_data.get('description', 'Unknown step')} (FAILED: {step_data.get('error', 'Unknown error')})")
            
            prompt = f"""Analysis Process:
{chr(10).join(steps_info)}

Data Sources: ChromaDB vector database, PostgreSQL database with ARGO float measurements

Generate a technical summary of this analysis process, including methods and any limitations."""
            
            response = self._call_ollama(prompt, system_prompt)
            return response if response else "Technical summary generation failed."
            
        except Exception as e:
            logger.error(f"Failed to generate technical summary: {e}")
            return f"Technical summary generation error: {str(e)}"
    
    def _format_results_for_llm(self, final_results: Dict[str, Any]) -> str:
        """Format results in a way that's useful for LLM processing."""
        formatted_parts = []
        
        # Summary information
        summary = final_results.get("summary", {})
        if summary:
            formatted_parts.append(f"Data Summary: {json.dumps(summary, indent=2)}")
        
        # Statistics
        statistics = final_results.get("statistics", {})
        if statistics:
            formatted_parts.append(f"Statistical Analysis: {json.dumps(statistics, indent=2, default=str)}")
        
        # Data information
        data = final_results.get("data", {})
        if data:
            data_info = []
            for key, value in data.items():
                if isinstance(value, dict) and "shape" in value:
                    data_info.append(f"{key}: {value['shape'][0]} rows, {value['shape'][1]} columns")
                elif isinstance(value, list):
                    data_info.append(f"{key}: {len(value)} items")
            if data_info:
                formatted_parts.append(f"Data: {'; '.join(data_info)}")
        
        # Visualizations
        visualizations = final_results.get("visualizations", [])
        if visualizations:
            viz_info = [f"{viz.get('description', 'Visualization')}" for viz in visualizations]
            formatted_parts.append(f"Visualizations: {'; '.join(viz_info)}")
        
        return "\n\n".join(formatted_parts) if formatted_parts else "No detailed results available."
    
    def _generate_fallback_response(self, user_query: str, final_results: Dict[str, Any]) -> str:
        """Generate a fallback response when LLM generation fails."""
        response_parts = [f"Analysis completed for query: '{user_query}'"]
        
        # Add summary information
        summary = final_results.get("summary", {})
        if "profiles_found" in summary:
            response_parts.append(f"Found {summary['profiles_found']} relevant ARGO profiles.")
        
        # Add statistics
        statistics = final_results.get("statistics", {})
        if "temperature" in statistics:
            temp_stats = statistics["temperature"]
            response_parts.append(f"Temperature range: {temp_stats.get('min', 'N/A')}°C to {temp_stats.get('max', 'N/A')}°C (mean: {temp_stats.get('mean', 'N/A')}°C)")
        
        if "salinity" in statistics:
            sal_stats = statistics["salinity"]
            response_parts.append(f"Salinity range: {sal_stats.get('min', 'N/A')} to {sal_stats.get('max', 'N/A')} (mean: {sal_stats.get('mean', 'N/A')})")
        
        # Add visualization info
        visualizations = final_results.get("visualizations", [])
        if visualizations:
            response_parts.append(f"Generated {len(visualizations)} visualization(s).")
        
        return " ".join(response_parts)
    
    def _create_execution_summary(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the execution process."""
        steps = execution_context.get("steps", {})
        
        return {
            "total_steps": len(steps),
            "successful_steps": sum(1 for step in steps.values() if step.get("success")),
            "failed_steps": sum(1 for step in steps.values() if not step.get("success")),
            "step_details": [
                {
                    "step": step_key,
                    "description": step_data.get("description"),
                    "success": step_data.get("success"),
                    "error": step_data.get("error") if not step_data.get("success") else None
                }
                for step_key, step_data in steps.items()
            ]
        }
    
    def _create_data_summary(self, final_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the data processed."""
        data_summary = {}
        
        # Profile information
        summary = final_results.get("summary", {})
        if "profiles_found" in summary:
            data_summary["profiles_analyzed"] = summary["profiles_found"]
        
        # Measurement information
        data = final_results.get("data", {})
        if "measurements" in data and isinstance(data["measurements"], dict):
            measurements_info = data["measurements"]
            if "shape" in measurements_info:
                data_summary["total_measurements"] = measurements_info["shape"][0]
                data_summary["measurement_variables"] = measurements_info.get("columns", [])
        
        return data_summary
    
    def _generate_recommendations(self, final_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the analysis results."""
        recommendations = []
        
        # Check data quality
        statistics = final_results.get("statistics", {})
        if statistics:
            if "temperature" in statistics and statistics["temperature"].get("std", 0) > 10:
                recommendations.append("High temperature variability detected - consider analyzing seasonal patterns")
            
            if "salinity" in statistics and statistics["salinity"].get("std", 0) > 2:
                recommendations.append("Significant salinity variations found - investigate water mass characteristics")
        
        # Check visualization availability
        visualizations = final_results.get("visualizations", [])
        if not visualizations:
            recommendations.append("Consider generating visualizations for better data interpretation")
        
        # General recommendations
        data_summary = final_results.get("summary", {})
        if data_summary.get("profiles_found", 0) < 5:
            recommendations.append("Limited data available - consider expanding search criteria or time range")
        
        return recommendations if recommendations else ["Analysis completed successfully - results are ready for interpretation"]

    def _extract_raw_data(self, execution_context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract raw data from execution context for plotting."""
        try:
            # Look for measurement data in step results
            steps = execution_context.get("steps", {})

            # Check step 2 (usually contains measurement data)
            step2_result = steps.get("step2", {}).get("result")
            if isinstance(step2_result, pd.DataFrame) and not step2_result.empty:
                return step2_result.to_dict('records')

            # Check other steps for data
            for step_key, step_data in steps.items():
                result = step_data.get("result")
                if isinstance(result, pd.DataFrame) and not result.empty:
                    return result.to_dict('records')

            return None

        except Exception as e:
            logger.error(f"Failed to extract raw data: {e}")
            return None
