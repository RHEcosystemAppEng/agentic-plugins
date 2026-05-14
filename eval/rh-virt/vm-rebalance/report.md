# A/B Evaluation Report: rh-virt-vm-rebalance

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/19
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9444 | 0.5555 |
| Median Reward | 1.0000 | 0.8333 |
| Std Reward | 0.0962 | 0.4811 |

## Comparison

- **Mean reward gap (Uplift):** +0.3889
- **Welch's t-test p-value:** 0.2949
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T02:59:39.260850+00:00
- Commit SHA: `adca67945e9bf9eec2fa939c85298859e5991b9e`
- Pipeline run: `abevalflow-gz2xl`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-rebalance@sha256:69eee2e7b5650708ce79642717b57d88b1b9f815320f92bf997668fd0b994aa6`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-rebalance@sha256:603f563c2a1dafbe2b78dfbaa9da310786ec3c3c420660ff35894beb88e83999`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-rebalance__CTY5Xsz | 1.0000 | PASS |
| 2 | rh-virt-vm-rebalance__xF5eKhk | 1.0000 | PASS |
| 3 | rh-virt-vm-rebalance__yu4BaCG | 0.8333 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-rebalance__K8mpNka | 0.8333 | PASS |
| 2 | rh-virt-vm-rebalance__QUhQAKn | 0.0000 | FAIL |
| 3 | rh-virt-vm-rebalance__n8zSF2H | 0.8333 | PASS |

</details>
