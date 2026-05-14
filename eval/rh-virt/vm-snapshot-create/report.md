# A/B Evaluation Report: rh-virt-vm-snapshot-create

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/7
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 1.0000 | 0.6111 |
| Median Reward | 1.0000 | 0.8333 |
| Std Reward | 0.0000 | 0.5358 |

## Comparison

- **Mean reward gap (Uplift):** +0.3889
- **Welch's t-test p-value:** 0.3356
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T10:53:44.594960+00:00
- Commit SHA: `8426c638d52ed95fe17bac835d28375b0b3156b3`
- Pipeline run: `abevalflow-stzjd`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-create@sha256:2d122d8e846412238b5b91f5351009af018c3f55a2637516abb6437d485f213e`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-create@sha256:fcb29f9ebeca4cabc086ed56031c8a1f8dd6382ad8abc626462b42efb827986f`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-create__dJ8XBst | 1.0000 | PASS |
| 2 | rh-virt-vm-snapshot-create__iufqEBo | 1.0000 | PASS |
| 3 | rh-virt-vm-snapshot-create__tJpnG54 | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-create__8j4BXLC | 0.8333 | PASS |
| 2 | rh-virt-vm-snapshot-create__K38MMkx | 0.0000 | FAIL |
| 3 | rh-virt-vm-snapshot-create__nnJKKQW | 1.0000 | PASS |

</details>
