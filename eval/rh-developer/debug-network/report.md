# A/B Evaluation Report: rh-developer-debug-network

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/39
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.9000 |
| Median Reward | 1.0000 | 0.9000 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.1000
- **Welch's t-test p-value:** 0.0000*
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T22:59:08.295180+00:00
- Commit SHA: `4639d97e84d05b93143dc6331bca48f937b30685`
- Pipeline run: `abevalflow-gn8qm`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-debug-network@sha256:a16083ad7658ff0fb2b71bc9810eed9c18499df3bca4c79fbc1bc992c8487644`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-debug-network@sha256:dbbb520e5ab466886bfda6c61c9007c8e99bf49ccd3235d22cb0ed4ae5e8e41c`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-debug-network__Hrjcz4w | 1.0000 | PASS |
| 2 | rh-developer-debug-network__nexHbib | 1.0000 | PASS |
| 3 | rh-developer-debug-network__oXk49do | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-debug-network__KkAb6o9 | 0.9000 | PASS |
| 2 | rh-developer-debug-network__WrmyT8T | 0.9000 | PASS |
| 3 | rh-developer-debug-network__yVU6S7q | 0.9000 | PASS |

</details>
