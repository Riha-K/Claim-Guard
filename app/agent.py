from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm import generate_triage
from app.rag import PolicyStore
from app.tools import ToolTrace, run_tool_suite


@dataclass
class AgentResult:
    recommendation: str
    answer: str
    fields: dict[str, Any]
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    tool_bundle: dict[str, Any] = field(default_factory=dict)


class ClaimGuardAgent:
    """
    Agentic triage pipeline (tool-calling orchestration):

      parse fields -> search_policy -> fraud_heuristic -> checklist
                   -> LLM summary grounded on tool outputs

    This is intentionally a fixed graph with observable tool calls so you can
    explain planning, tools, and audit traces in interviews.
    """

    def __init__(self) -> None:
        self.store = PolicyStore()

    def ready(self) -> dict:
        return self.store.ensure()

    def reindex(self) -> dict:
        return self.store.ingest(clear=True)

    def run(self, message: str) -> AgentResult:
        cleaned = (message or "").strip()
        if not cleaned:
            raise ValueError("message is empty")

        self.ready()
        trace = ToolTrace()
        bundle = run_tool_suite(self.store, cleaned, trace)
        answer = generate_triage(cleaned, bundle)

        return AgentResult(
            recommendation=bundle["recommendation"],
            answer=answer,
            fields=bundle["fields"],
            tool_bundle=bundle,
            tool_trace=[
                {"name": c.name, "input": c.input, "output": c.output} for c in trace.calls
            ],
        )
