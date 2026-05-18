# A/B Evaluation Report: rh-virt-vm-inventory

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/6
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 0 |
| Failed | 0 | 3 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.0000 |
| Mean Reward | 0.9047 | 0.0000 |
| Median Reward | 0.8571 | 0.0000 |
| Std Reward | 0.0825 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.9047
- **Welch's t-test p-value:** 0.0028
- **Fisher's exact p-value:** 0.1000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T14:06:46.020270Z
- Commit SHA: `b1db00e92087b369f882523185c36ca61978d881`
- Pipeline run: `abevalflow-hndtj`
