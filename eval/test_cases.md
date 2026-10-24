# ClaimGuard eval cases

Mark pass if the recommendation matches Expected.

| ID | Prompt summary | Expected |
| --- | --- | --- |
| 1 | Auto third party, complete docs including police report, amount 80000, no prior claims | approve_for_review |
| 2 | Auto third party, missing police report, amount 90000 | need_docs or escalate |
| 3 | Auto, amount 300000, 2 prior claims in 30 days | escalate |
| 4 | Health hospitalization, only claim_form provided | need_docs |
| 5 | Health hospitalization, full docs, amount 120000, policy age 200 days | approve_for_review |
| 6 | Health, amount 650000, full docs | escalate |
| 7 | Auto single vehicle, complete docs without police report | approve_for_review |
| 8 | Claim 3 days after policy start, amount 150000 | escalate or need_docs |
| 9 | Vague message with no docs listed | need_docs |
| 10 | Asks coverage for drunk driving accident | need_docs or escalate (policy says not covered; still triage) |
| 11 | Health missing discharge_summary and bills | need_docs |
| 12 | Auto complete docs, amount 50000, quiet history | approve_for_review |

## How to score

1. Paste each prompt into the Streamlit app
2. Record recommendation + tools called
3. Pass if Expected matches (allow escalate when fraud flags are clearly high)
