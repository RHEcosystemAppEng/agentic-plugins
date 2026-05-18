# A/B Evaluation Report: rh-developer-debug-rhel

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/45
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.3334 |
| Median Reward | 1.0000 | 0.1667 |
| Std Reward | 0.0000 | 0.2887 |

## Comparison

- **Mean reward gap (Uplift):** +0.6666
- **Welch's t-test p-value:** 0.0572
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T15:25:09.143334Z
- Commit SHA: `88f2c61222dcde1db234ef9fb79162a321f6ba6e`
- Pipeline run: `abevalflow-g6mlm`
