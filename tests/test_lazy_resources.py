import chromadb
import sqlalchemy

from agentic_workflow.tools.retriever_tool import RetrieverTool
from agentic_workflow.tools.sql_executor_tool import SQLExecutorTool


def test_tool_construction_does_not_open_external_resources(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("external resource initialized eagerly")

    monkeypatch.setattr(chromadb, "PersistentClient", fail)
    monkeypatch.setattr(sqlalchemy, "create_engine", fail)

    retriever = RetrieverTool()
    sql_executor = SQLExecutorTool()

    assert retriever.collection is None
    assert sql_executor.engine is None

