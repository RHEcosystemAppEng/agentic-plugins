# A/B Evaluation Report: rh-virt-vm-create

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/4
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.5714 |
| Median Reward | 1.0000 | 0.5714 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.4286
- **Welch's t-test p-value:** 0.0000*
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-09T16:55:27.277362+00:00
- Commit SHA: `3a79148da85e625188c3158dc2bbee22741c5fbb`
- Pipeline run: `abevalflow-kcfcm`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-create@sha256:189e7c6ce2c2f44572fb90dfa1c649ccc52f7e61ea2bc0e12a237aabdf07613d`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-create@sha256:3c94840d360ae2782bb282eb6a1c2a64b2420677dbb9d3545304f1935aeb7262`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-create__Lk9aqhv | 1.0000 | PASS |
| 2 | rh-virt-vm-create__dNkrt3N | 1.0000 | PASS |
| 3 | rh-virt-vm-create__wHuiyqp | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-create__4BtXuH7 | 0.5714 | PASS |
| 2 | rh-virt-vm-create__4LEP3Yg | 0.5714 | PASS |
| 3 | rh-virt-vm-create__mKEFUgW | 0.5714 | PASS |

</details>
