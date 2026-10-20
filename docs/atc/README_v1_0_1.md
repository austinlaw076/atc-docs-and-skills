# ATC v1.0.1 research pilot

Correctness fixes: isolated source snapshots, bounded JSON verification, deadline rechecks, product context delivery, per-criterion review and persisted prompt/host receipts. Strong runtime isolation remains unverified.

Use Python3.11+ with requirements.txt. The v1.0 PRD JSON format is preserved subject to the new size/complexity budgets. Always use a NEW run directory: v1.0.1 response schemas and delivery records are stricter and old run databases are not auto-migrated.

```bash
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 compile
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 dispatch R1 > request.json
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 prompt REQUEST_ID > actual-prompt.txt
```

The actual prompt bytes are already persisted at RUN/deliveries/REQUEST_ID.txt. Send those exact UTF-8 bytes as the host-visible user message to a real worker, with no summary/projection. Capture its actual host session ID. Hash the bytes actually sent, then bind and attest delivery:

```bash
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 bind REQUEST_ID HOST_AGENT_ID
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 delivered REQUEST_ID HOST_AGENT_ID SENT_PROMPT_SHA256 HOST_RECEIPT_ID
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 receive REQUEST_ID HOST_AGENT_ID worker-response.json
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 dispatch R1 --role reviewer > review-request.json
```

Repeat prompt→new independent reviewer→bind→delivered→receive. Reviewer JSON includes `criteria:[{criterion_id,satisfied,claim_refs,reason}]` covering every `order.criteria` item, alongside per-claim checks, artifact hash, summary and acceptance_satisfied. A satisfied criterion needs actual supporting claim IDs. Record rejection rather than substituting a host-written approval.

`HostDispatcher` passes the persisted prompt into `HostRuntime.start(..., prompt=...)`. `CallbackHostRuntime` checks that this matches its rendering and sends it directly to the provided start_agent callback. The returned true host agent ID is also used as the local receipt ID; this attests the send through the trusted host, not remote-model internals. Existing custom runtimes must accept the new prompt argument and must send it verbatim.

```bash
python -m pytest -q tests
python -m unittest discover -s tests -p 'test_atc10*.py' -q
python -m atc10 --prd examples/atc10/prd.json --run outputs/new-101 report
```

`fail REQUEST_ID REASON` recovers actual runtime failures/expired requests before a new attempt. No request replay. Accepted reports recheck artifact and delivered-prompt hashes. Only fully accepted requirements with no integrity errors yield accepted_host_reviewed.

See SPEC_v1_0_1.md and TEST_REPORT_v1_0_1.md for current verification. README_v0_9.md and older SPEC/report files describe historical versions. Old live output folders remain historical and are not passed off as v1.0.1 live proof.
