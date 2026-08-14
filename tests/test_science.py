import numpy as np
import pandas as pd
import pytest

from agentic_workflow.tools.analyzer_tool import AnalyzerTool


def test_teos10_density_requires_coordinates() -> None:
    analyzer = AnalyzerTool()
    with pytest.raises(ValueError, match="longitude and latitude"):
        analyzer.calculate_potential_density(
            np.array([10.0]), np.array([35.0]), np.array([0.0])
        )


def test_teos10_density_matches_reference_value() -> None:
    analyzer = AnalyzerTool()
    density = analyzer.calculate_potential_density(
        np.array([10.0]),
        np.array([35.0]),
        np.array([0.0]),
        longitude=np.array([80.0]),
        latitude=np.array([10.0]),
    )

    assert density[0] == pytest.approx(1026.95, abs=0.08)


def _region_frame(offset: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "wmo_id": [1, 1, 2, 2],
            "cycle_number": [1, 1, 1, 1],
            "pressure": [10.0, 100.0, 10.0, 100.0],
            "temp": np.array([20.0, 10.0, 22.0, 12.0]) + offset,
            "psal": np.array([35.0, 35.2, 34.8, 35.1]) + offset / 10,
        }
    )


def test_region_comparison_rejects_aliasing() -> None:
    analyzer = AnalyzerTool()
    frame = _region_frame(0.0)

    result = analyzer.compare_regions(frame, frame)

    assert "independent datasets" in result["error"]


def test_region_comparison_uses_profile_level_samples() -> None:
    analyzer = AnalyzerTool()

    result = analyzer.compare_regions(
        _region_frame(0.0), _region_frame(2.0), "Arabian Sea", "Bay of Bengal"
    )

    assert result["differences"]["temperature"]["mean_diff"] == pytest.approx(-2.0)
    assert "vertically averaged" in result["limitations"][0]


def test_hierarchical_region_comparison_is_flagged() -> None:
    analyzer = AnalyzerTool()
    result = analyzer.compare_regions(
        _region_frame(0.0), _region_frame(1.0), "Indian Ocean", "Bay of Bengal"
    )
    assert "overlap hierarchically" in result["warning"]

