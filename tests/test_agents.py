"""
Unit tests for the FloatChat agent components.

Ollama HTTP calls are mocked so tests run without a local Ollama server.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# PlannerAgent tests
# ---------------------------------------------------------------------------

class TestPlannerAgentInit:
    """PlannerAgent can be instantiated without a live Ollama connection."""

    def test_init_sets_known_regions(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        assert "Bay of Bengal" in planner.known_regions
        assert "Arabian Sea" in planner.known_regions
        assert "Indian Ocean" in planner.known_regions
        assert "Southern Ocean" in planner.known_regions

    def test_init_sets_available_tools(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        assert "retriever" in planner.available_tools
        assert "sql_executor" in planner.available_tools
        assert "analyzer" in planner.available_tools
        assert "visualizer" in planner.available_tools


class TestPlannerAgentFallbackParse:
    """_fallback_parse works without any LLM call."""

    def test_detects_bay_of_bengal(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        result = planner._fallback_parse("Show temperature in Bay of Bengal")
        assert "Bay of Bengal" in result.get("regions", [])

    def test_detects_arabian_sea(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        result = planner._fallback_parse("Salinity profile Arabian Sea")
        assert "Arabian Sea" in result.get("regions", [])

    def test_detects_temperature_variable(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        result = planner._fallback_parse("What is the temperature at 200m?")
        assert "temperature" in result.get("variables", [])

    def test_detects_salinity_variable(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        result = planner._fallback_parse("Plot salinity depth profile")
        assert "salinity" in result.get("variables", [])

    def test_detects_plot_intent(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        result = planner._fallback_parse("Plot the T-S diagram")
        assert result.get("intent") in ("plot", "visualize", "analyze", "find")


class TestPlannerAgentParseQueryWithMock:
    """parse_query falls back gracefully when Ollama returns bad JSON."""

    def test_parse_query_with_invalid_llm_response(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        with patch.object(planner, "_call_ollama", return_value="not json at all"):
            result = planner.parse_query("Temperature in Bay of Bengal")
        assert isinstance(result, dict)

    def test_parse_query_with_valid_llm_json(self):
        from agentic_workflow.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        mock_response = json.dumps({
            "intent": "analyze",
            "variables": ["temperature"],
            "regions": ["Bay of Bengal"],
            "time_period": None,
            "analysis_type": "statistics",
            "output_format": "summary",
        })
        with patch.object(planner, "_call_ollama", return_value=mock_response):
            result = planner.parse_query("Temperature in Bay of Bengal")
        assert result.get("intent") == "analyze"
        assert "temperature" in result.get("variables", [])


# ---------------------------------------------------------------------------
# SynthesizerAgent tests
# ---------------------------------------------------------------------------

class TestSynthesizerAgentInit:
    def test_init_without_error(self):
        from agentic_workflow.agents.synthesizer_agent import SynthesizerAgent
        agent = SynthesizerAgent()
        assert agent is not None


class TestSynthesizerAgentSummarize:
    """synthesize / generate_response returns a string even when Ollama is absent."""

    def test_returns_string_on_ollama_failure(self):
        from agentic_workflow.agents.synthesizer_agent import SynthesizerAgent
        agent = SynthesizerAgent()
        with patch.object(agent, "_call_ollama", return_value=""):
            query_info = {"intent": "analyze", "variables": ["temperature"], "regions": ["Bay of Bengal"]}
            analysis = {"statistics": {"mean_temp": 28.4, "profiles": 10}}
            result = agent.synthesize(query_info=query_info, analysis_results=analysis, retrieved_data=[])
        assert isinstance(result, str)

    def test_returns_string_with_mock_response(self):
        from agentic_workflow.agents.synthesizer_agent import SynthesizerAgent
        agent = SynthesizerAgent()
        with patch.object(agent, "_call_ollama", return_value="The temperature is 28°C."):
            query_info = {"intent": "analyze", "variables": ["temperature"], "regions": []}
            result = agent.synthesize(query_info=query_info, analysis_results={}, retrieved_data=[])
        assert "temperature" in result.lower() or isinstance(result, str)
