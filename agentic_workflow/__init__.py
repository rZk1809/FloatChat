"""
Agentic AI RAG Workflow System for ARGO Float Data Analysis.

A comprehensive system for intelligent analysis of oceanographic data from ARGO floats
using retrieval-augmented generation and multi-agent workflows.
"""

__version__ = "1.0.0"
__description__ = "Intelligent ARGO Float Data Analysis System"

__all__ = ["WorkflowEngine", "config"]


def __getattr__(name: str):
    """Load public objects lazily so importing the package has no service effects."""
    if name == "WorkflowEngine":
        from .core.workflow_engine import WorkflowEngine

        return WorkflowEngine
    if name == "config":
        from .core.config import config

        return config
    raise AttributeError(name)
