"""
Agentic AI RAG Workflow System for ARGO Float Data Analysis.

A comprehensive system for intelligent analysis of oceanographic data from ARGO floats
using retrieval-augmented generation and multi-agent workflows.
"""

__version__ = "1.0.0"
__author__ = "Agentic AI Team"
__description__ = "Intelligent ARGO Float Data Analysis System"

from .core.workflow_engine import WorkflowEngine
from .core.config import config

# Main exports
__all__ = [
    "WorkflowEngine",
    "config"
]
