# ClaimGuard

Agentic insurance claim triage assistant.

ClaimGuard runs a multi-step AI workflow for claim intake: retrieve policy clauses (RAG), run fraud heuristics, build a document checklist, then write a grounded triage recommendation with a full tool trace.

## Resume one-liner

ClaimGuard: multi-step AI agent for insurance claim triage with RAG policy retrieval, rule-based fraud checks, document checklist tools, and an auditable tool trace.

## What it does

1. Parse claim type and simple fields from free text
2. Tool `search_policy`: retrieve relevant policy chunks from ChromaDB
3. Tool `fraud_heuristic`: rule-based risk flags
4. Tool `checklist`: required vs provided documents
5. LLM writes a short recommendation: `approve_for_review`, `need_docs`, or `escalate`
6. UI shows every tool call for auditability

## Stack

- Python
- Streamlit
- ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`)
- OpenAI API or local Ollama
- Custom agent orchestration (fixed tool graph with observable calls)

## Setup

```bash
cd ClaimGuard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` with either `OPENAI_API_KEY` or a running Ollama model.

## Run

```bash
streamlit run app/streamlit_app.py
```

First run will download the embedding model. Click **Reindex knowledge base** once.

## Project layout

```text
knowledge_base/   policy and triage markdown
app/
  rag.py          ingest + retrieve
  tools.py        search_policy, fraud_heuristic, checklist
  agent.py        orchestration graph
  llm.py          final grounded summary
  streamlit_app.py
eval/             sample questions and expected decisions
```

## Interview talking points

- Not a single chatbot call: tools run first, then the LLM summarizes evidence
- Fraud checks are explicit rules (honest, inspectable), not a black-box fraud model
- Missing docs drive `need_docs`; high risk drives `escalate`
- Knowledge updates mean edit markdown and reindex (RAG), not fine-tune

## Eval

See `eval/test_cases.md` for 12 starter cases. Mark pass/fail by recommendation match.
