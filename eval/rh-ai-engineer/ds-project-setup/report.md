# A/B Evaluation Report: rh-ai-engineer-ds-project-setup

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/51
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 1 |
| Failed | 0 | 2 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.3333 |
| Mean Reward | 0.9333 | 0.2667 |
| Median Reward | 0.9000 | 0.0000 |
| Std Reward | 0.0577 | 0.4619 |

## Comparison

- **Mean reward gap (Uplift):** +0.6667
- **Welch's t-test p-value:** 0.1275
- **Fisher's exact p-value:** 0.4000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T17:28:47.619003+00:00
- Commit SHA: `bc90559c812977f19fad8b62e46479ba457d367d`
- Pipeline run: `abevalflow-qmxns`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-ds-project-setup@sha256:0dcc5b5e037dfa909ccae75fe5b6ab3a8c0d6fe17d4e8ff97bccf8f0ff91759e`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-ds-project-setup@sha256:8c9ae04d5e0be8577db3d94bd0161553117f0a1153b448dce9aeb08ae864052e`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-ds-project-setup__QswMpnT | 0.9000 | PASS |
| 2 | rh-ai-engineer-ds-project-setup__ZxMohFy | 1.0000 | PASS |
| 3 | rh-ai-engineer-ds-project-setup__m8J696y | 0.9000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-ds-project-setup__JmpxQ2D | 0.0000 | FAIL |
| 2 | rh-ai-engineer-ds-project-setup__fQx8PKW | 0.8000 | PASS |
| 3 | rh-ai-engineer-ds-project-setup__sBtCJyL | 0.0000 | FAIL |

</details>
