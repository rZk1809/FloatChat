"""
Executor Agent for the Agentic AI RAG Workflow.
Responsible for executing the planned steps using available tools.
"""

import logging
import re
from typing import Any

import pandas as pd

from ..tools.analyzer_tool import AnalyzerTool
from ..tools.retriever_tool import RetrieverTool
from ..tools.sql_executor_tool import SQLExecutorTool

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """Agent responsible for executing planned steps using available tools."""

    ALLOWED_FUNCTIONS = {
        "retriever": {
            "retrieve_profiles",
            "retrieve_by_region",
            "retrieve_by_float_id",
        },
        "sql_executor": {
            "get_profile_metadata",
            "get_measurements_by_profiles",
            "get_profiles_by_region_and_time",
        },
        "analyzer": {
            "calculate_profile_statistics",
            "calculate_average_profile",
            "compare_regions",
        },
        "visualizer": {
            "plot_temperature_salinity_diagram",
            "plot_profile_comparison",
            "plot_average_profile",
        },
    }

    def __init__(self):
        # Initialize tools
        self.retriever = RetrieverTool()
        self.sql_executor = SQLExecutorTool()
        self.analyzer = AnalyzerTool()
        # Plotting has a much heavier optional dependency stack. Keep it out of
        # the service import path and initialize it only for a visualization
        # step.
        self.visualizer = None

        # Execution context to store intermediate results
        self.context = {}

    def execute_plan(self, execution_plan: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Execute the complete execution plan step by step.

        Args:
            execution_plan: List of execution steps from planner

        Returns:
            Dictionary with execution results and context
        """
        try:
            logger.info(f"Starting execution of {len(execution_plan)} steps")

            # Clear previous context
            self.context = {"steps": {}, "final_results": {}}

            for step in execution_plan:
                step_num = step.get("step", 0)
                logger.info(f"Executing step {step_num}: {step.get('description', 'Unknown step')}")

                try:
                    result = self._execute_step(step)
                    self.context["steps"][f"step{step_num}"] = {
                        "description": step.get("description"),
                        "result": result,
                        "success": True
                    }

                    # Store key results for later steps
                    self._store_step_results(step_num, step, result)

                except Exception as e:
                    logger.error(f"Step {step_num} failed: {e}")
                    self.context["steps"][f"step{step_num}"] = {
                        "description": step.get("description"),
                        "error": str(e),
                        "success": False
                    }
                    # Continue with remaining steps if possible

            # Compile final results
            self._compile_final_results()

            logger.info("Execution plan completed")
            return self.context

        except Exception as e:
            logger.error(f"Failed to execute plan: {e}")
            return {"error": str(e), "context": self.context}

    def _execute_step(self, step: dict[str, Any]) -> Any:
        """Execute a single step."""
        tool_name = step.get("tool")
        function_name = step.get("function")
        parameters = step.get("parameters", {})

        # Resolve parameter references
        resolved_params = self._resolve_parameters(parameters)

        # Get the appropriate tool
        tool = self._get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        allowed = self.ALLOWED_FUNCTIONS.get(tool_name, set())
        if function_name not in allowed:
            raise ValueError(f"Function is not allowed for tool {tool_name}")

        function = getattr(tool, function_name)

        # Execute the function
        logger.debug("Calling %s.%s", tool_name, function_name)
        result = function(**resolved_params)

        return result

    def _get_tool(self, tool_name: str):
        """Get tool instance by name."""
        if tool_name == "visualizer" and self.visualizer is None:
            from ..tools.visualizer_tool import VisualizerTool

            self.visualizer = VisualizerTool()

        tool_map = {
            "retriever": self.retriever,
            "sql_executor": self.sql_executor,
            "analyzer": self.analyzer,
            "visualizer": self.visualizer
        }
        return tool_map.get(tool_name)

    def _resolve_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Resolve parameter references to actual values from context."""
        resolved = {}

        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # This is a reference to a previous step result
                ref_key = value[2:-2]  # Remove {{ and }}
                resolved_value = self._get_context_value(ref_key)
                resolved[key] = resolved_value
            else:
                resolved[key] = value

        return resolved

    def _get_context_value(self, ref_key: str) -> Any:
        """Get value from execution context.

        Reference keys are of the form `step<N>_profile_ids` or
        `step<N>_measurements`, so any step number can be referenced -
        needed for comparison plans that retrieve two regions independently
        (e.g. step2_measurements and step4_measurements), not just a single
        hardcoded step1/step2 pair.
        """
        profile_ids_match = re.match(r'^step(\d+)_profile_ids$', ref_key)
        if profile_ids_match:
            step_key = f"step{profile_ids_match.group(1)}"
            step_result = self.context.get("steps", {}).get(step_key, {}).get("result")
            if isinstance(step_result, dict) and "profiles" in step_result:
                return [profile["id"] for profile in step_result["profiles"]]
            if isinstance(step_result, pd.DataFrame) and {
                "wmo_id",
                "cycle_number",
            }.issubset(step_result.columns):
                return [
                    f"{int(row.wmo_id)}_{int(row.cycle_number)}"
                    for row in step_result[["wmo_id", "cycle_number"]].itertuples(
                        index=False
                    )
                ]
            return []

        measurements_match = re.match(r'^step(\d+)_measurements$', ref_key)
        if measurements_match:
            step_key = f"step{measurements_match.group(1)}"
            step_result = self.context.get("steps", {}).get(step_key, {}).get("result")
            if isinstance(step_result, pd.DataFrame):
                return step_result
            return pd.DataFrame()

        # Try to get direct reference
        parts = ref_key.split("_")
        if len(parts) >= 2 and parts[0].startswith("step"):
            step_key = parts[0]
            result_key = "_".join(parts[1:])

            step_result = self.context.get("steps", {}).get(step_key, {}).get("result")
            if isinstance(step_result, dict) and result_key in step_result:
                return step_result[result_key]

        logger.warning(f"Could not resolve context reference: {ref_key}")
        return None

    def _store_step_results(self, step_num: int, step: dict[str, Any], result: Any):
        """Store important results for use in later steps."""
        tool_name = step.get("tool")
        # Store retrieval results
        if tool_name == "retriever" and isinstance(result, dict) and "profiles" in result:
            self.context[f"step{step_num}_profiles"] = result["profiles"]
            self.context[f"step{step_num}_profile_ids"] = [p["id"] for p in result["profiles"]]

        # Store measurement data
        elif tool_name == "sql_executor" and isinstance(result, pd.DataFrame):
            self.context[f"step{step_num}_measurements"] = result

        # Store analysis results
        elif tool_name == "analyzer":
            self.context[f"step{step_num}_analysis"] = result

        # Store visualization results
        elif tool_name == "visualizer":
            self.context[f"step{step_num}_visualization"] = result

    def _compile_final_results(self):
        """Compile final results from all executed steps."""
        final_results = {
            "summary": {},
            "data": {},
            "visualizations": [],
            "statistics": {}
        }

        # Collect results from each step
        for step_key, step_data in self.context.get("steps", {}).items():
            if not step_data.get("success"):
                continue

            result = step_data.get("result")

            # Handle different types of results
            if isinstance(result, dict):
                if "profiles" in result:  # Retrieval results
                    final_results["summary"]["profiles_found"] = result.get("n_results", 0)
                    final_results["data"]["retrieved_profiles"] = result["profiles"]

                elif any(key in result for key in ["temperature", "salinity", "profile_count"]):  # Analysis results
                    final_results["statistics"].update(result)

                elif "regions" in result:  # Comparison results
                    final_results["statistics"]["comparison"] = result

            elif isinstance(result, pd.DataFrame):  # Measurement data
                final_results["data"]["measurements"] = {
                    "shape": result.shape,
                    "columns": result.columns.tolist(),
                    "sample": result.head().to_dict() if not result.empty else {}
                }

            elif isinstance(result, str) and result:  # Visualization (base64 or path)
                final_results["visualizations"].append({
                    "step": step_key,
                    "description": step_data.get("description"),
                    "result": result
                })

        self.context["final_results"] = final_results

    def get_execution_summary(self) -> dict[str, Any]:
        """Get a summary of the execution results."""
        if not self.context:
            return {"error": "No execution context available"}

        summary = {
            "total_steps": len(self.context.get("steps", {})),
            "successful_steps": sum(1 for step in self.context.get("steps", {}).values() if step.get("success")),
            "failed_steps": sum(1 for step in self.context.get("steps", {}).values() if not step.get("success")),
            "final_results": self.context.get("final_results", {}),
            "execution_details": []
        }

        # Add execution details
        for step_key, step_data in self.context.get("steps", {}).items():
            detail = {
                "step": step_key,
                "description": step_data.get("description"),
                "success": step_data.get("success"),
                "error": step_data.get("error") if not step_data.get("success") else None
            }
            summary["execution_details"].append(detail)

        return summary
