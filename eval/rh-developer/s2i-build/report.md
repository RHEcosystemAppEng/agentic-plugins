# A/B Evaluation Report: rh-developer-s2i-build

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/40
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.8889 |
| Median Reward | 1.0000 | 0.8889 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.1111
- **Welch's t-test p-value:** 0.0000*
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T23:36:43.506087+00:00
- Commit SHA: `bff97f866b6a59022431d491efad296f8289d3d6`
- Pipeline run: `abevalflow-66hgp`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-s2i-build@sha256:2d182d150fe22e02f7f4c0146e9252dc9bb6d3a06037c865eb68005042100e96`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-s2i-build@sha256:9bfb1160b357dd128f14a2dbb4f66b07b7ff944b34be02f1499d8c12494bdff2`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-s2i-build__bkxniou | 1.0000 | PASS |
| 2 | rh-developer-s2i-build__i3NrPRf | 1.0000 | PASS |
| 3 | rh-developer-s2i-build__veNYK3D | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-s2i-build__BLRcqBS | 0.8889 | PASS |
| 2 | rh-developer-s2i-build__Cnd8Y3v | 0.8889 | PASS |
| 3 | rh-developer-s2i-build__T3PSvfk | 0.8889 | PASS |

</details>
