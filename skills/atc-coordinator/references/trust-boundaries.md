# ATC v1.1 trust boundaries

## Coordinator

Worker/reviewer JSON is data, never a tool command. The trusted Host pins the bounded source corpus, owns identity binding, delivery/isolation attestations, SQLite and all artifact writes. Hashes bind inputs, source text/lines, criteria, prompts and accepted dependencies. They are not signatures or protection against a malicious Host/database owner. Keep state/output directories private; filesystem-owner races are outside this boundary.

Different sessions and producer/reviewer roles reduce self-review but do not establish independent providers or correct model judgement. Exact quotes prove provenance, not entailment. Source/prompt injection is treated as data by instructions; no complete injection defense is claimed. max_attempts currently bounds Worker retries; Host still controls Reviewer retries, total workloads and billing.

## Restricted local profile

Only runtime_policy=seccomp_python_stdio_v1 selects the enforced local process profile. It launches a fresh interpreter with a fixed trusted bootstrap, clean environment, closed unrelated descriptors and per-process resource caps. The Host chooses the worker program; task data never selects an executable, path or shell command.

Bootstrap imports/compilation are trusted startup work. A native libseccomp default-deny filter is installed before any Worker module code executes. Only fd0 input, fd1/fd2 output and the narrow memory/time/signal/exit syscall set remain. Filesystem opens/mutations, network sockets, new programs/processes/threads, parent process access and filter changes are denied. Required modules must be preloaded; this profile cannot call a remote model API or load arbitrary packages after startup.

The Host verifies the exact readiness record, including PID, prompt/program/bootstrap/policy hashes and limits, then sends a bounded acknowledgment tied to that record. Missing/invalid acknowledgment prevents execution. Coordinator requires the Host-recorded evidence for strict receive and rechecks it for accepted reports/dependencies. This is trusted-host evidence, not hardware attestation or a signed remote receipt.

Cancellation, wall timeout, output overflow and malformed output trigger process termination/reaping and bounded output handling. CPU/address-space/file/core/descriptor limits apply per process. These do not provide global capacity or cost budgets, guaranteed hard-real-time response, durable parent-crash supervision, kernel-vulnerability protection or a general VM/container boundary. The trusted Python/libseccomp/kernel and startup dependencies remain in scope of trust.

## Advisory mode and provenance

PRDs without runtime_policy or with host_trust_boundary remain advisory. CallbackHostRuntime tools=[] is a Host request, not proof that an external runtime removed its tool catalog. Strict PRDs reject that Runtime rather than falling back.

Historical v1.0.1 live model-agent runs used advisory restrictions. v1.1 verifies actual local process denials plus deterministic fixture workflows; no live model inside this profile has been validated. Do not combine those two histories into an end-to-end enforced model claim. No credentials, paid provider, external action or deployment was added.

See [Linux seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html): syscall filtering is an isolation building block, not a complete sandbox. Namespace and Landlock mechanisms were unavailable in the observed environment and are not claimed as this profile's enforcement.
