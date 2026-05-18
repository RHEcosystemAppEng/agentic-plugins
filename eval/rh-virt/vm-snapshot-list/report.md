# A/B Evaluation Report: rh-virt-vm-snapshot-list

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/25
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9697 | 0.8485 |
| Median Reward | 1.0000 | 0.9091 |
| Std Reward | 0.0525 | 0.1050 |

## Comparison

- **Mean reward gap (Uplift):** +0.1212
- **Welch's t-test p-value:** 0.1734
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-08T18:05:36.199154+00:00
- Commit SHA: `f96d44d8a711de5c6203a5fbb8af8325dd66e395`
- Pipeline run: `abevalflow-fqsx9`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-list@sha256:a1769d7efcc54a0d837be0e96f649ce558c1c85d89f309e93bce0b92ba80babf`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-list@sha256:6a5c18d82b3786096a60ba0f2688d3dcf36d81fd544ab934d9eab49354ceb964`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-list__Bk7t5b4 | 0.9091 | PASS |
| 2 | rh-virt-vm-snapshot-list__bXbLXhS | 1.0000 | PASS |
| 3 | rh-virt-vm-snapshot-list__o4rqbo8 | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-list__HMMzi7F | 0.7273 | PASS |
| 2 | rh-virt-vm-snapshot-list__ftvfZiL | 0.9091 | PASS |
| 3 | rh-virt-vm-snapshot-list__kwS2UB5 | 0.9091 | PASS |

</details>
