"""Fail-closed local Python Runtime; no provider/network integration."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass

from .core import ContractError
from ._restricted_worker import PROFILE, policy_hash
from .runtime import render_prompt


@dataclass(frozen=True)
class Limits:
    memory_bytes: int = 268_435_456
    cpu_seconds: int = 5
    wall_seconds: float = 10
    stdout_bytes: int = 500_000
    stderr_bytes: int = 16_384

    def __post_init__(self):
        for name, low, high in [('memory_bytes', 67_108_864, 536_870_912),
                                ('cpu_seconds', 1, 30), ('stdout_bytes', 100, 500_000),
                                ('stderr_bytes', 100, 65_536)]:
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError('invalid limit ' + name)
        if type(self.wall_seconds) not in (int, float) or not 0.05 <= self.wall_seconds <= 60:
            raise ValueError('invalid wall_seconds')


class IsolatedPythonRuntime:
    """Host selects a Python file defining run(packet). Requests never select code.

    Python/bootstrap imports occur before isolation. Worker module execution and
    run() occur after enforcement; later filesystem-dependent imports fail.
    Only stdin snapshots are available, even if their source paths are named.
    """
    isolation_profile = PROFILE

    def __init__(self, worker_path, *, limits=None):
        self.limits = limits or Limits()
        with Path(worker_path).open('rb') as handle:
            source = handle.read(1_000_001)
        if len(source) > 1_000_000:
            raise ContractError('worker program too large')
        self.source = source.decode('utf-8')
        self.bootstrap = Path(__file__).with_name('_restricted_worker.py')
        self.active = {}

    async def _stop(self, proc):
        proc.stdin.close()
        if proc.returncode is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        async def discard(stream):
            while await stream.read(65_536):
                pass
        # A paused asyncio pipe can otherwise keep wait() pending after kill.
        await asyncio.gather(discard(proc.stdout), discard(proc.stderr), proc.wait())
        try:
            await proc.stdin.wait_closed()
        except (BrokenPipeError, ConnectionResetError):
            pass

    async def start(self, *, instructions, envelope, response_schema, prompt):
        if prompt != render_prompt(instructions, envelope, response_schema):
            raise ContractError('runtime prompt differs from persisted delivery')
        packet = {'worker_source': self.source, 'limits': asdict(self.limits),
                  'prompt': prompt, 'envelope': envelope, 'response_schema': response_schema}
        raw = json.dumps(packet, ensure_ascii=False, allow_nan=False).encode()
        if len(raw) > 8_000_000:
            raise ContractError('startup packet too large')
        work = tempfile.TemporaryDirectory(prefix='atc-restricted-')
        proc = None
        started = time.monotonic()
        try:
            async with asyncio.timeout(min(5, self.limits.wall_seconds)):
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, '-I', '-B', str(self.bootstrap),
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE, cwd=work.name,
                    env={'LANG': 'C.UTF-8'}, close_fds=True, start_new_session=True,
                    limit=2048)
                proc.stdin.write(raw + b'\n')
                await proc.stdin.drain()
                line = await proc.stdout.readline()
                try:
                    ready = json.loads(line)['ready']
                except (ValueError, KeyError, TypeError) as exc:
                    raise ContractError('restricted runtime unavailable: no enforced readiness') from exc
                expected = {'profile': PROFILE, 'pid': proc.pid,
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'worker_sha256': hashlib.sha256(self.source.encode()).hexdigest(),
                    'bootstrap_sha256': hashlib.sha256(self.bootstrap.read_bytes()).hexdigest(),
                    'policy_sha256': policy_hash(asdict(self.limits)),
                    'limits': asdict(self.limits)}
                if ready != expected:
                    raise ContractError('restricted runtime readiness mismatch')
                token = hashlib.sha256(json.dumps(ready, sort_keys=True).encode()).hexdigest()
                proc.stdin.write(json.dumps({'execute': token}).encode() + b'\n')
                await proc.stdin.drain()
                proc.stdin.close()
                await proc.stdin.wait_closed()
                identity = f'seccomp:{proc.pid}:{uuid.uuid4().hex}'
                self.active[identity] = (proc, work, started, ready)
                return identity
        except BaseException:
            if proc is not None:
                await self._stop(proc)
            work.cleanup()
            raise

    def attestation(self, identity):
        return copy.deepcopy(self.active[identity][3])

    async def terminate(self, identity):
        entry = self.active.pop(identity, None)
        if entry:
            proc, work, _, _ = entry
            try:
                await self._stop(proc)
            finally:
                work.cleanup()

    async def _read(self, stream, budget):
        result = bytearray()
        while True:
            block = await stream.read(min(65_536, budget + 1 - len(result)))
            if not block:
                return bytes(result)
            result.extend(block)
            if len(result) > budget:
                raise ContractError('restricted runtime output budget exceeded')

    async def collect(self, identity, *, timeout_seconds):
        proc, _, started, _ = self.active[identity]
        remaining = min(timeout_seconds, self.limits.wall_seconds - (time.monotonic() - started))
        tasks = [asyncio.create_task(self._read(proc.stdout, self.limits.stdout_bytes)),
                 asyncio.create_task(self._read(proc.stderr, self.limits.stderr_bytes)),
                 asyncio.create_task(proc.wait())]
        try:
            async with asyncio.timeout(max(0, remaining)):
                out, err, code = await asyncio.gather(*tasks)
            if code != 0:
                raise ContractError(f'restricted worker exited {code}: {err[:500].decode(errors="replace")}')
            result = json.loads(out)
            if not isinstance(result, dict):
                raise ContractError('restricted worker must return one JSON object')
            return result
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.terminate(identity)
