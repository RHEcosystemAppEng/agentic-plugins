# A/B Evaluation Report: rh-sre-job-template-remediation-validator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/11
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.9047 |
| Median Reward | 1.0000 | 0.8571 |
| Std Reward | 0.0000 | 0.0825 |

## Comparison

- **Mean reward gap (Uplift):** +0.0953
- **Welch's t-test p-value:** 0.1835
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-05T19:56:18.660394+00:00
- Commit SHA: `0a6c8f2a54e9c4a903a01554aa397204181ec851`
- Pipeline run: `abevalflow-tblqn`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-job-template-remediation-validator@sha256:7db7e44b9ded890f8c6c9df820da7b9e28f3bcae0ced01706afc23cb18393f84`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-job-template-remediation-validator@sha256:96a268b2517796ea04a9af44a5a8dffbe7be15047a80434cb9e6504dc80f01ce`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-job-template-remediation__7zUghav | 1.0000 | PASS |
| 2 | rh-sre-job-template-remediation__R7tjGUb | 1.0000 | PASS |
| 3 | rh-sre-job-template-remediation__dHFdrdu | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-job-template-remediation__7WnE7rc | 0.8571 | PASS |
| 2 | rh-sre-job-template-remediation__UHPHpWX | 0.8571 | PASS |
| 3 | rh-sre-job-template-remediation__yhJCtLb | 1.0000 | PASS |

</details>