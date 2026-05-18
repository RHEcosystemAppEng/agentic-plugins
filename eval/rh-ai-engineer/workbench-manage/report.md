# A/B Evaluation Report: rh-ai-engineer-workbench-manage

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/53
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.7222 |
| Median Reward | 1.0000 | 0.8333 |
| Std Reward | 0.0000 | 0.1924 |

## Comparison

- **Mean reward gap (Uplift):** +0.2778
- **Welch's t-test p-value:** 0.1296
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T19:56:43.821292Z
- Commit SHA: `90d4428c66126b11027cbf410d1d63b66d8d203d`
- Pipeline run: `abevalflow-xrdr7`
