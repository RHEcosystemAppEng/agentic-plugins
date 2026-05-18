# A/B Evaluation Report: rh-sre-mcp-aap-validator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/9
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 1 |
| Failed | 0 | 2 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.3333 |
| Mean Reward | 1.0000 | 0.2857 |
| Median Reward | 1.0000 | 0.0000 |
| Std Reward | 0.0000 | 0.4948 |

## Comparison

- **Mean reward gap (Uplift):** +0.7143
- **Welch's t-test p-value:** 0.1296
- **Fisher's exact p-value:** 0.4000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T08:32:46.327474+00:00
- Commit SHA: `700e94b84c5765a75f27984ed7eb49b65ae99b57`
- Pipeline run: `abevalflow-kkjt4`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-mcp-aap-validator@sha256:51c56c952e95acd750c0558904809253cd26b62d9b212609501b62b5735b9faf`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-mcp-aap-validator@sha256:e990fd9591f2e0450562bd243be4bc0576255d0267b988d0bdb838823c4594c3`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-mcp-aap-validator__E26HbnT | 1.0000 | PASS |
| 2 | rh-sre-mcp-aap-validator__cLNHUhJ | 1.0000 | PASS |
| 3 | rh-sre-mcp-aap-validator__fumhhFc | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-mcp-aap-validator__8hLUnoP | 0.0000 | FAIL |
| 2 | rh-sre-mcp-aap-validator__jVxtpyd | 0.0000 | FAIL |
| 3 | rh-sre-mcp-aap-validator__ynqQ8Au | 0.8571 | PASS |

</details>
