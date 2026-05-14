# A/B Evaluation Report: rh-sre-system-context

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/14
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 2 |
| Failed | 0 | 1 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 0.6667 |
| Mean Reward | 0.9394 | 0.6364 |
| Median Reward | 1.0000 | 0.9091 |
| Std Reward | 0.1050 | 0.5530 |

## Comparison

- **Mean reward gap (Uplift):** +0.3030
- **Welch's t-test p-value:** 0.4438
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T05:47:21.557314+00:00
- Commit SHA: `71948bce90ff2d2d924fff89e52e0fcddff362db`
- Pipeline run: `abevalflow-s9478`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-system-context@sha256:fda927ab1c6fe04107a480b5467fd03b1f53af3371f08ee6f45cfed78bc10877`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-system-context@sha256:0b1ae9176836f594a7aa69c25d8fa6438127fe5544b33e398bfd6aadb2a02ef6`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-system-context__DxZ4SJW | 1.0000 | PASS |
| 2 | rh-sre-system-context__LdJVnx4 | 1.0000 | PASS |
| 3 | rh-sre-system-context__tWXA9m4 | 0.8182 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-system-context__BwwcEdu | 0.9091 | PASS |
| 2 | rh-sre-system-context__FbFfhkS | 0.0000 | FAIL |
| 3 | rh-sre-system-context__GwVtPYw | 1.0000 | PASS |

</details>
