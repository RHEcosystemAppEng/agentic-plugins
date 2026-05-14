# A/B Evaluation Report: rh-developer-debug-container

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/43
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9667 | 0.6333 |
| Median Reward | 1.0000 | 0.9000 |
| Std Reward | 0.0577 | 0.5508 |

## Comparison

- **Mean reward gap (Uplift):** +0.3333
- **Welch's t-test p-value:** 0.4046
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-11T12:28:51.765279+00:00
- Commit SHA: `11f4c6d8a327729a5bb33bfd6c205f61b1eb86d0`
- Pipeline run: `abevalflow-8q82z`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-debug-container@sha256:b04296f2fc0ba00ad7f6a66b884e7e80169bee905b25be61adc374f8e33d8bb1`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-debug-container@sha256:fccf20ba9327326728eebd4cdc1af1dc200fd432a01b747b4538638399823ff0`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-debug-container__4RN4HYB | 0.9000 | PASS |
| 2 | rh-developer-debug-container__SZ8dmzs | 1.0000 | PASS |
| 3 | rh-developer-debug-container__rXnhnMp | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-debug-container__4yXQsEd | 0.9000 | PASS |
| 2 | rh-developer-debug-container__pJHnfeS | 1.0000 | PASS |
| 3 | rh-developer-debug-container__uqY2Hee | 0.0000 | FAIL |

</details>
