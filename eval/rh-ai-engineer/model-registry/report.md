# A/B Evaluation Report: rh-ai-engineer-model-registry

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/57
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.8889 | 0.4445 |
| Median Reward | 0.8333 | 0.6667 |
| Std Reward | 0.0962 | 0.3849 |

## Comparison

- **Mean reward gap (Uplift):** +0.4444
- **Welch's t-test p-value:** 0.1776
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-14T22:13:08.943797Z
- Commit SHA: `522328c85b1a53b524179788bc7c2ed32643758b`
- Pipeline run: `abevalflow-ldkf7`
