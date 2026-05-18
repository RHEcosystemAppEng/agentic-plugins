# A/B Evaluation Report: rh-developer-rhel-deploy

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/49
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9524 | 0.5714 |
| Median Reward | 1.0000 | 0.5714 |
| Std Reward | 0.0825 | 0.1429 |

## Comparison

- **Mean reward gap (Uplift):** +0.3809
- **Welch's t-test p-value:** 0.0248
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-16T19:17:00.232568Z
- Commit SHA: `203bc6e69b1b4eef87c88c974bbebf6390be4605`
- Pipeline run: `abevalflow-wxkph`
