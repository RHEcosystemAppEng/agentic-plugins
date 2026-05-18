# A/B Evaluation Report: rh-virt-vm-delete

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/16
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.8519 |
| Median Reward | 1.0000 | 0.8889 |
| Std Reward | 0.0000 | 0.0641 |

## Comparison

- **Mean reward gap (Uplift):** +0.1481
- **Welch's t-test p-value:** 0.0572
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T05:01:30.846286+00:00
- Commit SHA: `5eaf7184d1a654b3853fc3f6a93e3224d70bcfbb`
- Pipeline run: `abevalflow-8dng7`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-delete@sha256:535a923032882c14a2a26afdeb72dde925f275716e52fb849032ad894b735a04`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-delete@sha256:bc57f2ca099b4a879575e1934cb94684ccc53d6c14ff6072f0e9f48e3c63dd5c`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-delete__BPuqrDD | 1.0000 | PASS |
| 2 | rh-virt-vm-delete__EvGawYw | 1.0000 | PASS |
| 3 | rh-virt-vm-delete__KLaTsEp | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-delete__TDSV63M | 0.7778 | PASS |
| 2 | rh-virt-vm-delete__vKrzNtA | 0.8889 | PASS |
| 3 | rh-virt-vm-delete__vVdkDkG | 0.8889 | PASS |

</details>
