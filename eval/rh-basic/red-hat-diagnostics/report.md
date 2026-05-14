# A/B Evaluation Report: rh-basic-red-hat-diagnostics

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/33
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.7037 |
| Median Reward | 1.0000 | 0.6667 |
| Std Reward | 0.0000 | 0.0641 |

## Comparison

- **Mean reward gap (Uplift):** +0.2963
- **Welch's t-test p-value:** 0.0153 *
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T16:48:59.701201+00:00
- Commit SHA: `2c0debdad99d3ff507f6d018fd94af06a2054a66`
- Pipeline run: `abevalflow-6cgdf`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-diagnostics@sha256:8e4f319b22ade181f0ce1864fd3c48d767f52dd672b27102dd96019fe4386d81`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-diagnostics@sha256:fe83233fd7c15b2b0e348c477c98bcd7ce4f292598069ea557edc1390567b746`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-diagnostics__7XsDXU3 | 1.0000 | PASS |
| 2 | rh-basic-red-hat-diagnostics__KZ7SBiL | 1.0000 | PASS |
| 3 | rh-basic-red-hat-diagnostics__KvTHN2H | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-diagnostics__FAqeh6V | 0.6667 | PASS |
| 2 | rh-basic-red-hat-diagnostics__HbQZeQS | 0.6667 | PASS |
| 3 | rh-basic-red-hat-diagnostics__kKvQFGQ | 0.7778 | PASS |

</details>
