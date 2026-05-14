# A/B Evaluation Report: rh-virt-vm-snapshot-restore

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/26
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.7778 |
| Median Reward | 1.0000 | 0.6667 |
| Std Reward | 0.0000 | 0.1924 |

## Comparison

- **Mean reward gap (Uplift):** +0.2222
- **Welch's t-test p-value:** 0.1835
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-09T21:08:19.959611+00:00
- Commit SHA: `85bb892af0701abd811d8e64d6bf4fa7912b73f1`
- Pipeline run: `abevalflow-pppg8`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-restore@sha256:571450d83d67c2b99320ac66b738727a8d33e438733c9593bb7aae61e2d6cfe0`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-snapshot-restore@sha256:5a4e3ae82da01787b27fbbedb2bbb4e40d463885aeeadebd7eebb4f2c84eae92`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-restore__V7KjpFJ | 1.0000 | PASS |
| 2 | rh-virt-vm-snapshot-restore__WA82cug | 1.0000 | PASS |
| 3 | rh-virt-vm-snapshot-restore__Xb6jV47 | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-snapshot-restore__GgTEnq5 | 0.6667 | PASS |
| 2 | rh-virt-vm-snapshot-restore__NZR8jWS | 1.0000 | PASS |
| 3 | rh-virt-vm-snapshot-restore__ePb7hV6 | 0.6667 | PASS |

</details>
