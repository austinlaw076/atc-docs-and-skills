import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
import copy
import subprocess
import sys
import time
from dataclasses import asdict
from unittest.mock import patch

from atc10.core import ContractError, Coordinator, compile_prd, digest
from atc10.isolation import IsolatedPythonRuntime, Limits
from atc10.runtime import render_prompt, HostDispatcher, CallbackHostRuntime

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = (ROOT/'examples/atc11/fixture_worker.py').read_text()


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    async def execute(self, source, *, envelope=None, limits=None):
        path = self.root/'worker.py'
        path.write_text(source)
        runtime = IsolatedPythonRuntime(path, limits=limits)
        env = envelope or {'test': 'stdin snapshot'}
        agent = await runtime.start(instructions='fixture', envelope=env, response_schema={},
                                    prompt=render_prompt('fixture', env, {}))
        ready = runtime.attestation(agent)
        result = await runtime.collect(agent, timeout_seconds=10)
        self.assertFalse(runtime.active)
        return result, ready

    def test_in_memory_json_and_readiness(self):
        result, ready = asyncio.run(self.execute("def run(p): return {'value':p['envelope']['test']}"))
        self.assertEqual(result, {'value':'stdin snapshot'})
        self.assertEqual(ready['profile'], 'seccomp_python_stdio_v1')
        self.assertGreater(ready['pid'], 0)

    def test_filesystem_read_write_denied(self):
        canary = self.root/'secret'
        canary.write_text('private canary')
        source = '''def run(p):
    results = {}
    for mode in ['r', 'w', 'a']:
        try:
            open(p['envelope']['path'], mode)
            results[mode] = 'allowed'
        except PermissionError:
            results[mode] = 'denied'
    return results
'''
        result, _ = asyncio.run(self.execute(source, envelope={'path':str(canary)}))
        self.assertEqual(result, dict.fromkeys(['r','w','a'], 'denied'))
        self.assertEqual(canary.read_text(), 'private canary')

    def test_network_and_process_tools_denied(self):
        source = '''def run(p):
    import socket, os, subprocess
    result = {}
    for name, action in [('tcp', lambda:socket.socket()),
                         ('udp', lambda:socket.socket(type=socket.SOCK_DGRAM)),
                         ('unix', lambda:socket.socket(socket.AF_UNIX)),
                         ('fork', os.fork),
                         ('tool', lambda:subprocess.run(['/bin/true']))]:
        try:
            action()
            result[name] = 'allowed'
        except PermissionError:
            result[name] = 'denied'
    return result
'''
        result, _ = asyncio.run(self.execute(source))
        self.assertEqual(result, dict.fromkeys(['tcp','udp','unix','fork','tool'], 'denied'))

    def test_wall_timeout_terminates(self):
        with self.assertRaises(TimeoutError):
            asyncio.run(self.execute('def run(p):\n while True: pass', limits=Limits(wall_seconds=0.5)))

    def test_stdout_budget(self):
        with self.assertRaisesRegex(ContractError, 'output budget'):
            asyncio.run(self.execute("def run(p): return {'x':'a'*10000}", limits=Limits(stdout_bytes=500)))

    def test_large_valid_output_is_not_truncated(self):
        result,_=asyncio.run(self.execute("def run(p): return {'x':'a'*400000}"))
        self.assertEqual(len(result['x']),400000)

    def test_alternate_syscall_abi_cannot_open(self):
        source='''def run(p):
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True)
    value=libc.syscall(0x40000002,b'/etc/hostname',0)
    return {'return':value,'errno':ctypes.get_errno()}
'''
        try:
            result,_=asyncio.run(self.execute(source))
        except ContractError as exc:
            self.assertIn('exited -31',str(exc))  # SIGSYS: wrong ABI killed.
        else:
            self.assertEqual(result['return'],-1)
            self.assertIn(result['errno'],(1,38))

    def test_clean_environment(self):
        os.environ['ATC_TEST_SECRET'] = 'must not inherit'
        try:
            result, _ = asyncio.run(self.execute("def run(p):\n import os\n return {'secret':os.getenv('ATC_TEST_SECRET')}"))
        finally:
            del os.environ['ATC_TEST_SECRET']
        self.assertEqual(result, {'secret':None})

    def test_raw_syscalls_cannot_bypass_python_wrappers(self):
        canary = self.root/'native-secret'
        canary.write_text('native canary')
        source = '''def run(p):
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    path = p['envelope']['path'].encode()
    how = ctypes.create_string_buffer(24)
    calls = {'open':(2, path, 0), 'openat':(257, -100, path, 0),
             'openat2':(437, -100, path, ctypes.byref(how), 24),
             'ptrace':(101, 16, p['envelope']['parent'], 0, 0),
             'process_vm_readv':(310, p['envelope']['parent'], 0, 0, 0, 0, 0),
             'kill_parent_probe':(62, p['envelope']['parent'], 0),
             'prctl':(157, 38, 0, 0, 0, 0), 'seccomp':(317, 1, 0, 0),
             'execve':(59, b'/bin/true', 0, 0)}
    result = {}
    for name, args in calls.items():
        ctypes.set_errno(0)
        value = libc.syscall(*args)
        result[name] = [value, ctypes.get_errno()]
    return result
'''
        result, _ = asyncio.run(self.execute(source, envelope={'path':str(canary),'parent':os.getpid()}))
        for name, value in result.items():
            self.assertEqual(value, [-1,1], name)
        self.assertEqual(canary.read_text(), 'native canary')

    def test_paths_and_mutations_denied(self):
        canary = self.root/'canary'
        canary.write_text('unchanged')
        link = self.root/'link'
        link.symlink_to(canary)
        source = '''def run(p):
    import os
    result = {}
    for name, action in [('symlink_read',lambda:open(p['envelope']['link'])),
                         ('traversal',lambda:open(p['envelope']['traversal'])),
                         ('unlink',lambda:os.unlink(p['envelope']['path'])),
                         ('mkdir',lambda:os.mkdir(p['envelope']['path']+'dir')),
                         ('symlink_create',lambda:os.symlink('/etc/hostname',p['envelope']['path']+'new'))]:
        try:
            action()
            result[name]='allowed'
        except PermissionError:
            result[name]='denied'
    return result
'''
        result, _ = asyncio.run(self.execute(source,envelope={'path':str(canary),'link':str(link),
            'traversal':str(self.root/'..'/self.root.name/'canary')}))
        self.assertTrue(all(v=='denied' for v in result.values()))
        self.assertEqual(len(result),5)
        self.assertEqual(canary.read_text(),'unchanged')

    def test_inherited_descriptor_cannot_be_mapped(self):
        canary = self.root/'fd-secret'
        canary.write_text('descriptor secret')
        fd = os.open(canary, os.O_RDONLY)
        os.set_inheritable(fd, True)
        source = '''def run(p):
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True)
    libc.mmap.restype=ctypes.c_void_p
    value=libc.mmap(None,4096,1,2,p['envelope']['fd'],0)
    return {'failed':value==ctypes.c_void_p(-1).value,'errno':ctypes.get_errno()}
'''
        try:
            result,_=asyncio.run(self.execute(source,envelope={'fd':fd}))
        finally:
            os.close(fd)
        self.assertEqual(result,{'failed':True,'errno':9})

    def test_memory_limit(self):
        with self.assertRaisesRegex(ContractError,'exited'):
            asyncio.run(self.execute("def run(p): return {'x':bytearray(1_000_000_000)}"))

    def test_cpu_limit(self):
        with self.assertRaisesRegex(ContractError,'exited'):
            asyncio.run(self.execute('def run(p):\n while True: pass',limits=Limits(cpu_seconds=1,wall_seconds=5)))

    def test_stderr_budget_and_invalid_json(self):
        with self.assertRaisesRegex(ContractError,'output budget'):
            asyncio.run(self.execute("def run(p):\n import os\n os.write(2,b'x'*20000)\n return {}"))
        with self.assertRaises(ValueError):
            asyncio.run(self.execute("def run(p):\n import os\n os.write(1,b'bad')\n return {}"))

    def test_threads_denied(self):
        source = '''def run(p):
    import threading
    try:
        threading.Thread(target=lambda:None).start()
        return {'thread':'allowed'}
    except RuntimeError:
        return {'thread':'denied'}
'''
        result,_=asyncio.run(self.execute(source))
        self.assertEqual(result,{'thread':'denied'})

    def test_module_body_is_already_restricted(self):
        marker=self.root/'marker'
        with self.assertRaises(ContractError):
            asyncio.run(self.execute(f"open({str(marker)!r},'w').write('bad')\ndef run(p): return {{}}"))
        self.assertFalse(marker.exists())

    def test_missing_library_fails_before_worker_execution(self):
        path=self.root/'worker.py';marker=self.root/'marker'
        path.write_text(f"open({str(marker)!r},'w').write('bad')\ndef run(p): return {{}}")
        runtime=IsolatedPythonRuntime(path)
        broken=self.root/'broken_bootstrap.py'
        broken.write_text(runtime.bootstrap.read_text().replace('libseccomp.so.2','lib_atc_does_not_exist.so'))
        runtime.bootstrap=broken
        with self.assertRaises(ValueError):
            asyncio.run(runtime.start(instructions='x',envelope={},response_schema={},prompt=render_prompt('x',{},{})))
        self.assertFalse(marker.exists())
        self.assertFalse(runtime.active)

    def test_failed_filter_load_never_executes_worker(self):
        path=self.root/'worker.py';marker=self.root/'marker'
        path.write_text(f"open({str(marker)!r},'w').write('bad')\ndef run(p): return {{}}")
        runtime=IsolatedPythonRuntime(path)
        broken=self.root/'filter_load_failure.py'
        broken.write_text(runtime.bootstrap.read_text().replace(
            'if lib.seccomp_load(ctx) != 0:', 'if True or lib.seccomp_load(ctx) != 0:'))
        runtime.bootstrap=broken
        with self.assertRaisesRegex(ContractError,'no enforced readiness'):
            asyncio.run(runtime.start(instructions='x',envelope={},response_schema={},prompt=render_prompt('x',{},{})))
        self.assertFalse(marker.exists())
        self.assertFalse(runtime.active)

    def test_bootstrap_requires_valid_host_ack(self):
        bootstrap=ROOT/'atc10/_restricted_worker.py'
        packet={'worker_source':"import os\nos.write(1,b'EXECUTED')\ndef run(p): return {}",
                'limits':asdict(Limits()),'prompt':'fixture','envelope':{},'response_schema':{}}
        for ack in [b'',b'{"execute":"wrong"}\n']:
            with self.subTest(ack=ack):
                completed=subprocess.run([sys.executable,'-I','-B',str(bootstrap)],
                    input=json.dumps(packet).encode()+b'\n'+ack,capture_output=True,timeout=5,
                    env={'LANG':'C.UTF-8'},close_fds=True)
                self.assertIn(b'"ready"',completed.stdout)
                self.assertNotEqual(completed.returncode,0)
                self.assertNotIn(b'EXECUTED',completed.stdout)

    def test_parent_readiness_mismatch_never_enters_payload(self):
        path=self.root/'worker.py'
        path.write_text("import os\nos.write(1,b'EXECUTED')\ndef run(p): return {}")
        class CaptureRuntime(IsolatedPythonRuntime):
            async def _stop(self,proc):
                proc.stdin.close()
                if proc.returncode is None:proc.kill()
                self.observed,_,_=await asyncio.gather(proc.stdout.read(),proc.stderr.read(),proc.wait())
        runtime=CaptureRuntime(path)
        mismatch=self.root/'mismatched_ready.py'
        mismatch.write_text(runtime.bootstrap.read_text().replace("'pid': os.getpid()", "'pid': 0"))
        runtime.bootstrap=mismatch
        loads=json.loads
        def slow_verify(raw,*a,**kw):
            time.sleep(0.1)  # Let a child without an acknowledgment gate execute.
            return loads(raw,*a,**kw)
        with patch('atc10.isolation.json.loads',side_effect=slow_verify):
            with self.assertRaisesRegex(ContractError,'readiness mismatch'):
                asyncio.run(runtime.start(instructions='x',envelope={},response_schema={},prompt=render_prompt('x',{},{})))
        self.assertNotIn(b'EXECUTED',runtime.observed)
        self.assertFalse(runtime.active)

    def test_invalid_limits_and_prompt(self):
        for kw in [{'cpu_seconds':True},{'cpu_seconds':0},{'memory_bytes':1},
                   {'wall_seconds':float('nan')},{'wall_seconds':61},{'stdout_bytes':500001}]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):Limits(**kw)
        path=self.root/'worker.py';path.write_text('def run(p): return {}')
        runtime=IsolatedPythonRuntime(path)
        with self.assertRaisesRegex(ContractError,'prompt differs'):
            asyncio.run(runtime.start(instructions='x',envelope={},response_schema={},prompt='not the prompt'))
        self.assertFalse(runtime.active)

    def coordinator(self):
        prd=json.loads((ROOT/'examples/atc10/prd.json').read_text())
        prd['runtime_policy']='seccomp_python_stdio_v1'
        c=Coordinator(compile_prd(prd,ROOT/'examples/atc10'),self.root/'run')
        self.addCleanup(c.close)
        return c

    def test_strict_dispatch_rejects_advisory_runtime(self):
        c=self.coordinator()
        async def forbidden(**kw):
            self.fail('advisory runtime must not start')
        runtime=CallbackHostRuntime(forbidden,forbidden)
        with self.assertRaisesRegex(ContractError,'no advisory fallback'):
            asyncio.run(HostDispatcher(c,runtime).execute('R1'))
        self.assertEqual(c.report()['tasks']['R1']['status'],'failed')

    def test_strict_receive_requires_attestation(self):
        c=self.coordinator();e=c.dispatch('R1');agent='seccomp:123:fixture'
        c.bind(e['request_id'],agent)
        c.record_delivery(e['request_id'],agent,c.delivery(e['request_id'])['prompt_sha256'],'fixture')
        scope={};exec(FIXTURE,scope)
        with self.assertRaisesRegex(ContractError,'isolation attestation'):
            c.receive(e['request_id'],agent,scope['run']({'envelope':e}))

    def test_strict_workflow_and_attestation_tamper(self):
        c=self.coordinator();path=self.root/'fixture.py';path.write_text(FIXTURE)
        runtime=IsolatedPythonRuntime(path)
        report=asyncio.run(HostDispatcher(c,runtime).run())
        self.assertEqual(report['product_status'],'accepted_host_reviewed')
        self.assertEqual(report['runtime_policy'],'seccomp_python_stdio_v1')
        self.assertFalse(runtime.active)
        self.assertEqual(len({r['host_agent_id'] for r in report['requests'].values()}),6)
        self.assertTrue(all('isolation' in r for r in report['requests'].values()))
        state=c._load();request=next(iter(state['requests'].values()))
        request['isolation']['evidence']['prompt_sha256']='0'*64
        request['isolation']['sha256']=digest(request['isolation']['evidence'])
        with c.db:c._save(state,'test_tamper',{})
        self.assertEqual(c.report()['product_status'],'incomplete')
        self.assertTrue(c.report()['integrity_errors'])
        with self.assertRaises(ContractError):c.dispatch('R3')

    def test_cancellation_terminates_bound_child(self):
        c=self.coordinator();path=self.root/'busy.py';path.write_text('def run(p):\n while True: pass')
        runtime=IsolatedPythonRuntime(path)
        async def run():
            task=asyncio.create_task(HostDispatcher(c,runtime).execute('R1',ttl=10))
            for _ in range(200):
                if runtime.active:break
                await asyncio.sleep(0.005)
            self.assertTrue(runtime.active)
            pid=next(iter(runtime.active.values()))[0].pid
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertFalse(runtime.active)
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
        asyncio.run(run())
        self.assertEqual(c.report()['tasks']['R1']['status'],'failed')

    def test_bad_isolation_evidence_rolls_back(self):
        from atc10.runtime import WORKER_RULES
        c=self.coordinator();e=c.dispatch('R1')
        path=self.root/'fixture.py';path.write_text(FIXTURE)
        runtime=IsolatedPythonRuntime(path)
        async def run():
            schema=json.loads((ROOT/'schemas/result_v1_1.schema.json').read_text())
            agent=await runtime.start(instructions=WORKER_RULES,envelope=e,response_schema=schema,
                                      prompt=c.delivery(e['request_id'])['prompt'])
            evidence=runtime.attestation(agent)
            c.bind(e['request_id'],agent)
            c.record_delivery(e['request_id'],agent,evidence['prompt_sha256'],'fixture')
            for change in [{'profile':'advisory'}, {'pid':0}, {'worker_sha256':'bad'},
                           {'limits':{}}, {'policy_sha256':'0'*64}, {'prompt_sha256':'0'*64}]:
                bad=copy.deepcopy(evidence);bad.update(change)
                with self.subTest(change=change),self.assertRaises(ContractError):
                    c.record_isolation(e['request_id'],agent,bad)
                self.assertNotIn('isolation',c._load()['requests'][e['request_id']])
            c.record_isolation(e['request_id'],agent,evidence)
            with self.assertRaisesRegex(ContractError,'already recorded'):
                c.record_isolation(e['request_id'],agent,evidence)
            response=await runtime.collect(agent,timeout_seconds=10)
            self.assertEqual(c.receive(e['request_id'],agent,response),'submitted')
        asyncio.run(run())
