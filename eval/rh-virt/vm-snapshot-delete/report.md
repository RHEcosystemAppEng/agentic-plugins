# A/B Evaluation Report: rh-virt-vm-snapshot-delete

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/24
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.8889 |
| Median Reward | 1.0000 | 0.8333 |
| Std Reward | 0.0000 | 0.0962 |

## Comparison

- **Mean reward gap (Uplift):** +0.1111
- **Welch's t-test p-value:** 0.1835
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T09:12:37.583030+00:00
- Commit SHA: `4220fd3b2f72a04d367f5bc45abb7755123b2b17`
- Pipeline run: `abevalflow-ld8qq`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-delete@sha256:0ddaf7a18dcbef066dd937f1f88f7711459a23fb0bb8e8ffd6d1b526484ca96a`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-delete@sha256:8010efb2fca10938c4e9eca2b916c9c8c673d0c6ce8d85e06421bd28190f8a04`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-delete__Pc3VvfT | 1.0000 | PASS |
| 2 | rh-virt-vm-snapshot-delete__iWwNk2w | 1.0000 | PASS |
| 3 | rh-virt-vm-snapshot-delete__xDYJ2ms | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-delete__U3GDHtn | 1.0000 | PASS |
| 2 | rh-virt-vm-snapshot-delete__VABsBRN | 0.8333 | PASS |
| 3 | rh-virt-vm-snapshot-delete__bMw6Hb3 | 0.8333 | PASS |

</details>
