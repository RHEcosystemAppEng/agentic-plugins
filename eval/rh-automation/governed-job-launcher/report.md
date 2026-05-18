# A/B Evaluation Report: rh-automation-governed-job-launcher

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/68
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9524 | 0.4762 |
| Median Reward | 1.0000 | 0.4286 |
| Std Reward | 0.0825 | 0.0824 |

## Comparison

- **Mean reward gap (Uplift):** +0.4762
- **Welch's t-test p-value:** 0.0021
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-16T22:02:15.620574Z
- Commit SHA: `8e58327d9d22a2a941a6c65226cfc66338b70961`
- Pipeline run: `abevalflow-slp87`
