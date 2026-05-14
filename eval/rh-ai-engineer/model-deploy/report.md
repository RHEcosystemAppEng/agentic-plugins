# A/B Evaluation Report: rh-ai-engineer-model-deploy

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/30
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9630 | 0.6296 |
| Median Reward | 1.0000 | 0.8889 |
| Std Reward | 0.0641 | 0.5481 |

## Comparison

- **Mean reward gap (Uplift):** +0.3333
- **Welch's t-test p-value:** 0.4028
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T19:17:49.862673+00:00
- Commit SHA: `ac04791fc01b86e70aad50c1f071f43ac1bb5f04`
- Pipeline run: `abevalflow-g8q9k`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-model-deploy@sha256:cef9f0fb656efef7a21587f1803f615df84e963b8357d7a42b8e6b0939c78dfe`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-model-deploy@sha256:438a4b756344c367f5be20f2a456656597d8c6e41006bf76d9e2870a7c2cf34b`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-model-deploy__4WeSntA | 0.8889 | PASS |
| 2 | rh-ai-engineer-model-deploy__A2Qjprf | 1.0000 | PASS |
| 3 | rh-ai-engineer-model-deploy__GhZxRpq | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-model-deploy__LMM8khi | 1.0000 | PASS |
| 2 | rh-ai-engineer-model-deploy__k69sETE | 0.8889 | PASS |
| 3 | rh-ai-engineer-model-deploy__pejhh4V | 0.0000 | FAIL |

</details>
