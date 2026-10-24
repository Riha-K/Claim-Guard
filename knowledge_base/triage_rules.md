# Triage Rules for ClaimGuard

## Allowed recommendations
- approve_for_review: documents look complete and risk is low or medium
- need_docs: required documents are missing
- escalate: strong fraud signals or injury / high amount cases

## Process
1. Identify claim type from the user message
2. Search policy knowledge for relevant clauses
3. Run fraud heuristics on structured fields when present
4. Build document checklist for the claim type
5. Produce a final recommendation with short reasons
6. Keep an audit trail of every tool call

## Honesty rule
If policy text is missing from retrieval, say so. Do not invent coverage limits.
