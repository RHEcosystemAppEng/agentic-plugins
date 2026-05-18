# A/B Evaluation Report: rh-sre-remediation

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/5
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9333 | 0.5000 |
| Median Reward | 0.9000 | 0.5000 |
| Std Reward | 0.0577 | 0.1000 |

## Comparison

- **Mean reward gap (Uplift):** +0.4333
- **Welch's t-test p-value:** 0.0061
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-07T11:08:43.791786+00:00
- Commit SHA: `196a2028dbb3b1a3b9d9f04ffa9a9e10e7f87281`
- Pipeline run: `abevalflow-79xr7`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-remediation@sha256:29f01d69b6d8970c26fd4b03efe3bdfee9ff85287f104aab555845377a8136bc`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-remediation@sha256:9248e92d534e69fd3fb8fb9c725f2d3344da5bb1f2a14ad29e1eda89c533f0a3`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-remediation__EHXxEoU | 0.9000 | PASS |
| 2 | rh-sre-remediation__mgVj6Y5 | 0.9000 | PASS |
| 3 | rh-sre-remediation__vMpzmEL | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-remediation__3jZ8C6c | 0.5000 | PASS |
| 2 | rh-sre-remediation__GTJyQuq | 0.4000 | PASS |
| 3 | rh-sre-remediation__wzRDKZi | 0.6000 | PASS |

</details>
