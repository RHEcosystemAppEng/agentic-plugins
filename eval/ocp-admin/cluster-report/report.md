# A/B Evaluation Report: ocp-admin-cluster-report

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/3
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 1 |
| Failed | 0 | 2 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.3333 |
| Mean Reward | 0.9091 | 0.2727 |
| Median Reward | 0.9091 | 0.0000 |
| Std Reward | 0.0000 | 0.4724 |

## Comparison

- **Mean reward gap (Uplift):** +0.6364
- **Welch's t-test p-value:** 0.1448
- **Fisher's exact p-value:** 0.4000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T11:05:34.424536+00:00
- Commit SHA: `0f448e0ae9610166053dde81af92f6a0288543bb`
- Pipeline run: `abevalflow-s7fp5`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-report@sha256:f9723786d85d6fa3a5fe2fd0770c2f638ca0f05625146009e4921d62c7a92f89`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-report@sha256:9902f8feb13266de61565a2e5c5c9db771b88b1e3acbb9ad25e3c9fe4329d373`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-report__JM9AwJ2 | 0.9091 | PASS |
| 2 | ocp-admin-cluster-report__NdGgVSJ | 0.9091 | PASS |
| 3 | ocp-admin-cluster-report__qSvNkzV | 0.9091 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-report__LhreyEP | 0.8182 | PASS |
| 2 | ocp-admin-cluster-report__bTJTUSe | 0.0000 | FAIL |
| 3 | ocp-admin-cluster-report__q865w8X | 0.0000 | FAIL |

</details>
