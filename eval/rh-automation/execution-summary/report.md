# A/B Evaluation Report: rh-automation-execution-summary

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/63
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9444 | 0.7222 |
| Median Reward | 1.0000 | 0.6667 |
| Std Reward | 0.0962 | 0.0962 |

## Comparison

- **Mean reward gap (Uplift):** +0.2222
- **Welch's t-test p-value:** 0.0474
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-15T00:31:39.019554Z
- Commit SHA: `1baa71c966ddb41283efa260574cf72c0568d3cd`
- Pipeline run: `abevalflow-rznzc`
