# A/B Evaluation Report: rh-basic-red-hat-product-lifecycle

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/34
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 1.0000 | 0.6667 |
| Median Reward | 1.0000 | 1.0000 |
| Std Reward | 0.0000 | 0.5774 |

## Comparison

- **Mean reward gap (Uplift):** +0.3333
- **Welch's t-test p-value:** 0.4226
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-11T06:40:26.662985+00:00
- Commit SHA: `ee937fa4d4cc8a62f5c61c1772ce4b1e7192b0cf`
- Pipeline run: `abevalflow-p56xp`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-product-lifecycle@sha256:ac140ca3b83a40986149fdbe0751a148a0cbae0662193e2920c0e4fc4f67b11f`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-product-lifecycle@sha256:07be8f05cc4ba6ed08677a2b4ec18a556e3942b15ffa9a8993d1af5ba5574e03`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-product-lifecyc__FLLR5oj | 1.0000 | PASS |
| 2 | rh-basic-red-hat-product-lifecyc__MZwN2os | 1.0000 | PASS |
| 3 | rh-basic-red-hat-product-lifecyc__dpEfjSa | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-product-lifecyc__PxC3qnP | 1.0000 | PASS |
| 2 | rh-basic-red-hat-product-lifecyc__jmfVbMW | 1.0000 | PASS |
| 3 | rh-basic-red-hat-product-lifecyc__rS6uJpq | 0.0000 | FAIL |

</details>
