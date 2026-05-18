# A/B Evaluation Report: ocp-admin-cluster-inventory

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/28
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8485 | 0.7576 |
| Median Reward | 0.8182 | 0.7273 |
| Std Reward | 0.0525 | 0.1389 |

## Comparison

- **Mean reward gap (Uplift):** +0.0909
- **Welch's t-test p-value:** 0.3785
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-08T09:32:05.288688+00:00
- Commit SHA: `a4449e2ad8451fc26ac8f1aeb371bbb975bcfff7`
- Pipeline run: `abevalflow-dqzcr`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-inventory@sha256:f7a6b3e8ddb73c21c7a124a099129b6560e151c8e16a2f3a5c21e98e7aada857`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-inventory@sha256:60d13bad13eee61fc4fdaf65cf0297393a8509a97fda01adf58cee8704c09f31`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-inventory__2effbh9 | 0.8182 | PASS |
| 2 | ocp-admin-cluster-inventory__6Zp2qGu | 0.8182 | PASS |
| 3 | ocp-admin-cluster-inventory__NKpHW3U | 0.9091 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-inventory__ByFjuhw | 0.6364 | PASS |
| 2 | ocp-admin-cluster-inventory__KEtmFLy | 0.9091 | PASS |
| 3 | ocp-admin-cluster-inventory__aYXvDrv | 0.7273 | PASS |

</details>
