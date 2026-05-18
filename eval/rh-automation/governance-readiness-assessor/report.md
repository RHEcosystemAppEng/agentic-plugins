# A/B Evaluation Report: rh-automation-governance-readiness-assessor

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/67
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8571 | 0.1905 |
| Median Reward | 0.8571 | 0.1429 |
| Std Reward | 0.0000 | 0.0824 |

## Comparison

- **Mean reward gap (Uplift):** +0.6666
- **Welch's t-test p-value:** 0.0051
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-16T21:16:37.624312Z
- Commit SHA: `2930d47b4d9ffe5c20684bd32c7564022779300b`
- Pipeline run: `abevalflow-s7brq`
