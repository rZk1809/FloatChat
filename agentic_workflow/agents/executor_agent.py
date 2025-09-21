"""
Executor Agent for the Agentic AI RAG Workflow.
Responsible for executing the planned steps using available tools.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from tools.retriever_tool import RetrieverTool
from tools.sql_executor_tool import SQLExecutorTool
from tools.analyzer_tool import AnalyzerTool
from tools.visualizer_tool import VisualizerTool
from core.config import SYSTEM_CONFIG

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """Agent responsible for executing planned steps using available tools."""
    
    def __init__(self):
        # Initialize tools
        self.retriever = RetrieverTool()
        self.sql_executor = SQLExecutorTool()
        self.analyzer = AnalyzerTool()
        self.visualizer = VisualizerTool()
        
        # Execution context to store intermediate results
        self.context = {}
    
    def execute_plan(self, execution_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    
    def _execute_step(self, step: Dict[str, Any]) -> Any:
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
        
        # Get the function
        if not hasattr(tool, function_name):
            raise ValueError(f"Tool {tool_name} does not have function {function_name}")
        
        function = getattr(tool, function_name)
        
        # Execute the function
        logger.debug(f"Calling {tool_name}.{function_name} with params: {resolved_params}")
        result = function(**resolved_params)
        
        return result
    
    def _get_tool(self, tool_name: str):
        """Get tool instance by name."""
        tool_map = {
            "retriever": self.retriever,
            "sql_executor": self.sql_executor,
            "analyzer": self.analyzer,
            "visualizer": self.visualizer
        }
        return tool_map.get(tool_name)
    
    def _resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
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
        """Get value from execution context."""
        # Handle common reference patterns
        if ref_key == "step1_profile_ids":
            # Extract profile IDs from step 1 retrieval results
            step1_result = self.context.get("steps", {}).get("step1", {}).get("result")
            if step1_result and "profiles" in step1_result:
                return [profile["id"] for profile in step1_result["profiles"]]
            return []
        
        elif ref_key == "step2_measurements":
            # Get measurements DataFrame from step 2
            step2_result = self.context.get("steps", {}).get("step2", {}).get("result")
            if isinstance(step2_result, pd.DataFrame):
                return step2_result
            return pd.DataFrame()
        
        elif ref_key.startswith("region") and ref_key.endswith("_measurements"):
            # Handle region-specific measurements for comparison
            # This would need more sophisticated logic based on the specific use case
            step2_result = self.context.get("steps", {}).get("step2", {}).get("result")
            if isinstance(step2_result, pd.DataFrame):
                return step2_result  # Simplified - would need region filtering
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
    
    def _store_step_results(self, step_num: int, step: Dict[str, Any], result: Any):
        """Store important results for use in later steps."""
        tool_name = step.get("tool")
        function_name = step.get("function")
        
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
    
    def get_execution_summary(self) -> Dict[str, Any]:
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
