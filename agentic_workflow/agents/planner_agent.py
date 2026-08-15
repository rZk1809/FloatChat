"""
Planner Agent for the Agentic AI RAG Workflow.
Responsible for understanding user queries and generating execution plans.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from ..core.config import OLLAMA_CONFIG, SYSTEM_CONFIG

logger = logging.getLogger(__name__)

class PlannerAgent:
    """Agent responsible for query understanding and plan generation."""

    def __init__(self):
        self.model = OLLAMA_CONFIG.general_model
        self.generate_url = OLLAMA_CONFIG.generate_url

        # Define available tools and their capabilities
        self.available_tools = {
            "retriever": {
                "description": "Search ChromaDB for relevant ARGO profiles using semantic similarity",
                "functions": ["retrieve_profiles", "retrieve_by_region", "retrieve_by_float_id"]
            },
            "sql_executor": {
                "description": "Execute SQL queries against PostgreSQL database for detailed measurements",
                "functions": ["get_profile_metadata", "get_measurements_by_profiles", "get_profiles_by_region_and_time"]
            },
            "analyzer": {
                "description": "Perform oceanographic analysis and calculations",
                "functions": ["calculate_profile_statistics", "calculate_average_profile", "compare_regions"]
            },
            "visualizer": {
                "description": "Create plots and visualizations",
                "functions": ["plot_temperature_salinity_diagram", "plot_profile_comparison", "plot_average_profile"]
            }
        }

        # Geographic regions
        self.known_regions = {
            "Bay of Bengal": {"lat_min": 5.0, "lat_max": 25.0, "lon_min": 80.0, "lon_max": 100.0},
            "Arabian Sea": {"lat_min": 5.0, "lat_max": 25.0, "lon_min": 60.0, "lon_max": 80.0},
            "Indian Ocean": {"lat_min": -60.0, "lat_max": 30.0, "lon_min": 20.0, "lon_max": 120.0},
            "Southern Ocean": {"lat_min": -80.0, "lat_max": -40.0, "lon_min": -180.0, "lon_max": 180.0}
        }

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

    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """
        Parse user query to extract key information.

        Args:
            user_query: Natural language query from user

        Returns:
            Dictionary with parsed query components
        """
        try:
            system_prompt = """You are an expert in oceanographic data analysis. Parse the user query and extract key information in JSON format.

Extract the following information:
- intent: The main goal (e.g., "analyze", "compare", "plot", "find")
- variables: Oceanographic variables mentioned (temperature, salinity, pressure, density)
- regions: Geographic regions mentioned
- time_period: Time constraints mentioned
- analysis_type: Type of analysis requested (statistics, profiles, trends, comparison)
- output_format: Desired output (plot, table, summary, visualization)

Return only valid JSON."""

            prompt = f"""Parse this oceanographic query and extract key information:

Query: "{user_query}"

Known regions: {list(self.known_regions.keys())}

