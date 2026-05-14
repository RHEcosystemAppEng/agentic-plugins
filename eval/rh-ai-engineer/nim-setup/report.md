# A/B Evaluation Report: rh-ai-engineer-nim-setup

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/31
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.7333 |
| Median Reward | 1.0000 | 0.7000 |
| Std Reward | 0.0000 | 0.0577 |

## Comparison

- **Mean reward gap (Uplift):** +0.2667
- **Welch's t-test p-value:** 0.0153 *
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-11T20:42:51.824599+00:00
- Commit SHA: `817cf57cea7b9acd1bd6ea1df9cdc2f41065f60f`
- Pipeline run: `abevalflow-64llt`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-nim-setup@sha256:371bcaf8b623441c8c7b5ecb46150f374f47587021c06bde356ed871f2b794ec`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-ai-engineer-nim-setup@sha256:d3a6115eaab870941ce5729ef6307151c256fb1eac922f4a6b6ef29ca9f4cafc`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-nim-setup__NkaAh7K | 1.0000 | PASS |
| 2 | rh-ai-engineer-nim-setup__PoPkG73 | 1.0000 | PASS |
| 3 | rh-ai-engineer-nim-setup__c8YWzAK | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-ai-engineer-nim-setup__B75tczM | 0.7000 | PASS |
| 2 | rh-ai-engineer-nim-setup__cGMdBtr | 0.8000 | PASS |
| 3 | rh-ai-engineer-nim-setup__wVuCJ8t | 0.7000 | PASS |

</details>
