from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings


SYSTEM_PROMPT = """
You are ClaimGuard, an insurance claim triage assistant.
You receive tool outputs (policy retrieval, fraud heuristics, document checklist).
Write a short triage answer for an operations analyst.

Rules:
- Use only the provided tool outputs and user message.
- State the recommendation clearly: approve_for_review, need_docs, or escalate.
- Cite policy source file names when you use retrieved text.
- If retrieval is empty, say knowledge was insufficient.
- Do not invent coverage amounts or legal advice.
- Keep the answer under 180 words.
""".strip()


def generate_triage(user_message: str, tool_bundle: dict[str, Any]) -> str:
    payload = {
        "user_message": user_message,
        "tool_bundle": tool_bundle,
    }
    user_content = (
        "Triage this claim using the tool bundle JSON.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=True)
    )

    url = settings.ollama_base_url.rstrip("/") + "/v1/chat/completions"
    body = {
        "model": settings.ollama_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
    return (data["choices"][0]["message"]["content"] or "").strip()
