"""Trusted coordinator. Workers return JSON data, never executable commands.

The host authenticates runtime identities; this is not an OS sandbox. Only the
coordinator reads source files and writes outputs. Source text is untrusted data.
"""
from __future__ import annotations

import copy
import hashlib
import json
import secrets
import sqlite3
import time
from itertools import islice
from pathlib import Path

from jsonschema import Draft202012Validator


class ContractError(ValueError):
    pass


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def validate(value, kind):
    path = Path(__file__).resolve().parent.parent / "schemas" / f"{kind}_v1_1.schema.json"
    schema = json.loads(path.read_text())
    bound_json(value)
    errors = list(islice(Draft202012Validator(schema).iter_errors(value), 5))
    if errors:
        raise ContractError("; ".join(e.message[:500] for e in errors[:5]))



def bound_json(value):
    """Bound untrusted shapes before schema validation or serialization."""
    stack = [(value, 0)]
    nodes = 0
    byte_estimate = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 8192 or depth > 16:
            raise ContractError("JSON complexity budget exceeded")
        if isinstance(item, str):
            if len(item) > 10000:
                raise ContractError("string budget exceeded")
            byte_estimate += len(json.dumps(item).encode())
        else:
            byte_estimate += 8
        if byte_estimate > 500_000:
            raise ContractError("JSON byte budget exceeded")
        if isinstance(item, dict):
            if len(item) > 32:
                raise ContractError("too many object fields")
            if any(not isinstance(key, str) or len(key) > 128 for key in item):
                raise ContractError("object key budget exceeded")
            byte_estimate += sum(len(json.dumps(key).encode()) + 2 for key in item)
            stack.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            if len(item) > 128:
                raise ContractError("array item budget exceeded")
            stack.extend((v, depth + 1) for v in item)
    if len(json.dumps(value, allow_nan=False).encode()) > 500_000:
        raise ContractError("JSON byte budget exceeded")


def check_sources(bundle):
    for source in bundle['sources'].values():
        if (hashlib.sha256(source['text'].encode('utf-8')).hexdigest() != source['sha256']
                or source['lines'] != source['text'].splitlines()):
            raise ContractError("source snapshot inconsistent")

def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ContractError("invalid relative path")
    if relative.startswith("/") or any(p in ("", ".", "..") for p in relative.split("/")):
        raise ContractError("unsafe relative path")
    target = root / relative
    # Check all ancestors, including a symlink in the caller-supplied root.
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ContractError("symlink forbidden")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ContractError("path outside root")
    return target


def unique(items, field="id"):
    ids = [item[field] for item in items]
    if len(ids) != len(set(ids)):
        raise ContractError(f"duplicate {field}")


def compile_prd(prd, source_root):
    """Compile a structured PRD into deterministic work orders; no invented scope."""
    validate(prd, "prd")
    prd = copy.deepcopy(prd)
    unique(prd["requirements"])
    unique(prd["sources"])
    root = Path(source_root).absolute()
    sources = {}
    total = 0
    for source in prd["sources"]:
        path = safe_path(root, source["path"])
        if not path.is_file() or path.stat().st_size > 200_000:
            raise ContractError("source missing or larger than 200 KB")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        total += len(raw)
        if total > 500_000:
            raise ContractError("source budget exceeded")
        sources[source["id"]] = {"path": source["path"], "sha256": hashlib.sha256(raw).hexdigest(),
                                  "text": text, "lines": text.splitlines()}
    requirements = {r["id"] for r in prd["requirements"]}
    orders = {}
    for req in prd["requirements"]:
        if not set(req["source_refs"]) <= sources.keys():
            raise ContractError("unknown source")
        if not set(req["depends_on"]) <= requirements or req["id"] in req["depends_on"]:
            raise ContractError("unknown or self dependency")
        orders[req["id"]] = {"id": req["id"], "goal": req["goal"],
            "requirement_refs": [req["id"]], "acceptance": req["acceptance"],
            "source_refs": req["source_refs"], "depends_on": req["depends_on"],
            "criteria": [{"id": f"AC{i:03d}", "text": text} for i, text in enumerate(req["acceptance"], 1)],
            "capabilities": ["read_provided_snapshots", "return_json"]}
    remaining = set(orders)
    levels = []
    while remaining:
        ready = sorted(t for t in remaining if not set(orders[t]["depends_on"]) & remaining)
        if not ready:
            raise ContractError("dependency cycle")
        levels.append(ready)
        remaining.difference_update(ready)
    content = {"version": "1.1", "prd": prd, "orders": orders, "sources": sources, "levels": levels}
    return {**content, "contract_hash": digest(content)}


