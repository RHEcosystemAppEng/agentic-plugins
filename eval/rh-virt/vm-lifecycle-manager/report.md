# A/B Evaluation Report: rh-virt-vm-lifecycle-manager

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/18
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.8889 | 0.5000 |
| Median Reward | 0.8333 | 0.6667 |
| Std Reward | 0.0962 | 0.4410 |

## Comparison

- **Mean reward gap (Uplift):** +0.3889
- **Welch's t-test p-value:** 0.2637
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-13T17:54:58.055980+00:00
- Commit SHA: `fc8ebb25420237ae5b9064b004ff1dbce890b329`
- Pipeline run: `abevalflow-pr9v6`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-lifecycle-manager@sha256:f57fb8fe607ac705cbe400d5ae98a1bdfc8a4e80ca970a85f41181ff01c2cec3`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-lifecycle-manager@sha256:5cc70112f2c266b9ca7df6da00ae5f6c7cc5a4fb6ca60f2541403f164149736f`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-lifecycle-manager__FWedXLE | 0.8333 | PASS |
| 2 | rh-virt-vm-lifecycle-manager__d3uEgqH | 1.0000 | PASS |
| 3 | rh-virt-vm-lifecycle-manager__s9uQBMY | 0.8333 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-lifecycle-manager__M6uzZ9J | 0.6667 | PASS |
| 2 | rh-virt-vm-lifecycle-manager__QApYK6c | 0.8333 | PASS |
| 3 | rh-virt-vm-lifecycle-manager__ZXYnTwk | 0.0000 | FAIL |

</details>
