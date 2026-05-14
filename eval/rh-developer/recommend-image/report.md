# A/B Evaluation Report: rh-developer-recommend-image

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/37
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9524 | 0.8571 |
| Median Reward | 1.0000 | 0.8571 |
| Std Reward | 0.0825 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.0953
- **Welch's t-test p-value:** 0.1835
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-11T17:33:49.325418+00:00
- Commit SHA: `a7fae96b129d61749ec208bdd526dcc4d1653ac2`
- Pipeline run: `abevalflow-7w576`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-recommend-image@sha256:d0bd366ab5c9b0ed2513d301739a4238c9144a9152e7ceb2fa4c4b0658bfb860`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-recommend-image@sha256:34aa46a7a4f225668cd473d263b4ff18ec0d61c63e480749e383df350dab9f71`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-recommend-image__2GXMP8H | 0.8571 | PASS |
| 2 | rh-developer-recommend-image__i2QZUmn | 1.0000 | PASS |
| 3 | rh-developer-recommend-image__zqUyJjS | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-recommend-image__6QZWkZo | 0.8571 | PASS |
| 2 | rh-developer-recommend-image__QMhkmcX | 0.8571 | PASS |
| 3 | rh-developer-recommend-image__gtdbkJK | 0.8571 | PASS |

</details>
