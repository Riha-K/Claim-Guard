from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import ClaimGuardAgent
from app.config import settings

st.set_page_config(page_title="ClaimGuard", page_icon="CG", layout="wide")
st.title("ClaimGuard")
st.caption("Agentic insurance claim triage assistant")


@st.cache_resource
def get_agent() -> ClaimGuardAgent:
    return ClaimGuardAgent()


agent = get_agent()

with st.sidebar:
    st.header("Setup")
    st.write(f"LLM: {'OpenAI ' + settings.openai_model if settings.use_openai else 'Ollama ' + settings.ollama_model}")
    st.write(f"Embeddings: {settings.embedding_model}")
    if st.button("Reindex knowledge base"):
        with st.spinner("Indexing..."):
            info = agent.reindex()
        st.success(f"Indexed {info.get('chunks')} chunks from {info.get('files')} files")
    if st.button("Ensure index"):
        info = agent.ready()
        st.info(json.dumps(info))

    st.markdown("### Example prompts")
    st.code(
        "Auto claim: third party collision, amount INR 180000, "
        "docs claim_form driving_license vehicle_rc damage_photos repair_estimate police_report",
        language="text",
    )
    st.code(
        "Health claim hospitalization amount INR 600000, "
        "docs claim_form only, 5 days after policy start",
        language="text",
    )

message = st.text_area("Claim description", height=140)
run = st.button("Run triage", type="primary")

if run:
    try:
        with st.spinner("Running agent tools..."):
            result = agent.run(message)
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.subheader("Recommendation")
            st.metric("Decision", result.recommendation)
            st.subheader("Agent answer")
            st.write(result.answer)
            st.subheader("Parsed fields")
            st.json(result.fields)
        with col2:
            st.subheader("Tool trace (audit)")
            for i, call in enumerate(result.tool_trace, start=1):
                with st.expander(f"{i}. {call['name']}", expanded=(i == 1)):
                    st.markdown("**Input**")
                    st.json(call["input"])
                    st.markdown("**Output**")
                    st.json(call["output"])
    except Exception as exc:
        st.error(str(exc))
