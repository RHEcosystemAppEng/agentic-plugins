# A/B Evaluation Report: rh-sre-mcp-lightspeed-validator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/17
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 1.0000 | 0.3809 |
| Median Reward | 1.0000 | 0.5714 |
| Std Reward | 0.0000 | 0.3299 |

## Comparison

- **Mean reward gap (Uplift):** +0.6191
- **Welch's t-test p-value:** 0.0830
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T04:19:00.743356+00:00
- Commit SHA: `8a3c7c22f92f7ede087294ce13239e946d8e8fd0`
- Pipeline run: `abevalflow-krhxl`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-mcp-lightspeed-validator@sha256:b41b0841814bd6d92ea112ea4d618d42f3de07c4a18ca7161ec959a600b1353b`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-mcp-lightspeed-validator@sha256:8f5fbc4c70c5f62e8637ddde40d38f0bb4f125f2319b342aade905f0db823052`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-mcp-lightspeed-validator__BCnrS9t | 1.0000 | PASS |
| 2 | rh-sre-mcp-lightspeed-validator__EtQV3UT | 1.0000 | PASS |
| 3 | rh-sre-mcp-lightspeed-validator__zCYw3HX | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-mcp-lightspeed-validator__2Jz6yJj | 0.5714 | PASS |
| 2 | rh-sre-mcp-lightspeed-validator__DGJ76nt | 0.0000 | FAIL |
| 3 | rh-sre-mcp-lightspeed-validator__x6Ew2SN | 0.5714 | PASS |

</details>
