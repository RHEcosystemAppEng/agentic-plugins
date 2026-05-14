# A/B Evaluation Report: rh-basic-red-hat-support-severity

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/35
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.8889 |
| Median Reward | 1.0000 | 0.8333 |
| Std Reward | 0.0000 | 0.0962 |

## Comparison

- **Mean reward gap (Uplift):** +0.1111
- **Welch's t-test p-value:** 0.1835
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-13T20:22:54.621127+00:00
- Commit SHA: `00087c12db7ae45689bf8aeb2fea936bc9bee3e7`
- Pipeline run: `abevalflow-624rf`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-support-severity@sha256:2b721f5d6dae8394054a8c9672101733f3e158265e316743f7fd70f1ee613021`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-basic-red-hat-support-severity@sha256:c90e722f817fd55fd3b05d9ae2c8f5a1afab1c6f1658a453bbbc5f098d58983d`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-support-severit__G7Exfzr | 1.0000 | PASS |
| 2 | rh-basic-red-hat-support-severit__UbGoSJY | 1.0000 | PASS |
| 3 | rh-basic-red-hat-support-severit__tuoBx83 | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-basic-red-hat-support-severit__3ZogVyQ | 1.0000 | PASS |
| 2 | rh-basic-red-hat-support-severit__9R8dgwH | 0.8333 | PASS |
| 3 | rh-basic-red-hat-support-severit__YB3Wuiz | 0.8333 | PASS |

</details>
