# A/B Evaluation Report: rh-sre-playbook-generator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/13
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.9697 | 0.8485 |
| Median Reward | 1.0000 | 0.9091 |
| Std Reward | 0.0525 | 0.1050 |

## Comparison

- **Mean reward gap (Uplift):** +0.1212
- **Welch's t-test p-value:** 0.1734
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T06:27:46.523633+00:00
- Commit SHA: `8352a8f9c9146a8da8a5b02ea01e808cc4d25bcb`
- Pipeline run: `abevalflow-2g6nh`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-playbook-generator@sha256:f054e3f834ae1d813e3610c77676f2b59c3921fd5df2bf86ffc91c301ce4cdae`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-playbook-generator@sha256:0a41a68bb48b9b1c31c2b46bfa6fda1107c1afeaba49daec1018c4d86c4315b3`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-playbook-generator__FYdbqCz | 1.0000 | PASS |
| 2 | rh-sre-playbook-generator__hBkkQBV | 0.9091 | PASS |
| 3 | rh-sre-playbook-generator__m3GRAnd | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-playbook-generator__2UKpsAz | 0.7273 | PASS |
| 2 | rh-sre-playbook-generator__QiXp9CT | 0.9091 | PASS |
| 3 | rh-sre-playbook-generator__Uz4AKRk | 0.9091 | PASS |

</details>
