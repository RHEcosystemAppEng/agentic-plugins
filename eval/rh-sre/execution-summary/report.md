# A/B Evaluation Report: rh-sre-execution-summary

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/21
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9167 | 0.2778 |
| Median Reward | 0.9167 | 0.4167 |
| Std Reward | 0.0834 | 0.2406 |

## Comparison

- **Mean reward gap (Uplift):** +0.6389
- **Welch's t-test p-value:** 0.0330 *
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T01:10:36.623553+00:00
- Commit SHA: `02af6fb2a855866bf4806364c7f358d20396d635`
- Pipeline run: `abevalflow-vcbcp`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-execution-summary@sha256:31b399fec637cb70abc14b5f5d1bbadc9170fa84a5a60afe9b4bb38af76594f1`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-execution-summary@sha256:ab0cda7e471fdd9af6b1673dc38dd1847627624fffa47b1ec4d9a4dd05848f27`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-execution-summary__DnnqnYf | 0.9167 | PASS |
| 2 | rh-sre-execution-summary__E27XPeT | 0.8333 | PASS |
| 3 | rh-sre-execution-summary__q2nzzfs | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-execution-summary__E2jD4c8 | 0.4167 | PASS |
| 2 | rh-sre-execution-summary__NvYXxwT | 0.0000 | FAIL |
| 3 | rh-sre-execution-summary__cRAUdf4 | 0.4167 | PASS |

</details>
