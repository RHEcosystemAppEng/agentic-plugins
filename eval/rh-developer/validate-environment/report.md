# A/B Evaluation Report: rh-developer-validate-environment

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/36
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.7143 |
| Median Reward | 1.0000 | 0.7143 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.2857
- **Welch's t-test p-value:** 0.0000*
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-10T21:23:34.202942+00:00
- Commit SHA: `48a7ee5b9ab6ab7450c90adcfde9fd18128f7133`
- Pipeline run: `abevalflow-95bjh`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-validate-environment@sha256:728f580baab5b212b0369c7550d6c8ea34b65aa69d1b47337c5a0b2ea038510f`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-validate-environment@sha256:8655aa3d75c09703d585afc370148c0cd2bc77455970debbdcba69ae0d688b92`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-validate-environmen__4Jfb9Ym | 1.0000 | PASS |
| 2 | rh-developer-validate-environmen__TyizGKW | 1.0000 | PASS |
| 3 | rh-developer-validate-environmen__qHBAJGV | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-validate-environmen__V7EQxKN | 0.7143 | PASS |
| 2 | rh-developer-validate-environmen__bGe9qRr | 0.7143 | PASS |
| 3 | rh-developer-validate-environmen__nXYwxvu | 0.7143 | PASS |

</details>
