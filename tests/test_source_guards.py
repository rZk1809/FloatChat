from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_source_has_no_destructive_database_or_collection_calls() -> None:
    python_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*ROOT.joinpath("agentic_workflow").rglob("*.py"), *ROOT.joinpath("scripts").rglob("*.py")]
    )
    assert "DROP TABLE" not in python_source.upper()
    assert "delete_collection" not in python_source
    assert "verify=False" not in python_source


def test_model_generated_sql_is_not_executed() -> None:
    source = (ROOT / "scripts" / "analysis" / "xai.py").read_text(encoding="utf-8")
    assert "pd.read_sql(text(sql_query)" not in source
    assert "legacy text-to-SQL interface is disabled" in source

