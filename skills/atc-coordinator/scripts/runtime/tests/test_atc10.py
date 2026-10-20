import asyncio
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from atc10.core import ContractError, Coordinator, compile_prd, digest
from atc10.runtime import CallbackHostRuntime, HostDispatcher, render_prompt

ROOT = Path(__file__).resolve().parent.parent


class ATC10Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prd = json.loads((ROOT/'examples/atc10/prd.json').read_text())
        self.bundle = compile_prd(self.prd, ROOT/'examples/atc10')
        self.c = Coordinator(self.bundle, Path(self.tmp.name)/'run')
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.c.close)

    def bind(self, request_id, agent):
        self.c.bind(request_id, agent)
        packet = self.c.delivery(request_id)
        self.c.record_delivery(request_id, agent, packet['prompt_sha256'], 'unit-fixture-' + request_id)

    def result(self, env):
        sid = next(iter(env['sources']))
        source = env['sources'][sid]
        line = next(i for i, s in enumerate(source['lines'], 1) if s.strip())
        return {**{k:env[k] for k in ('request_id','task_id','contract_hash','input_hash')},
                'claims':[{'id':'C1','text':'The source document identifies its test report version.',
                  'requirement_refs':[env['task_id']], 'evidence':[{'source_id':sid,
                   'source_sha256':source['sha256'],'start_line':line,'end_line':line,
                   'quote':source['lines'][line-1]}]}], 'limitations':['Synthetic unit-test result, not live research.']}

    def review(self, env, accept=True):
        return {**{k:env[k] for k in ('request_id','task_id','contract_hash','input_hash','artifact_hash')},
          'verdict':'accept' if accept else 'reject','acceptance_satisfied':accept,
          'criteria':[{'criterion_id':c['id'],'satisfied':accept,'claim_refs':[a['id'] for a in env['artifact']['claims']] if accept else [],'reason':'Synthetic unit fixture for criterion control.'} for c in env['order']['criteria']],
          'checks':[{'claim_id':c['id'],'supported':accept,'reason':'Unit fixture checks workflow control only.'} for c in env['artifact']['claims']],
          'summary':'Synthetic reviewer fixture, not an independent semantic evaluation.'}

    def submit(self, tid='R1', producer='worker-1'):
        e=self.c.dispatch(tid)
        self.bind(e['request_id'],producer)
        self.c.receive(e['request_id'],producer,self.result(e))
        return e

    def accept(self, tid='R1', producer='worker-1'):
        self.submit(tid, producer)
        e=self.c.dispatch(tid,'reviewer')
        self.bind(e['request_id'],'reviewer-1')
        self.c.receive(e['request_id'],'reviewer-1',self.review(e))
        return e

    def test_prd_decomposes(self):
        self.assertEqual(self.bundle['levels'],[['R1','R2'],['R3']])
        self.assertEqual(len(self.bundle['orders']),3)

    def test_unknown_prd_field(self):
        self.prd['tools']=['shell']
        with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_duplicate_requirement(self):
        self.prd['requirements'].append(copy.deepcopy(self.prd['requirements'][0]))
        with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_cycle(self):
        self.prd['requirements'][0]['depends_on']=['R3']
        with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_unknown_dependency(self):
        self.prd['requirements'][0]['depends_on']=['UNKNOWN']
        with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_unknown_source(self):
        self.prd['requirements'][0]['source_refs']=['UNKNOWN']
        with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_unsafe_sources(self):
        for p in ('../secret','/etc/passwd','sources/../secret','a\\b','a//b','file:secret'):
            with self.subTest(p=p):
                self.prd['sources'][0]['path']=p
                with self.assertRaises(ContractError): compile_prd(self.prd,ROOT/'examples/atc10')

    def test_compiled_tamper(self):
        self.bundle['orders']['R1']['goal']='changed'
        with self.assertRaises(ContractError): Coordinator(self.bundle,Path(self.tmp.name)/'new')

    def test_output_symlink(self):
        p=Path(self.tmp.name)/'link'; p.symlink_to(self.c.out,target_is_directory=True)
        with self.assertRaises(ContractError): Coordinator(self.bundle,p)

    def test_source_symlink(self):
        root=Path(self.tmp.name)/'src'; root.mkdir()
        (root/'link').symlink_to(ROOT/'examples/atc10/sources/test_report.md')
        self.prd['sources']=[{'id':'S1','path':'link'}]
        with self.assertRaises(ContractError): compile_prd(self.prd,root)

    def test_dependency_gate(self):
        with self.assertRaises(ContractError): self.c.dispatch('R3')

    def test_not_accepted_on_submit(self):
        self.submit()
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'submitted')
        self.assertEqual(self.c.report()['product_status'],'incomplete')

    def test_self_review(self):
        self.submit(); e=self.c.dispatch('R1','reviewer')
        with self.assertRaises(ContractError): self.bind(e['request_id'],'worker-1')

    def test_role_switch(self):
        self.accept(); e=self.c.dispatch('R2')
        with self.assertRaises(ContractError): self.bind(e['request_id'],'reviewer-1')

    def test_binding_required(self):
        e=self.c.dispatch('R1')
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'worker-1',self.result(e))

    def test_double_binding(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'worker-1')
        with self.assertRaises(ContractError): self.bind(e['request_id'],'worker-2')

    def test_identity_mismatch(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'worker-1')
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'worker-2',self.result(e))

    def test_replay(self):
        e=self.submit()
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'worker-1',self.result(e))

    def test_response_binding_fields(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w')
        for key in ('request_id','task_id','contract_hash','input_hash'):
            result=self.result(e); result[key]='R2' if key=='task_id' else 'a'*len(result[key])
            with self.subTest(key=key), self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',result)

    def test_unknown_response_fields(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w'); r=self.result(e);r['approved']=True
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',r)

    def test_bad_evidence(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w')
        for field,value in [('quote','made up'),('source_sha256','a'*64),('source_id','UNKNOWN'),('start_line',0),('end_line',999999),('start_line',True)]:
            r=self.result(e);r['claims'][0]['evidence'][0][field]=value
            with self.subTest(field=field,value=value), self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',r)

    def test_missing_evidence(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w');r=self.result(e);r['claims'][0]['evidence']=[]
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',r)

    def test_integral_json_line_numbers(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w');r=self.result(e)
        r['claims'][0]['evidence'][0]['start_line']=1.0
        r['claims'][0]['evidence'][0]['end_line']=1.0
        self.assertEqual(self.c.receive(e['request_id'],'w',r),'submitted')

    def test_unknown_requirement(self):
        e=self.c.dispatch('R1'); self.bind(e['request_id'],'w');r=self.result(e);r['claims'][0]['requirement_refs']=['R2']
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',r)

    def test_duplicate_claim_id(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'w');r=self.result(e)
        other=copy.deepcopy(r['claims'][0]);other['text']='Another different textual claim with same ID.';r['claims'].append(other)
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',r)

    def test_lease_expiry(self):
        e=self.c.dispatch('R1',ttl=1);self.bind(e['request_id'],'w')
        with patch('atc10.core.time.time',return_value=10**12), self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',self.result(e))
        self.c.fail(e['request_id'],'expired');self.assertEqual(self.c.report()['tasks']['R1']['status'],'failed')

    def test_retry_budget(self):
        for i in range(3):
            e=self.c.dispatch('R1'); self.c.fail(e['request_id'],'timeout')
        with self.assertRaises(ContractError): self.c.dispatch('R1')

    def test_stale_failed_request(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'w');self.c.fail(e['request_id'],'failure');self.c.dispatch('R1')
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'w',self.result(e))

    def test_accepted_cannot_redispatch(self):
        self.accept()
        with self.assertRaises(ContractError): self.c.dispatch('R1')

    def test_review_incomplete(self):
        self.submit();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'rv');r=self.review(e);r['checks'][0]['claim_id']='UNKNOWN'
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'rv',r)

    def test_review_acceptance_false(self):
        self.submit();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'rv');r=self.review(e);r['acceptance_satisfied']=False
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'rv',r)

    def test_review_unsupported(self):
        self.submit();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'rv');r=self.review(e);r['checks'][0]['supported']=False
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'rv',r)

    def test_wrong_review_artifact(self):
        self.submit();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'rv');r=self.review(e);r['artifact_hash']='a'*64
        with self.assertRaises(ContractError): self.c.receive(e['request_id'],'rv',r)

    def test_reviewer_reject(self):
        self.submit();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'rv')
        self.assertEqual(self.c.receive(e['request_id'],'rv',self.review(e,False)),'rejected')
        self.assertEqual(self.c.dispatch('R1')['attempt'],2)

    def test_full_flow(self):
        self.accept('R1','w1');self.accept('R2','w2');self.accept('R3','w3')
        self.assertEqual(self.c.report()['product_status'],'accepted_host_reviewed')

    def test_artifact_tamper(self):
        self.accept();task=self.c.report()['tasks']['R1'];(self.c.out/task['artifact_path']).write_text('{}')
        self.assertIn('R1',self.c.report()['integrity_errors'])
        with self.assertRaises(ContractError): self.c.dispatch('R1','reviewer')

    def test_dependency_tamper(self):
        self.accept('R1','w1');self.accept('R2','w2');task=self.c.report()['tasks']['R1'];(self.c.out/task['artifact_path']).write_text('{}')
        with self.assertRaises(ContractError): self.c.dispatch('R3')

    def test_resume(self):
        self.accept();other=Coordinator(self.bundle,self.c.out)
        self.addCleanup(other.close)
        self.assertEqual(other.report()['tasks']['R1']['status'],'accepted')
        with self.assertRaises(ContractError): other.dispatch('R1')

    def test_changed_contract_resume(self):
        self.prd['title']='Different product';b=compile_prd(self.prd,ROOT/'examples/atc10')
        with self.assertRaises(ContractError): Coordinator(b,self.c.out)

    def test_runtime_dispatcher(self):
        fixture=self
        class Runtime:
            def __init__(self): self.requests={};self.counter=0
            async def start(self,**kw):
                self.counter+=1;identity=('reviewer' if kw['envelope']['role']=='reviewer' else 'worker')+str(self.counter)
                self.requests[identity]=kw['envelope'];return identity
            async def collect(self,identity,**kw):
                e=self.requests[identity];return fixture.result(e) if e['role']=='worker' else fixture.review(e)
        report=asyncio.run(HostDispatcher(self.c,Runtime()).run())
        self.assertEqual(report['product_status'],'accepted_host_reviewed')
        self.assertEqual(len([e for e in report['events'] if e['kind']=='dispatch']),6)

    def test_runtime_error_marks_failed(self):
        class Runtime:
            async def start(self,**kw): raise RuntimeError('offline')
        with self.assertRaises(RuntimeError): asyncio.run(HostDispatcher(self.c,Runtime()).execute('R1'))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'failed')

    def test_runtime_timeout(self):
        class Runtime:
            async def start(self,**kw): await asyncio.sleep(5)
        with self.assertRaises(TimeoutError): asyncio.run(HostDispatcher(self.c,Runtime()).execute('R1',ttl=1))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'failed')

    def test_runtime_malformed_reply(self):
        class Runtime:
            async def start(self,**kw): return 'w'
            async def collect(self,*args,**kw): return {'arbitrary':'data'}
        with self.assertRaises(ContractError): asyncio.run(HostDispatcher(self.c,Runtime()).execute('R1'))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'failed')

    def test_prompt_is_self_contained(self):
        env=self.c.dispatch('R1')
        prompt=render_prompt('worker rules',env,{'type':'object'})
        self.assertIn(env['input_hash'],prompt)
        for source in env['sources'].values():
            self.assertIn(source['sha256'],prompt)
        self.assertIn('UNTRUSTED TASK DATA',prompt)
        self.assertIn('Scope warning',prompt)

    def test_callback_adapter_delivers_schema_and_no_tools(self):
        calls=[]
        async def start_agent(**kwargs):
            calls.append(kwargs)
            return 'actual-session-id'
        async def collect_agent(identity,**kwargs):
            return {'identity':identity,'timeout':kwargs['timeout_seconds']}
        runtime=CallbackHostRuntime(start_agent,collect_agent)
        env=self.c.dispatch('R1')
        identity=asyncio.run(runtime.start(instructions='read only',envelope=env,response_schema={'type':'object'}))
        self.assertEqual(calls[0]['tools'],[])
        self.assertIn(env['request_id'],calls[0]['prompt'])
        self.assertIn('RESPONSE SCHEMA',calls[0]['prompt'])
        self.assertEqual(asyncio.run(runtime.collect(identity,timeout_seconds=12)),{'identity':'actual-session-id','timeout':12})


if __name__=='__main__': unittest.main()
