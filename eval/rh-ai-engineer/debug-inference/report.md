# A/B Evaluation Report: rh-ai-engineer-debug-inference

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/29
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 1.0000 | 0.6333 |
| Median Reward | 1.0000 | 0.9000 |
| Std Reward | 0.0000 | 0.5508 |

## Comparison

- **Mean reward gap (Uplift):** +0.3667
- **Welch's t-test p-value:** 0.3681
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T13:56:15.990280+00:00
- Commit SHA: `8afb9cc16e1342e74c2413ce7d54e23143a2b8a1`
- Pipeline run: `abevalflow-j98rh`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-debug-inference@sha256:82f98dbd5b7e8e73b18b936151191b41f5fabd8e18428fe5d3c618bb3f06b7a6`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-debug-inference@sha256:cb159981432a6d5b6d3e2533e9fe244a68ecf2a0262821e396f2421bbc3455e6`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-debug-inference__88dWURF | 1.0000 | PASS |
| 2 | rh-ai-engineer-debug-inference__TZg5QW2 | 1.0000 | PASS |
| 3 | rh-ai-engineer-debug-inference__XYELkza | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-debug-inference__PrAHgb4 | 1.0000 | PASS |
| 2 | rh-ai-engineer-debug-inference__Y6tNdi7 | 0.9000 | PASS |
| 3 | rh-ai-engineer-debug-inference__zh4q2Po | 0.0000 | FAIL |

</details>
