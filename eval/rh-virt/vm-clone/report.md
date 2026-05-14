# A/B Evaluation Report: rh-virt-vm-clone

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/10
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8889 | 0.3333 |
| Median Reward | 0.8333 | 0.3333 |
| Std Reward | 0.0962 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.5556
- **Welch's t-test p-value:** 0.0099
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-09T18:34:10.868743+00:00
- Commit SHA: `b7976dad07db3f068f170d03afd2ba295a3d341e`
- Pipeline run: `abevalflow-ctdw4`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-clone@sha256:43a99fa6a066dce49a24b1dbfb8ae10e6aa655f910a641a03de0b32f6fe78c00`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-virt-vm-clone@sha256:c34a067973d4f0490ec84da6818c7df5163efa8f56daedee8bb2706a48c1bf88`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-clone__STEbawL | 1.0000 | PASS |
| 2 | rh-virt-vm-clone__VWU92ds | 0.8333 | PASS |
| 3 | rh-virt-vm-clone__ZtPxRvN | 0.8333 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-virt-vm-clone__D2ssPf3 | 0.3333 | PASS |
| 2 | rh-virt-vm-clone__dcwCFQo | 0.3333 | PASS |
| 3 | rh-virt-vm-clone__kqEF46R | 0.3333 | PASS |

</details>
