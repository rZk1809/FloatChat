"""
Enhanced logging utilities for the Agentic AI RAG Workflow System.
Provides XAI (Explainable AI) logging capabilities and structured logging.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import traceback

@dataclass
class XAILogEntry:
    """Structured log entry for explainable AI tracking."""
    timestamp: str
    session_id: str
    user_query: str
    workflow_stage: str
    action: str
    data_sources: List[str]
    reasoning: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class XAILogger:
    """Enhanced logger for explainable AI tracking."""
    
    def __init__(self, log_file: str = "xai_audit.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("XAI")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for XAI logs
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - XAI - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_workflow_start(self, session_id: str, user_query: str, metadata: Optional[Dict[str, Any]] = None):
        """Log the start of a workflow."""
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage="initialization",
            action="workflow_start",
            data_sources=[],
            reasoning="User initiated new query",
            metadata=metadata
        )
        self._write_entry(entry)
    
    def log_planning_decision(self, session_id: str, user_query: str, 
                            parsed_query: Dict[str, Any], execution_plan: List[Dict[str, Any]]):
        """Log planning decisions and reasoning."""
        reasoning = f"Parsed intent: {parsed_query.get('intent', 'unknown')}, " \
                   f"identified {len(parsed_query.get('regions', []))} regions, " \
                   f"generated {len(execution_plan)} execution steps"
        
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage="planning",
            action="plan_generation",
            data_sources=["query_parser", "execution_planner"],
            reasoning=reasoning,
            metadata={
                "parsed_query": parsed_query,
                "plan_steps": len(execution_plan)
            }
        )
        self._write_entry(entry)
    
    def log_data_access(self, session_id: str, user_query: str, 
                       data_source: str, action: str, result_summary: Dict[str, Any]):
        """Log data access operations."""
        reasoning = f"Accessed {data_source} for {action}, " \
                   f"retrieved {result_summary.get('count', 'unknown')} records"
        
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage="execution",
            action=f"data_access_{action}",
            data_sources=[data_source],
            reasoning=reasoning,
            metadata=result_summary
        )
        self._write_entry(entry)
    
    def log_analysis_step(self, session_id: str, user_query: str,
                         analysis_type: str, input_data: Dict[str, Any], 
                         results: Dict[str, Any]):
        """Log analysis operations."""
        reasoning = f"Performed {analysis_type} analysis on " \
                   f"{input_data.get('record_count', 'unknown')} records, " \
                   f"generated {len(results)} result metrics"
        
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage="execution",
            action=f"analysis_{analysis_type}",
            data_sources=["analyzer_tool"],
            reasoning=reasoning,
            metadata={
                "input_summary": input_data,
                "result_keys": list(results.keys())
            }
        )
        self._write_entry(entry)
    
    def log_synthesis_decision(self, session_id: str, user_query: str,
                             synthesis_approach: str, key_findings: List[str]):
        """Log synthesis decisions."""
        reasoning = f"Used {synthesis_approach} approach to synthesize response, " \
                   f"highlighted {len(key_findings)} key findings"
        
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage="synthesis",
            action="response_generation",
            data_sources=["synthesizer_agent", "ollama_llm"],
            reasoning=reasoning,
            metadata={
                "approach": synthesis_approach,
                "findings_count": len(key_findings)
            }
        )
        self._write_entry(entry)
    
    def log_error(self, session_id: str, user_query: str, 
                  stage: str, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log errors with context."""
        reasoning = f"Error in {stage}: {str(error)}"
        
        entry = XAILogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query,
            workflow_stage=stage,
            action="error",
            data_sources=[],
            reasoning=reasoning,
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context
            }
        )
        self._write_entry(entry)
    
    def _write_entry(self, entry: XAILogEntry):
        """Write XAI log entry to file."""
        try:
            log_data = asdict(entry)
            self.logger.info(json.dumps(log_data, default=str))
        except Exception as e:
            # Fallback logging
            self.logger.error(f"Failed to write XAI log entry: {e}")
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all logs for a specific session."""
        logs = []
        
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        if 'XAI' in line:
                            try:
                                # Extract JSON part
                                json_start = line.find('{')
                                if json_start != -1:
                                    log_data = json.loads(line[json_start:])
                                    if log_data.get('session_id') == session_id:
                                        logs.append(log_data)
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            self.logger.error(f"Failed to retrieve session logs: {e}")
        
        return logs

class StructuredLogger:
    """Enhanced structured logger for the workflow system."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.xai_logger = XAILogger()
    
    def log_with_context(self, level: str, message: str, 
                        session_id: Optional[str] = None,
                        stage: Optional[str] = None,
                        **kwargs):
        """Log with structured context."""
        context = {
            "session_id": session_id,
            "stage": stage,
            **kwargs
        }
        
        # Filter out None values
        context = {k: v for k, v in context.items() if v is not None}
        
        log_message = f"{message} | Context: {json.dumps(context, default=str)}"
        
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(log_message)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.log_with_context("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.log_with_context("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.log_with_context("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.log_with_context("debug", message, **kwargs)

# Global XAI logger instance
xai_logger = XAILogger()

def setup_logging(log_level: str = "INFO", log_file: str = "agentic_workflow.log"):
    """
    Initialize root logging for the application. Safe to call multiple times.
    Configures both console and file handlers and sets the desired log level.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()

    # Avoid duplicate handlers across Streamlit reruns by resetting handlers
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception:
        # Continue without file logging if it fails
        root_logger.warning("Failed to attach file handler for logging", exc_info=True)

    # Ensure XAI logger exists (it manages its own handler deduplication)
    _ = xai_logger


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
