# A/B Evaluation Report: rh-automation-host-fact-inspector

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/69
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.8571 | 0.2857 |
| Median Reward | 0.8571 | 0.4286 |
| Std Reward | 0.0000 | 0.2475 |

## Comparison

- **Mean reward gap (Uplift):** +0.5714
- **Welch's t-test p-value:** 0.0572
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-16T22:49:02.421694Z
- Commit SHA: `ce8a52d816396ddc1059748ebd358c40b8d4f169`
- Pipeline run: `abevalflow-b2jr8`
