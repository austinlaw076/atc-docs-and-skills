# ATC v1.1 — restricted local Python Runtime

This release adds a kernel-enforced local process profile, `seccomp_python_stdio_v1`. It is a narrow stdio-only Runtime, not a general container or VM. Real model-agent operation inside this profile has **not** been verified. Historical v1.0.1 live model sessions remain advisory evidence only.

## Requirements and policy

Linux x86-64, Python3.11+, `libseccomp.so.2` (commonly the `libseccomp2` system package), and requirements.txt. No privileged daemon, namespaces, external API, key or paid provider is needed. Unsupported platform or failed enforcement prevents worker execution. There is no advisory fallback.

Set `"runtime_policy": "seccomp_python_stdio_v1"` in a PRD. Use a **new run directory**: compiled contracts and schemas are v1.1; old saved runs are not upgraded. Existing PRDs without this field retain `host_trust_boundary` and must be described as advisory.

Host-selected worker files define `run(packet)` and return a JSON object. packet contains prompt, envelope and response_schema. They are compiled, then executed only after the trusted bootstrap has installed restrictions. Input snapshots and accepted dependencies arrive in memory; no source paths need opening. The worker has no host RPC/tool channel. Later imports requiring filesystem access will fail; required standard modules are preloaded by the bootstrap.

```python
import asyncio
import json
from pathlib import Path
from atc10.core import Coordinator, compile_prd
from atc10.isolation import IsolatedPythonRuntime
from atc10.runtime import HostDispatcher

p = Path("examples/atc11/prd.json")
c = Coordinator(compile_prd(json.loads(p.read_text()), p.parent), "outputs/new-11")
try:
    runtime = IsolatedPythonRuntime("examples/atc11/fixture_worker.py")
    report = asyncio.run(HostDispatcher(c, runtime).run())
finally:
    c.close()
```

That example is a **deterministic fixture**, not an LLM researcher/reviewer. A real worker must be separately integrated and validated. Existing CallbackHostRuntime remains available for advisory PRDs; strict PRDs reject it before start. The ordinary CLI cannot fabricate a strict-mode attestation: use HostDispatcher with the restricted Runtime.

## Enforced boundary

- Fresh interpreter with isolated startup, cleared environment, closed unrelated descriptors and bounded stdin; only fd0 input and fd1/fd2 output are permitted.
- Native libseccomp default-deny filter blocks open/openat/openat2, filesystem mutation, sockets, exec/fork/clone, ptrace, parent signaling/memory access and changes to the filter/privileges.
- CPU, address-space, file/core and descriptor limits apply before worker execution. Parent limits wall time, stdout and stderr; cancellation/errors kill and reap the process and drain pipes without accumulating discarded output.
- Trusted readiness binds actual PID/session, exact Prompt, worker/bootstrap/policy hashes and resource limits. A bounded acknowledgment bound to that verified frame gates worker execution; missing or invalid acknowledgment cannot enter payload code. Coordinator requires that evidence before strict-mode receive and rechecks it on accepted reports and dependencies.

The host remains trusted and can forge its own control plane; receipts are not signatures. Startup imports are trusted and occur before filtering. All code runs with the underlying kernel, so kernel vulnerabilities and side channels are outside this profile. Resource caps are per process, not a global concurrency or billing budget. No network provider can be called from this profile. No general filesystem allowlist, Python package loader or arbitrary tool execution is provided.

## Verification

```bash
python -m pytest -q tests
python evaluation/run_isolation.py --output outputs/NEW-isolation-evidence
```

The evaluator produces real child-process canary results and a clearly labelled synthetic three-order workflow, including readiness attestations in its run DB. Existing output directories are refused. See TEST_REPORT_v1_1.md and outputs/atc11-isolation/EVIDENCE_SUMMARY.json. A failed capability probe is blocked/failed, never a passed isolation test.

Design references: [Linux seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html) and [Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html). Seccomp constrains system calls; it is one component of isolation and is not by itself a complete sandbox. Namespace and Landlock probes were unavailable in this environment; they are not claimed as enforcement mechanisms in this release.
