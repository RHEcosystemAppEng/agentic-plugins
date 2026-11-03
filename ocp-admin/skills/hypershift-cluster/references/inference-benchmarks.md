# Measure inference on the verified guest

Use only when inference validation or efficiency comparison is requested. Keep
the application request path intact and distinguish functional checks from isolated
backend measurements. Follow the project's own contributor instructions before
changing code or building images.

## Establish comparability

Record physical hardware, sharing mode, image/runtime/driver versions, CPU quota
and binding, memory limits, model repository **revision**, tokenizer/chat template,
dtype/quantization, context limit, sampling parameters, input/output lengths and
concurrency. Pin model revisions when the supported serving path allows it; otherwise
record the resolved revision or state that it was not pinned. A different model
size or quantization changes quality and workload as well as hardware demand.

For a hardware-oriented comparison, use the same model and precision on each
platform where feasible. A temporary same-model control needs its own resource
budget, placement and identity receipt. Keep it outside production/demo routing,
avoid competing with the measured workload, and remove it after measurements.
Report CPU runtime preload, NUMA, instruction-set and thread-binding warnings;
an untuned deployment baseline is not a claim of maximum CPU performance. Apply
tuning only as a deliberate, supported change and report before/after separately.

## Collect meaningful measurements

- Define a fixed prompt corpus and output-length/concurrency policy before running.
  Record exact input lengths and excluded warmups. Measure equivalent warmed
  conditions, including batch shapes when compilation is relevant. Separate model
  download, compilation/startup, prefill and steady serving where the tools permit.
- Count tokens from backend usage or a documented tokenizer. Do not treat
  characters/4 or the trace UI's estimated count as exact usage. Validate streaming
  usage support with a small probe before a long trial. If forcing output length,
  verify the runtime supports the option and report that natural EOS was disabled.
- Define aggregate throughput as total completed output tokens divided by batch
  wall time. Report successful/failed requests, concurrency, TTFT (first nonempty
  content delta), full-request latency and sample size. A small exploratory sample
  does not establish saturation, production capacity or mathematical answer quality.
- Inspect prefix-cache counters before/after each trial. Unique user text alone can
  leave a shared system/chat-template prefix cached on one runtime. If cache reuse
  is outside the comparison, use supported isolation/reset semantics and verify
  actual zero cache-hit deltas. vLLM supports per-request
  [cache salting](https://docs.vllm.ai/en/stable/usage/security/); confirm support in
  the deployed version. Preserve superseded trial evidence and explain reruns.
- Preserve raw per-request timings/usage, runtime metric snapshots and the script
  version privately. Record failures rather than dropping them from the denominator
  or presenting a success-only trial as reliable capacity.

## Validate the product path separately

Send representative requests through the deployed router/UI API and both backend
choices. Check the classifier's actual label and destination, final status,
fallback signal and persisted trace. Verify simple answer correctness explicitly;
do not certify a truncated generated proof as mathematically correct. Test failover
only when appropriate and report whether it was actually exercised.

Measure backend streaming and routed streaming separately. A relay that reads a
large fixed buffer before flushing can delay visible content until generation is
nearly complete. That delay is not backend TTFT. Confirm the symptom with timing
and source inspection, and keep any relay code change separate from the baseline
measurement. UI health/HTML and API chat tests do not establish browser layout QA.

Use owned localhost-only port-forwards with the pinned guest kubeconfig/context,
and close them afterward. For HTTPS, trust the CA that actually signed the served
certificate; HyperShift ingress may use the guest root rather than a locally
generated ingress-operator CA. Verify chain/hostname instead of bypassing TLS.

## Report efficiency with its scope

Give tokens/s, latency and exact usage before interpreting efficiency. A compute-only
cost estimate at measured utilization is:

`worker hourly price / 3600 / output tokens per second × 1,000,000`.

State whether the price charges the whole worker or an allocated share. Verify
current provider/region/OS prices and identify excluded idle time, management,
support nodes, networking, storage and software costs. The always-on cluster bill
does not shrink merely because requests are routed to CPU. Distinguish reservation
of GPU capacity from actual scale-down savings. Do not report energy per token
without measured power/energy for a stated system boundary, or results for hardware
that was never tested.

Return a compact comparison plus raw CSV/JSON and reproducible access/test commands.
Label different-model comparisons and runtime/tuning limitations. Retain the guest
unless teardown was requested; then follow [teardown.md](teardown.md) and keep the
benchmark evidence after verified cleanup.