class Coordinator:
    """SQLite transactions serialize host mutations; host-owned state is trusted."""

    def __init__(self, compiled, output):
        expected = {k: v for k, v in compiled.items() if k != "contract_hash"}
        if digest(expected) != compiled.get("contract_hash"):
            raise ContractError("compiled contract tampered")
        if compiled.get("version") != "1.1":
            raise ContractError("fresh v1.1 contract required; old runs remain historical evidence")
        check_sources(compiled)
        self._bundle = copy.deepcopy(compiled)
        self.out = Path(output).absolute()
        if any(p.is_symlink() for p in (self.out, *self.out.parents)):
            raise ContractError("symlink output root")
        self.out.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(safe_path(self.out, "run.sqlite"), timeout=10)
        self.db.execute("CREATE TABLE IF NOT EXISTS run (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT data FROM run WHERE id=1").fetchone()
            if row:
                if json.loads(row[0])["contract_hash"] != compiled["contract_hash"]:
                    raise ContractError("run contract mismatch")
            else:
                state = {"contract_hash": compiled["contract_hash"], "tasks": {
                    tid: {"status": "pending", "attempt": 0} for tid in compiled["orders"]},
                    "requests": {}, "events": []}
                self.db.execute("INSERT INTO run VALUES(1,?)", (json.dumps(state),))

    @property
    def bundle(self):
        return copy.deepcopy(self._bundle)

    def close(self):
        self.db.close()

    def _load(self):
        return json.loads(self.db.execute("SELECT data FROM run WHERE id=1").fetchone()[0])

    def _save(self, state, event, detail, request=None):
        state["events"].append({"seq": len(state["events"]) + 1, "at": time.time(),
                                "kind": event, "detail": detail})
        payload = json.dumps(state, ensure_ascii=False)
        if request is not None and request['expires'] <= time.time():
            raise ContractError("request expired before commit")
        self.db.execute("UPDATE run SET data=? WHERE id=1", (payload,))
        if request is not None and request['expires'] <= time.time():
            raise ContractError("request expired during commit preparation")

    def _artifact(self, task):
        path = safe_path(self.out, task["artifact_path"])
        data = json.loads(path.read_text())
        if digest(data) != task["artifact_hash"]:
            raise ContractError("artifact changed since submission")
        return data

    def _integrity(self, state, tid, seen=None):
        seen = set() if seen is None else seen
        if tid in seen:
            return
        seen.add(tid)
        task = state["tasks"][tid]
        if task["status"] != "accepted":
            raise ContractError(f"dependency {tid} not accepted")
        data = self._artifact(task)
        self._verify_claims(tid, data)
        self._delivery_integrity(state['requests'][data['request_id']])
        self._isolation_integrity(state['requests'][data['request_id']])
        review = task["review"]
        self._delivery_integrity(state['requests'][review['request_id']])
        self._isolation_integrity(state['requests'][review['request_id']])
        if review["artifact_hash"] != task["artifact_hash"] or review["verdict"] != "accept":
            raise ContractError("review no longer matches artifact")
        for dep in self._bundle["orders"][tid]["depends_on"]:
            self._integrity(state, dep, seen)
            if task["dependency_hashes"][dep] != state["tasks"][dep]["artifact_hash"]:
                raise ContractError("dependency artifact changed")

    def dispatch(self, tid, role="worker", ttl=900):
        if tid not in self._bundle["orders"] or role not in ("worker", "reviewer"):
            raise ContractError("unknown task or role")
        if not 1 <= ttl <= 3600:
            raise ContractError("lease must be 1..3600 seconds")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            state = self._load()
            task = state["tasks"][tid]
            order = self._bundle["orders"][tid]
            dependencies = {}
            for dep in order["depends_on"]:
                self._integrity(state, dep)
                dependencies[dep] = {"artifact_hash": state["tasks"][dep]["artifact_hash"],
                                     "artifact": self._artifact(state["tasks"][dep])}
            wanted = "running" if role == "worker" else "reviewing"
            allowed = ("pending", "rejected", "failed") if role == "worker" else ("submitted",)
            if task["status"] not in allowed:
                raise ContractError("task not ready for this role")
            if role == "worker":
                if task["attempt"] >= self._bundle["prd"]["max_attempts"]:
                    raise ContractError("attempt budget exhausted")
                task["attempt"] += 1
            else:
                self._verify_claims(tid, self._artifact(task))
            request_id = secrets.token_hex(16)
            envelope = {"request_id": request_id, "task_id": tid, "role": role,
                "contract_hash": self._bundle["contract_hash"], "attempt": task["attempt"],
                "order": order, "dependencies": dependencies,
                "product_context": {k: self._bundle["prd"][k] for k in ("id", "title", "purpose", "audience", "scope")},
                "sources": {s: self._bundle["sources"][s] for s in order["source_refs"]},
                "authority": {"tools": [], "network": False, "filesystem": False,
                              "output": "json_response_only", "enforcement":
                              self._bundle['prd'].get('runtime_policy', 'host_trust_boundary')}}
            if role == "reviewer":
                envelope.update(artifact=self._artifact(task), artifact_hash=task["artifact_hash"])
            envelope["input_hash"] = digest(envelope)
            from .runtime import delivery_payload
            packet = delivery_payload(envelope)
            rel = f"deliveries/{request_id}.txt"
            target = safe_path(self.out, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as handle:
                handle.write(packet['prompt'])
            state["requests"][request_id] = {"envelope": copy.deepcopy(envelope), "expires": time.time() + ttl,
                "host_agent_id": None, "consumed": False,
                "delivery": {"prompt_path": rel, "prompt_sha256": packet['prompt_sha256'],
                             "schema_sha256": packet['schema_sha256'], "receipt": None}}
            task["status"] = wanted
            task["active_request"] = request_id
            task["dependency_hashes"] = {d: a["artifact_hash"] for d, a in dependencies.items()}
            self._save(state, "dispatch", {"request_id": request_id, "task_id": tid, "role": role})
            return copy.deepcopy(envelope)

    def _delivery_integrity(self, request, require_receipt=True):
        delivery = request['delivery']
        raw = safe_path(self.out, delivery['prompt_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != delivery['prompt_sha256']:
            raise ContractError("delivered prompt changed")
        receipt = delivery['receipt']
        if require_receipt and (not receipt or receipt['host_agent_id'] != request['host_agent_id']
                                or receipt['prompt_sha256'] != delivery['prompt_sha256']):
            raise ContractError("matching host delivery receipt required")
        return raw.decode('utf-8')

    def delivery(self, request_id):
        state = self._load()
        request = self._request(state, request_id)
        return {**copy.deepcopy(request['delivery']),
                "prompt": self._delivery_integrity(request, require_receipt=False)}

    def record_delivery(self, request_id, host_agent_id, prompt_sha256, receipt_id):
        """Trusted host attests the exact visible prompt sent, not remote model internals."""
        if not isinstance(receipt_id, str) or not 1 <= len(receipt_id) <= 200:
            raise ContractError("host delivery receipt ID required")
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            state = self._load()
            request = self._request(state, request_id)
            if not request['host_agent_id'] or request['host_agent_id'] != host_agent_id:
                raise ContractError("delivery identity mismatch")
            self._delivery_integrity(request, require_receipt=False)
            if prompt_sha256 != request['delivery']['prompt_sha256']:
                raise ContractError("delivery prompt hash mismatch")
            if request['delivery']['receipt'] is not None:
                raise ContractError("delivery already recorded")
            request['delivery']['receipt'] = {"host_agent_id": host_agent_id,
                "prompt_sha256": prompt_sha256, "receipt_id": receipt_id,
                "at": time.time(), "kind": "trusted_host_reported_send"}
            self._save(state, 'delivered', {"request_id": request_id,
                "prompt_sha256": prompt_sha256, "receipt_id": receipt_id})

    def bind(self, request_id, host_agent_id):
        """Trusted host calls this using the ID returned by its runtime, never worker JSON."""
        if not isinstance(host_agent_id, str) or not host_agent_id.strip() or len(host_agent_id) > 200:
            raise ContractError("invalid host identity")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            state = self._load()
            request = self._request(state, request_id)
            if request["host_agent_id"] is not None:
                raise ContractError("request already bound")
            env = request["envelope"]
            producer = state["tasks"][env["task_id"]].get("producer")
            if env["role"] == "reviewer" and producer == host_agent_id:
                raise ContractError("producer cannot review own artifact")
            # A runtime identity has exactly one role for this run.
            for other in state["requests"].values():
                if other["host_agent_id"] == host_agent_id and other["envelope"]["role"] != env["role"]:
                    raise ContractError("runtime identity cannot switch roles")
            if env['role'] == 'worker' and any(
                other['host_agent_id'] == host_agent_id and other['envelope']['task_id'] != env['task_id']
                for other in state['requests'].values()):
                raise ContractError("worker identity must be distinct across work orders")
            request["host_agent_id"] = host_agent_id
            self._save(state, "host_binding", {"request_id": request_id, "host_agent_id": host_agent_id})

    def _request(self, state, request_id):
        request = state["requests"].get(request_id)
        if not request or request["consumed"] or request["expires"] <= time.time():
            raise ContractError("unknown, consumed or expired request")
        env = request["envelope"]
        if state["tasks"][env["task_id"]].get("active_request") != request_id:
            raise ContractError("superseded request")
        return request

    def fail(self, request_id, reason):
        """Host reports runtime failure/timeout. Explicit retry creates a new request."""
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            state = self._load()
            req = state["requests"].get(request_id)
            if not req or req["consumed"]:
                raise ContractError("unknown or consumed request")
            tid = req["envelope"]["task_id"]
            if state["tasks"][tid].get("active_request") != request_id:
                raise ContractError("superseded request")
            req["consumed"] = True
            state["tasks"][tid]["status"] = "failed" if req["envelope"]["role"] == "worker" else "submitted"
            self._save(state, "runtime_failure", {"request_id": request_id, "reason": str(reason)[:1000]})

    def _verify_claims(self, tid, response):
        check_sources(self._bundle)
        validate(response, "result")
        order = self._bundle["orders"][tid]
        unique(response["claims"])
        coverage = set()
        for claim in response["claims"]:
            refs = set(claim["requirement_refs"])
            if not refs <= set(order["requirement_refs"]):
                raise ContractError("claim cites unknown requirement")
            coverage.update(refs)
            for evidence in claim["evidence"]:
                sid = evidence["source_id"]
                if sid not in order["source_refs"]:
                    raise ContractError("source not granted to task")
                source = self._bundle["sources"][sid]
                # JSON Schema integers include integral JSON numbers such as 1.0.
                start, end = int(evidence["start_line"]), int(evidence["end_line"])
                if not 1 <= start <= end <= len(source["lines"]):
                    raise ContractError("evidence line range invalid")
                if evidence["source_sha256"] != source["sha256"]:
                    raise ContractError("source hash mismatch")
                if evidence["quote"] != "\n".join(source["lines"][start - 1:end]):
                    raise ContractError("quote differs from pinned source")
        if coverage != set(order["requirement_refs"]):
            raise ContractError("requirement evidence coverage incomplete")

    def record_isolation(self, request_id, host_agent_id, evidence):
        """Host-only readiness attestation, never an untrusted response field."""
        if self._bundle['prd'].get('runtime_policy', 'host_trust_boundary') == 'host_trust_boundary':
            raise ContractError('advisory contract does not require isolation attestation')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            state = self._load()
            request = self._request(state, request_id)
            if request['host_agent_id'] != host_agent_id or not host_agent_id:
                raise ContractError('isolation identity mismatch')
            if 'isolation' in request:
                raise ContractError('isolation already recorded')
            request['isolation'] = {'evidence': copy.deepcopy(evidence), 'sha256': digest(evidence)}
            self._isolation_integrity(request)
            self._save(state, 'isolation_ready', {'request_id': request_id,
                'host_agent_id': host_agent_id, 'sha256': digest(evidence)}, request=request)

    def _isolation_integrity(self, request):
        required = self._bundle['prd'].get('runtime_policy', 'host_trust_boundary')
        if required == 'host_trust_boundary':
            return
        record = request.get('isolation', {})
        if not isinstance(record, dict) or not isinstance(record.get('evidence'), dict):
            raise ContractError('required isolation attestation missing or inconsistent')
        evidence = record['evidence']
        expected_fields = {'profile', 'pid', 'prompt_sha256', 'worker_sha256',
                           'bootstrap_sha256', 'policy_sha256', 'limits'}
        if (set(evidence) != expected_fields or evidence.get('profile') != required
                or type(evidence.get('pid')) is not int or evidence['pid'] <= 0
                or not request['host_agent_id']
                or not request['host_agent_id'].startswith(f"seccomp:{evidence['pid']}:")
                or evidence.get('prompt_sha256') != request['delivery']['prompt_sha256']
                or record.get('sha256') != digest(evidence)):
            raise ContractError('required isolation attestation missing or inconsistent')
        import re
        for name in ('worker_sha256', 'bootstrap_sha256', 'policy_sha256'):
            if not isinstance(evidence[name], str) or not re.fullmatch('[0-9a-f]{64}', evidence[name]):
                raise ContractError('invalid isolation hash')
        from .isolation import Limits
        from ._restricted_worker import policy_hash
        try:
            if not isinstance(evidence['limits'], dict) or set(evidence['limits']) != set(Limits.__dataclass_fields__):
                raise ValueError('incomplete limits')
            Limits(**evidence['limits'])
            if policy_hash(evidence['limits']) != evidence['policy_sha256']:
                raise ValueError('policy hash mismatch')
        except (TypeError, ValueError) as exc:
            raise ContractError('invalid isolation limits or policy') from exc

    def receive(self, request_id, host_agent_id, response):
        """Host-only import API; data-plane workers cannot authenticate themselves."""
        bound_json(response)
        if len(json.dumps(response, allow_nan=False).encode()) > 500_000:
            raise ContractError("response budget exceeded")
        created = None
        try:
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                state = self._load()
                request = self._request(state, request_id)
                if not request["host_agent_id"] or request["host_agent_id"] != host_agent_id:
                    raise ContractError("host identity mismatch")
                self._delivery_integrity(request)
                self._isolation_integrity(request)
                env = request["envelope"]
                tid, role = env["task_id"], env["role"]
                task = state["tasks"][tid]
                validate(response, "result" if role == "worker" else "review")
                for key in ("request_id", "task_id", "contract_hash", "input_hash"):
                    if response[key] != env[key]:
                        raise ContractError(f"response {key} mismatch")
                for dep in self._bundle["orders"][tid]["depends_on"]:
                    self._integrity(state, dep)
                if role == "worker":
                    self._verify_claims(tid, response)
                    self._request(state, request_id)
                    rel = f"artifacts/{tid}/attempt-{task['attempt']}.json"
                    target = safe_path(self.out, rel)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Exclusive create prevents silent replacement and stale-file reuse.
                    with target.open("x", encoding="utf-8") as handle:
                        created = target
                        json.dump(response, handle, ensure_ascii=False, indent=2)
                    task.update(status="submitted", artifact_path=rel, artifact_hash=digest(response),
                                producer=host_agent_id)
                    task.pop("review", None)
                    task.pop("reviewer", None)
                else:
                    artifact = self._artifact(task)
                    self._verify_claims(tid, artifact)
                    if response["artifact_hash"] != task["artifact_hash"]:
                        raise ContractError("review artifact mismatch")
                    unique(response["checks"], "claim_id")
                    if {c["claim_id"] for c in response["checks"]} != {c["id"] for c in artifact["claims"]}:
                        raise ContractError("review must check every claim exactly once")
                    if host_agent_id == task["producer"]:
                        raise ContractError("self review forbidden")
                    unique(response['criteria'], 'criterion_id')
                    if {a['criterion_id'] for a in response['criteria']} != {a['id'] for a in self._bundle['orders'][tid]['criteria']}:
                        raise ContractError("review must cover every acceptance criterion")
                    claims = {a['id'] for a in artifact['claims']}
                    claim_checks = {a['claim_id']: a['supported'] for a in response['checks']}
                    for criterion in response['criteria']:
                        refs = set(criterion['claim_refs'])
                        if not refs <= claims or (criterion['satisfied'] and not refs):
                            raise ContractError("criterion must reference existing supporting claims")
                        if criterion['satisfied'] and not all(claim_checks[r] for r in refs):
                            raise ContractError("criterion refers to unsupported claim")
                    if response['acceptance_satisfied'] != all(a['satisfied'] for a in response['criteria']):
                        raise ContractError("acceptance summary conflicts with criterion decisions")
                    supported = all(c["supported"] for c in response["checks"])
                    if response["verdict"] == "accept" and (not supported or not response["acceptance_satisfied"]):
                        raise ContractError("accept verdict conflicts with unsupported claims")
                    task.update(status="accepted" if response["verdict"] == "accept" else "rejected",
                                reviewer=host_agent_id, review=response)
                self._request(state, request_id)
                request["consumed"] = True
                request["response"] = response
                request["response_hash"] = digest(response)
                self._save(state, "received", {"request_id": request_id, "task_id": tid,
                    "role": role, "host_agent_id": host_agent_id, "response_hash": digest(response),
                    "status": task["status"]}, request=request)
                return task["status"]
        except BaseException as exc:
            if created is not None:
                try:
                    created.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    exc.add_note(f"Unaccepted orphan artifact needs host cleanup: {cleanup_error}")
            raise

    def report(self):
        state = self._load()
        errors = {}
        for tid, task in state["tasks"].items():
            if task["status"] == "accepted":
                try:
                    self._integrity(state, tid)
                except (ContractError, OSError, ValueError) as exc:
                    errors[tid] = str(exc)
        all_accepted = all(t["status"] == "accepted" for t in state["tasks"].values())
        status = "accepted_host_reviewed" if all_accepted and not errors else "incomplete"
        return {**state, "product_status": status, "integrity_errors": errors,
            "scope": "Pinned-corpus research; host-authenticated review. Isolation applies only to the selected runtime profile.",
            "runtime_policy": self._bundle['prd'].get('runtime_policy', 'host_trust_boundary'),
            "traceability": {tid: {"requirement_refs": order["requirement_refs"],
                "acceptance": order["acceptance"], "artifact_hash": state["tasks"][tid].get("artifact_hash"),
                "reviewer": state["tasks"][tid].get("reviewer")} for tid, order in self._bundle["orders"].items()}}