Return JSON with extracted information:"""

            response = self._call_ollama(prompt, system_prompt)

            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed_info = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    parsed_info = self._fallback_parse(user_query)
            except json.JSONDecodeError:
                parsed_info = self._fallback_parse(user_query)

            # Enhance with additional parsing
            parsed_info = self._enhance_parsing(user_query, parsed_info)

            logger.info(
                "Parsed request (intent=%s, regions=%d, variables=%d)",
                parsed_info.get("intent", "unknown"),
                len(parsed_info.get("regions", [])),
                len(parsed_info.get("variables", [])),
            )
            return parsed_info

        except Exception as error:
            logger.error("Failed to parse request (%s)", type(error).__name__)
            return self._fallback_parse(user_query)

    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback parsing using simple keyword matching."""
        query_lower = query.lower()

        # Extract intent
        intent = "analyze"
        if any(word in query_lower for word in ["compare", "comparison"]):
            intent = "compare"
        elif any(word in query_lower for word in ["plot", "graph", "chart", "visualize"]):
            intent = "plot"
        elif any(word in query_lower for word in ["find", "search", "locate"]):
            intent = "find"

        # Extract variables
        variables = []
        if "temperature" in query_lower or "temp" in query_lower:
            variables.append("temperature")
        if "salinity" in query_lower or "salt" in query_lower:
            variables.append("salinity")
        if "pressure" in query_lower or "depth" in query_lower:
            variables.append("pressure")

        # Extract regions
        regions = []
        for region_name in self.known_regions.keys():
            if region_name.lower() in query_lower:
                regions.append(region_name)

        # Extract time period
        time_period = None
        if re.search(r'\b(january|jan)\b', query_lower):
            time_period = "January"
        if re.search(r'\b2024\b', query_lower):
            time_period = f"{time_period} 2024" if time_period else "2024"

        return {
            "intent": intent,
            "variables": variables,
            "regions": regions,
            "time_period": time_period,
            "analysis_type": "statistics",
            "output_format": "summary"
        }

    def _enhance_parsing(self, query: str, parsed_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance parsed information with additional details."""
        # Ensure required fields exist
        required_fields = ["intent", "variables", "regions", "time_period", "analysis_type", "output_format"]
        for field in required_fields:
            if field not in parsed_info:
                parsed_info[field] = None

        # Convert time period to date range if possible
        if parsed_info.get("time_period"):
            parsed_info["date_range"] = self._parse_time_period(parsed_info["time_period"])

        return parsed_info

    def _parse_time_period(self, time_period: str) -> Optional[Dict[str, str]]:
        """Parse time period into start and end dates."""
        if not time_period:
            return None

        time_lower = time_period.lower()

        # Handle "January 2024"
        if "january" in time_lower and "2024" in time_lower:
            return {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }

        # Handle just "2024"
        if "2024" in time_lower:
            return {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }

        return None

    def generate_execution_plan(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate step-by-step execution plan based on parsed query.

        Comparison queries (intent="compare" with 2+ regions) get independent
        retrieval + measurement steps per region, so compare_regions never
        receives the same DataFrame twice.

        Args:
            parsed_query: Parsed query information

        Returns:
            List of execution steps
        """
        try:
            plan = []
            regions = parsed_query.get("regions") or []
            is_comparison = parsed_query.get("intent") == "compare" and len(regions) >= 2

            if is_comparison:
                region_measurement_steps = []
                step_num = 0
                for region in regions[:2]:
                    bounds = self.known_regions[region]
                    date_range = parsed_query.get("date_range") or {}
                    step_num += 1
                    retrieve_step = step_num
                    plan.append({
                        "step": retrieve_step,
                        "tool": "sql_executor",
                        "function": "get_profiles_by_region_and_time",
                        "parameters": {
                            **bounds,
                            "start_date": date_range.get("start_date"),
                            "end_date": date_range.get("end_date"),
                        },
                        "description": f"Retrieve geographically bounded ARGO profiles from {region}"
                    })

                    step_num += 1
                    measure_step = step_num
                    plan.append({
                        "step": measure_step,
                        "tool": "sql_executor",
                        "function": "get_measurements_by_profiles",
                        "parameters": {"profile_ids": f"{{{{step{retrieve_step}_profile_ids}}}}"},
                        "description": f"Fetch detailed measurements for {region}"
                    })
                    region_measurement_steps.append(measure_step)

                step_num += 1
                plan.append({
                    "step": step_num,
                    "tool": "analyzer",
                    "function": "compare_regions",
                    "parameters": {
                        "region1_df": f"{{{{step{region_measurement_steps[0]}_measurements}}}}",
                        "region2_df": f"{{{{step{region_measurement_steps[1]}_measurements}}}}",
                        "region1_name": regions[0],
                        "region2_name": regions[1]
                    },
                    "description": f"Compare oceanographic properties between {regions[0]} and {regions[1]}"
                })

                primary_measurements_ref = f"{{{{step{region_measurement_steps[0]}_measurements}}}}"
            else:
                # Step 1: Retrieval
                if regions or parsed_query.get("time_period"):
                    plan.append({
                        "step": 1,
                        "tool": "retriever",
                        "function": "retrieve_by_region" if regions else "retrieve_profiles",
                        "parameters": self._build_retrieval_params(parsed_query),
                        "description": "Retrieve relevant ARGO profiles from vector database"
                    })
                else:
                    plan.append({
                        "step": 1,
                        "tool": "retriever",
                        "function": "retrieve_profiles",
                        "parameters": {"query": parsed_query.get("original_query", "ARGO profiles")},
                        "description": "Retrieve relevant ARGO profiles from vector database"
                    })

                # Step 2: Get detailed measurements
                plan.append({
                    "step": 2,
                    "tool": "sql_executor",
                    "function": "get_measurements_by_profiles",
                    "parameters": {"profile_ids": "{{step1_profile_ids}}"},
                    "description": "Fetch detailed measurements for retrieved profiles"
                })

                # Step 3: Analysis
                if "average" in str(parsed_query).lower() or "mean" in str(parsed_query).lower():
                    plan.append({
                        "step": 3,
                        "tool": "analyzer",
                        "function": "calculate_average_profile",
                        "parameters": {"df": "{{step2_measurements}}"},
                        "description": "Calculate average temperature and salinity profiles"
                    })
                else:
                    plan.append({
                        "step": 3,
                        "tool": "analyzer",
                        "function": "calculate_profile_statistics",
                        "parameters": {"df": "{{step2_measurements}}"},
                        "description": "Calculate statistical summary of profiles"
                    })

                primary_measurements_ref = "{{step2_measurements}}"

            # Visualization (if requested)
            if parsed_query.get("intent") == "plot" or parsed_query.get("output_format") == "plot":
                if "ts" in str(parsed_query).lower() or "temperature-salinity" in str(parsed_query).lower():
                    plot_function = "plot_temperature_salinity_diagram"
                elif "average" in str(parsed_query).lower():
                    plot_function = "plot_average_profile"
                else:
                    plot_function = "plot_profile_comparison"

                plan.append({
                    "step": len(plan) + 1,
                    "tool": "visualizer",
                    "function": plot_function,
                    "parameters": {"df": primary_measurements_ref, "title": "ARGO Data Analysis"},
                    "description": "Create visualization of the analysis results"
                })

            logger.info(f"Generated execution plan with {len(plan)} steps")
            return plan

        except Exception as e:
            logger.error(f"Failed to generate execution plan: {e}")
            return []

    def _build_retrieval_params(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Build parameters for a single-region (or region-less) retrieval step."""
        params = {}

        if parsed_query.get("regions"):
            params["region_name"] = parsed_query["regions"][0]

        if parsed_query.get("time_period"):
            params["time_filter"] = parsed_query["time_period"]

        if not params:
            params["query"] = "ARGO oceanographic profiles"

        return params
