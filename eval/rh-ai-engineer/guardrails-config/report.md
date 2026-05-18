# A/B Evaluation Report: rh-ai-engineer-guardrails-config

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/55
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9444 | 0.3333 |
| Median Reward | 1.0000 | 0.5000 |
| Std Reward | 0.0962 | 0.2887 |

## Comparison

- **Mean reward gap (Uplift):** +0.6111
- **Welch's t-test p-value:** 0.0551
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T20:51:50.118193Z
- Commit SHA: `5ae29fd156022b76b7453146c32b0b003e832938`
- Pipeline run: `abevalflow-swlp7`
