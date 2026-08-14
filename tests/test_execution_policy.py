from typing import Any

import pandas as pd
import pytest

from agentic_workflow.agents.executor_agent import ExecutorAgent
from agentic_workflow.agents.planner_agent import PlannerAgent


class FakeRetriever:
    def retrieve_profiles(self, **kwargs: Any) -> dict[str, Any]:
        return {"profiles": []}

    def hidden_method(self) -> None:
        raise AssertionError("must never be called")


def test_executor_rejects_non_allowlisted_method() -> None:
    executor = object.__new__(ExecutorAgent)
    executor.retriever = FakeRetriever()
    executor.sql_executor = object()
    executor.analyzer = object()
    executor.visualizer = object()
    executor.context = {"steps": {}, "final_results": {}}

    with pytest.raises(ValueError, match="not allowed"):
        executor._execute_step(
            {"tool": "retriever", "function": "hidden_method", "parameters": {}}
        )


def test_comparison_plan_uses_two_geographic_sql_queries() -> None:
    planner = PlannerAgent()
    plan = planner.generate_execution_plan(
        {
            "intent": "compare",
            "regions": ["Arabian Sea", "Bay of Bengal"],
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
        }
    )

    region_steps = [step for step in plan if step["function"] == "get_profiles_by_region_and_time"]
    assert len(region_steps) == 2
    assert region_steps[0]["parameters"]["lon_max"] == 80.0
    assert region_steps[1]["parameters"]["lon_min"] == 80.0
    assert region_steps[0]["parameters"] is not region_steps[1]["parameters"]


def test_dataframe_profile_references_are_resolved_independently() -> None:
    executor = object.__new__(ExecutorAgent)
    executor.context = {
        "steps": {
            "step1": {"result": pd.DataFrame({"wmo_id": [1], "cycle_number": [2]})},
            "step3": {"result": pd.DataFrame({"wmo_id": [3], "cycle_number": [4]})},
        }
    }

    assert executor._get_context_value("step1_profile_ids") == ["1_2"]
    assert executor._get_context_value("step3_profile_ids") == ["3_4"]

