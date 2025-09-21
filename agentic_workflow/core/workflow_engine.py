"""
Workflow Engine for the Agentic AI RAG System.
Orchestrates the interaction between planner, executor, and synthesizer agents.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.synthesizer_agent import SynthesizerAgent
from agents.plotting_agent import PlottingAgent
from core.config import config

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Main workflow engine that orchestrates the agentic AI system."""
    
    def __init__(self):
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.synthesizer = SynthesizerAgent()
        self.plotting_agent = PlottingAgent()

        # Workflow state
        self.current_session = None
        self.workflow_history = []

        # Validate system connections
        self._validate_system()
    
    def _validate_system(self):
        """Validate that all required services are available."""
        try:
            logger.info("Validating system connections...")
            connections = config.validate_connections()
            
            failed_services = [service for service, status in connections.items() if not status]
            
            if failed_services:
                logger.warning(f"Some services are not available: {failed_services}")
                logger.warning("The system may have limited functionality")
            else:
                logger.info("All services are available and ready")
                
        except Exception as e:
            logger.error(f"System validation failed: {e}")
    
    def process_query(self, 
                     user_query: str,
                     session_id: Optional[str] = None,
                     include_technical_details: bool = False,
                     enable_xai_logging: bool = None) -> Dict[str, Any]:
        """
        Process a user query through the complete agentic workflow.
        
        Args:
            user_query: Natural language query from the user
            session_id: Optional session identifier for tracking
            include_technical_details: Whether to include technical execution details
            enable_xai_logging: Override XAI logging setting
            
        Returns:
            Complete response with analysis results and explanations
        """
        workflow_start_time = datetime.now()
        
        try:
            logger.info(f"Processing query: '{user_query[:100]}...' (Session: {session_id})")
            
            # Initialize workflow session
            workflow_session = {
                "session_id": session_id or f"session_{int(workflow_start_time.timestamp())}",
                "user_query": user_query,
                "start_time": workflow_start_time,
                "stages": {},
                "errors": []
            }
            
            self.current_session = workflow_session
            
            # Stage 1: Planning
            logger.info("Stage 1: Query Planning")
            planning_result = self._execute_planning_stage(user_query, workflow_session)
            
            if not planning_result.get("success"):
                return self._handle_workflow_error("Planning stage failed", workflow_session, planning_result.get("error"))
            
            # Stage 2: Execution
            logger.info("Stage 2: Plan Execution")
            execution_result = self._execute_execution_stage(planning_result["execution_plan"], workflow_session)
            
            if not execution_result.get("success"):
                return self._handle_workflow_error("Execution stage failed", workflow_session, execution_result.get("error"))
            
            # Stage 3: Synthesis
            logger.info("Stage 3: Response Synthesis")
            synthesis_result = self._execute_synthesis_stage(
                user_query,
                execution_result["execution_context"],
                workflow_session,
                include_technical_details
            )

            if not synthesis_result.get("success"):
                return self._handle_workflow_error("Synthesis stage failed", workflow_session, synthesis_result.get("error"))

            # Stage 4: Plotting (if applicable)
            logger.info("Stage 4: Visualization Generation")
            plotting_result = self._execute_plotting_stage(
                user_query,
                synthesis_result["response"],
                workflow_session
            )

            # Plotting is optional, so we don't fail the workflow if it fails
            if plotting_result.get("success") and plotting_result.get("plots"):
                synthesis_result["response"]["plots"] = plotting_result["plots"]
                logger.info(f"Generated {len(plotting_result['plots'])} visualizations")
            else:
                logger.info("No visualizations generated")

            # Finalize workflow
            workflow_session["end_time"] = datetime.now()
            workflow_session["duration"] = (workflow_session["end_time"] - workflow_session["start_time"]).total_seconds()
            workflow_session["success"] = True
            
            # Add workflow metadata to response
            final_response = synthesis_result["response"]
            final_response["workflow_metadata"] = {
                "session_id": workflow_session["session_id"],
                "duration_seconds": workflow_session["duration"],
                "stages_completed": len(workflow_session["stages"]),
                "timestamp": workflow_start_time.isoformat()
            }

            # Format response for Streamlit compatibility
            streamlit_response = {
                "summary": final_response.get("main_response", ""),
                "data_summary": final_response.get("data_summary", {}),
                "recommendations": final_response.get("recommendations", []),
                "raw_data": final_response.get("raw_data"),
                "plots": final_response.get("plots", []),
                "metadata": final_response.get("metadata", {}),
                "workflow_metadata": final_response.get("workflow_metadata", {})
            }

            return streamlit_response
            
            # Store in history
            self.workflow_history.append(workflow_session)
            
            # XAI Logging
            if enable_xai_logging or (enable_xai_logging is None and config.system.enable_xai_logging):
                self._log_xai_information(workflow_session, final_response)
            
            logger.info(f"Workflow completed successfully in {workflow_session['duration']:.2f} seconds")
            return streamlit_response
            
        except Exception as e:
            logger.error(f"Workflow processing failed: {e}")
            logger.error(traceback.format_exc())
            return self._handle_workflow_error("Workflow processing failed", workflow_session, str(e))
    
    def _execute_planning_stage(self, user_query: str, workflow_session: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planning stage."""
        try:
            stage_start = datetime.now()
            
            # Parse the query
            parsed_query = self.planner.parse_query(user_query)
            parsed_query["original_query"] = user_query
            
            # Generate execution plan
            execution_plan = self.planner.generate_execution_plan(parsed_query)
            
            stage_result = {
                "success": True,
                "parsed_query": parsed_query,
                "execution_plan": execution_plan,
                "duration": (datetime.now() - stage_start).total_seconds()
            }
            
            workflow_session["stages"]["planning"] = stage_result
            logger.info(f"Planning completed: {len(execution_plan)} steps generated")
            
            return stage_result
            
        except Exception as e:
            error_msg = f"Planning stage error: {str(e)}"
            logger.error(error_msg)
            workflow_session["errors"].append(error_msg)
            return {"success": False, "error": error_msg}
    
    def _execute_execution_stage(self, execution_plan: list, workflow_session: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the execution stage."""
        try:
            stage_start = datetime.now()
            
            # Execute the plan
            execution_context = self.executor.execute_plan(execution_plan)
            execution_context["timestamp"] = stage_start.isoformat()
            
            stage_result = {
                "success": True,
                "execution_context": execution_context,
                "duration": (datetime.now() - stage_start).total_seconds()
            }
            
            workflow_session["stages"]["execution"] = stage_result
            
            # Check if execution was successful
            execution_summary = self.executor.get_execution_summary()
            successful_steps = execution_summary.get("successful_steps", 0)
            total_steps = execution_summary.get("total_steps", 0)
            
            logger.info(f"Execution completed: {successful_steps}/{total_steps} steps successful")
            
            if successful_steps == 0:
                return {"success": False, "error": "No steps executed successfully"}
            
            return stage_result
            
        except Exception as e:
            error_msg = f"Execution stage error: {str(e)}"
            logger.error(error_msg)
            workflow_session["errors"].append(error_msg)
            return {"success": False, "error": error_msg}
    
    def _execute_synthesis_stage(self, 
                               user_query: str, 
                               execution_context: Dict[str, Any], 
                               workflow_session: Dict[str, Any],
                               include_technical_details: bool) -> Dict[str, Any]:
        """Execute the synthesis stage."""
        try:
            stage_start = datetime.now()
            
            # Synthesize the response
            response = self.synthesizer.synthesize_response(
                user_query, 
                execution_context, 
                include_technical_details
            )
            
            stage_result = {
                "success": True,
                "response": response,
                "duration": (datetime.now() - stage_start).total_seconds()
            }
            
            workflow_session["stages"]["synthesis"] = stage_result
            logger.info("Synthesis completed successfully")
            
            return stage_result
            
        except Exception as e:
            error_msg = f"Synthesis stage error: {str(e)}"
            logger.error(error_msg)
            workflow_session["errors"].append(error_msg)
            return {"success": False, "error": error_msg}
    
    def _handle_workflow_error(self, 
                             error_message: str, 
                             workflow_session: Dict[str, Any], 
                             detailed_error: str = None) -> Dict[str, Any]:
        """Handle workflow errors and return error response."""
        workflow_session["success"] = False
        workflow_session["end_time"] = datetime.now()
        workflow_session["error"] = error_message
        
        if detailed_error:
            workflow_session["detailed_error"] = detailed_error
        
        # Store failed session in history
        self.workflow_history.append(workflow_session)
        
        return {
            "error": error_message,
            "detailed_error": detailed_error,
            "user_query": workflow_session.get("user_query"),
            "session_id": workflow_session.get("session_id"),
            "workflow_metadata": {
                "success": False,
                "error_stage": self._get_last_completed_stage(workflow_session),
                "duration_seconds": (workflow_session["end_time"] - workflow_session["start_time"]).total_seconds()
            }
        }
    
    def _get_last_completed_stage(self, workflow_session: Dict[str, Any]) -> str:
        """Get the name of the last completed stage."""
        stages = workflow_session.get("stages", {})
        if "synthesis" in stages:
            return "synthesis"
        elif "execution" in stages:
            return "execution"
        elif "planning" in stages:
            return "planning"
        else:
            return "initialization"
    
    def _log_xai_information(self, workflow_session: Dict[str, Any], final_response: Dict[str, Any]):
        """Log explainable AI information for transparency."""
        try:
            xai_log = {
                "session_id": workflow_session["session_id"],
                "timestamp": datetime.now().isoformat(),
                "user_query": workflow_session["user_query"],
                "workflow_stages": list(workflow_session["stages"].keys()),
                "execution_summary": {
                    "total_duration": workflow_session.get("duration", 0),
                    "stages_completed": len(workflow_session["stages"]),
                    "success": workflow_session.get("success", False)
                },
                "data_sources_used": final_response.get("metadata", {}).get("data_sources", []),
                "analysis_methods": self._extract_analysis_methods(workflow_session),
                "key_findings": self._extract_key_findings(final_response)
            }
            
            # Log to file (in production, this might go to a specialized XAI system)
            logger.info(f"XAI Log: {xai_log}")
            
        except Exception as e:
            logger.error(f"XAI logging failed: {e}")
    
    def _extract_analysis_methods(self, workflow_session: Dict[str, Any]) -> list:
        """Extract analysis methods used during execution."""
        methods = []
        
        execution_stage = workflow_session.get("stages", {}).get("execution", {})
        execution_context = execution_stage.get("execution_context", {})
        
        for step_key, step_data in execution_context.get("steps", {}).items():
            if step_data.get("success"):
                description = step_data.get("description", "")
                if description:
                    methods.append(description)
        
        return methods
    
    def _extract_key_findings(self, final_response: Dict[str, Any]) -> list:
        """Extract key findings from the final response."""
        findings = []
        
        # Extract from data summary
        data_summary = final_response.get("data_summary", {})
        if "profiles_analyzed" in data_summary:
            findings.append(f"Analyzed {data_summary['profiles_analyzed']} ARGO profiles")
        
        # Extract from recommendations
        recommendations = final_response.get("recommendations", [])
        findings.extend(recommendations[:3])  # Top 3 recommendations
        
        return findings

    def _execute_plotting_stage(self, user_query: str, synthesis_response: Dict[str, Any], workflow_session: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plotting stage to generate visualizations."""
        stage_start_time = datetime.now()

        try:
            logger.info("Starting plotting stage")

            # Generate plots using the plotting agent
            plots = self.plotting_agent.generate_plots(user_query, synthesis_response)

            # Record stage completion
            stage_duration = (datetime.now() - stage_start_time).total_seconds()
            workflow_session["stages"]["plotting"] = {
                "start_time": stage_start_time,
                "end_time": datetime.now(),
                "duration": stage_duration,
                "success": True,
                "plots_generated": len(plots)
            }

            logger.info(f"Plotting stage completed in {stage_duration:.2f} seconds")

            return {
                "success": True,
                "plots": plots,
                "stage_duration": stage_duration
            }

        except Exception as e:
            logger.error(f"Plotting stage failed: {e}")
            logger.error(traceback.format_exc())

            # Record stage failure
            stage_duration = (datetime.now() - stage_start_time).total_seconds()
            workflow_session["stages"]["plotting"] = {
                "start_time": stage_start_time,
                "end_time": datetime.now(),
                "duration": stage_duration,
                "success": False,
                "error": str(e)
            }

            return {
                "success": False,
                "error": str(e),
                "stage_duration": stage_duration
            }

    def get_workflow_history(self, limit: int = 10) -> list:
        """Get recent workflow history."""
        return self.workflow_history[-limit:] if self.workflow_history else []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        connections = config.validate_connections()
        
        return {
            "system_ready": all(connections.values()),
            "service_status": connections,
            "recent_workflows": len(self.workflow_history),
            "current_session": self.current_session["session_id"] if self.current_session else None
        }
