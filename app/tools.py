from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.rag import PolicyStore


@dataclass
class ToolResult:
    name: str
    input: dict[str, Any]
    output: dict[str, Any]


@dataclass
class ToolTrace:
    calls: list[ToolResult] = field(default_factory=list)

    def add(self, name: str, raw_input: dict[str, Any], output: dict[str, Any]) -> None:
        self.calls.append(ToolResult(name=name, input=raw_input, output=output))


CHECKLISTS = {
    "auto_collision": [
        "claim_form",
        "driving_license",
        "vehicle_rc",
        "damage_photos",
        "repair_estimate",
    ],
    "health_hospitalization": [
        "claim_form",
        "discharge_summary",
        "hospital_bills",
        "investigation_reports",
        "insured_kyc",
    ],
}


def search_policy(store: PolicyStore, query: str, top_k: int = 4) -> dict[str, Any]:
    chunks = store.search(query, top_k=top_k)
    return {
        "hits": [
            {
                "source": c.source,
                "score": round(c.score, 4),
                "text": c.text[:500],
            }
            for c in chunks
        ]
    }


def fraud_heuristic(
    claim_type: str,
    amount: float | None = None,
    days_since_policy_start: int | None = None,
    prior_claims_30d: int | None = None,
    third_party: bool | None = None,
    has_police_report: bool | None = None,
) -> dict[str, Any]:
    flags: list[str] = []
    risk = "low"

    if prior_claims_30d is not None and prior_claims_30d >= 2:
        flags.append("multiple_claims_in_30_days")
        risk = "high"

    if days_since_policy_start is not None and days_since_policy_start < 15:
        flags.append("claim_soon_after_policy_start")
        risk = "high" if risk == "high" else "medium"

    if claim_type == "auto_collision" and amount is not None and amount >= 250000:
        flags.append("high_auto_claim_amount")
        risk = "high"

    if claim_type == "health_hospitalization" and amount is not None and amount >= 500000:
        flags.append("high_health_claim_amount")
        risk = "high"

    if claim_type == "auto_collision" and third_party and has_police_report is False:
        flags.append("missing_police_report_for_third_party")
        risk = "high" if risk == "high" else "medium"

    if not flags:
        flags.append("no_rule_based_fraud_signal")

    return {"risk": risk, "flags": flags}


def checklist(
    claim_type: str,
    provided_docs: list[str] | None = None,
    third_party: bool | None = None,
) -> dict[str, Any]:
    required = list(CHECKLISTS.get(claim_type, ["claim_form"]))
    if claim_type == "auto_collision" and third_party:
        if "police_report" not in required:
            required.append("police_report")
    provided = [d.strip().lower() for d in (provided_docs or []) if d.strip()]
    missing = [d for d in required if d not in provided]
    return {
        "claim_type": claim_type,
        "required": required,
        "provided": provided,
        "missing": missing,
        "complete": len(missing) == 0,
    }


def parse_claim_fields(message: str) -> dict[str, Any]:
    """Lightweight field extraction from free text for demos."""
    lower = message.lower()
    claim_type = "auto_collision"
    if any(w in lower for w in ("hospital", "health", "discharge", "surgery")):
        claim_type = "health_hospitalization"

    amount = None
    m = re.search(r"(?:rs\.?|inr|amount)\s*[:\-]?\s*([0-9][0-9,]*)", lower)
    if m:
        amount = float(m.group(1).replace(",", ""))

    days = None
    m = re.search(r"([0-9]+)\s*days?\s*(?:after|since)\s*policy", lower)
    if m:
        days = int(m.group(1))

    prior = None
    m = re.search(r"([0-9]+)\s*(?:prior|previous|other)\s*claims?", lower)
    if m:
        prior = int(m.group(1))

    third_party = None
    if "third party" in lower or "third-party" in lower:
        third_party = True
    if "single vehicle" in lower or "no third party" in lower:
        third_party = False

    has_police = None
    if "police report" in lower or "fir" in lower:
        has_police = "no police" not in lower and "without police" not in lower

    docs: list[str] = []
    for token in (
        "claim_form",
        "driving_license",
        "vehicle_rc",
        "damage_photos",
        "repair_estimate",
        "police_report",
        "discharge_summary",
        "hospital_bills",
        "investigation_reports",
        "insured_kyc",
    ):
        if token.replace("_", " ") in lower or token in lower:
            docs.append(token)

    return {
        "claim_type": claim_type,
        "amount": amount,
        "days_since_policy_start": days,
        "prior_claims_30d": prior,
        "third_party": third_party,
        "has_police_report": has_police,
        "provided_docs": docs,
    }


def run_tool_suite(store: PolicyStore, message: str, trace: ToolTrace) -> dict[str, Any]:
    fields = parse_claim_fields(message)
    claim_type = fields["claim_type"]

    policy = search_policy(store, message)
    trace.add("search_policy", {"query": message}, policy)

    fraud = fraud_heuristic(
        claim_type=claim_type,
        amount=fields.get("amount"),
        days_since_policy_start=fields.get("days_since_policy_start"),
        prior_claims_30d=fields.get("prior_claims_30d"),
        third_party=fields.get("third_party"),
        has_police_report=fields.get("has_police_report"),
    )
    trace.add("fraud_heuristic", {k: fields.get(k) for k in fields}, fraud)

    docs = checklist(
        claim_type=claim_type,
        provided_docs=fields.get("provided_docs"),
        third_party=fields.get("third_party"),
    )
    trace.add("checklist", {"claim_type": claim_type, "provided_docs": fields.get("provided_docs")}, docs)

    if fraud["risk"] == "high":
        recommendation = "escalate"
    elif not docs["complete"]:
        recommendation = "need_docs"
    else:
        recommendation = "approve_for_review"

    return {
        "fields": fields,
        "recommendation": recommendation,
        "policy": policy,
        "fraud": fraud,
        "checklist": docs,
    }


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True)
