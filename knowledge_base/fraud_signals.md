# Fraud Signal Reference

## High risk signals
- Same policy number with multiple claims in a short window
- Claim amount much higher than typical for the claim type
- Missing police report for third-party auto claims
- Inconsistent dates between event and hospitalization

## Medium risk signals
- Incomplete document set
- First claim filed very soon after policy start
- Repeated repair shop name across unrelated claims (demo heuristic)

## Response guidance
- High risk: escalate to human investigator
- Medium risk: request documents and continue review
- Low risk: continue normal triage with policy retrieval
