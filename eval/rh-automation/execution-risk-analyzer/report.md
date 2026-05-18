# A/B Evaluation Report: rh-automation-execution-risk-analyzer

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/62
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9047 | 0.2857 |
| Median Reward | 0.8571 | 0.4286 |
| Std Reward | 0.0825 | 0.2475 |

## Comparison

- **Mean reward gap (Uplift):** +0.6190
- **Welch's t-test p-value:** 0.0384
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-16T20:27:14.166440Z
- Commit SHA: `fb68963123b5b3a3a3affd871ff442b6945fff48`
- Pipeline run: `abevalflow-gx2cz`
