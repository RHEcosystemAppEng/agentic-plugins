# A/B Evaluation Report: rh-automation-aap-mcp-validator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/61
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.1667 |
| Median Reward | 1.0000 | 0.1667 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.8333
- **Welch's t-test p-value:** 0.0000
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T23:33:05.521914Z
- Commit SHA: `8e54d3f31c336415d48d52c60522d4bcb5aeaebc`
- Pipeline run: `abevalflow-t4ckf`
