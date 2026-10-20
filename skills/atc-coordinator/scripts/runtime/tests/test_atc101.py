import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from atc10.core import ContractError,Coordinator,compile_prd,digest,validate

ROOT=Path(__file__).resolve().parent.parent

class ATC101Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.prd=json.loads((ROOT/'examples/atc10/prd.json').read_text())
        self.bundle=compile_prd(self.prd,ROOT/'examples/atc10')
        self.c=Coordinator(self.bundle,Path(self.tmp.name)/'run');self.addCleanup(self.c.close)

    def bind(self, request_id, agent):
        self.c.bind(request_id, agent)
        packet = self.c.delivery(request_id)
        self.c.record_delivery(request_id, agent, packet['prompt_sha256'], 'unit-fixture-' + request_id)

    def result(self,e):
        s=e['sources']['S1']
        return {**{k:e[k] for k in ('request_id','task_id','contract_hash','input_hash')},'claims':[{'id':'C1','text':'The source is the ATC v0.9 test report.','requirement_refs':[e['task_id']],'evidence':[{'source_id':'S1','source_sha256':s['sha256'],'start_line':1,'end_line':1,'quote':s['lines'][0]}]}],'limitations':['Unit fixture, not live research.']}

    def test_caller_cannot_mutate_snapshot(self):
        self.bundle['sources']['S1']['lines'][0]='FORGED'
        e=self.c.dispatch('R1')
        self.assertNotEqual(e['sources']['S1']['lines'][0],'FORGED')

    def test_envelope_mutation_cannot_forge_quote(self):
        e=self.c.dispatch('R1');e['sources']['S1']['lines'][0]='FORGED SOURCE'
        self.bind(e['request_id'],'w')
        with self.assertRaises(ContractError):self.c.receive(e['request_id'],'w',self.result(e))

    def test_bundle_property_returns_copy(self):
        self.c.bundle['sources']['S1']['lines'][0]='FORGED'
        self.assertNotEqual(self.c.bundle['sources']['S1']['lines'][0],'FORGED')

    def test_rehashed_inconsistent_source_rejected(self):
        self.bundle['sources']['S1']['lines'][0]='FORGED'
        self.bundle['contract_hash']=digest({k:v for k,v in self.bundle.items() if k!='contract_hash'})
        with self.assertRaises(ContractError):Coordinator(self.bundle,Path(self.tmp.name)/'bad')

    def test_product_context_delivered(self):
        e=self.c.dispatch('R1')
        for field in ('purpose','audience','scope'):self.assertEqual(e['product_context'][field],self.prd[field])

    def test_large_claim_array_rejected_quickly(self):
        e=self.c.dispatch('R1');r=self.result(e);r['claims']=[{'x':i} for i in range(2000)]
        start=time.monotonic()
        with self.assertRaises(ContractError):validate(r,'result')
        self.assertLess(time.monotonic()-start,0.5)

    def test_expiry_after_validation_cannot_commit(self):
        e=self.c.dispatch('R1',ttl=1);self.bind(e['request_id'],'w');r=self.result(e)
        verify=self.c._verify_claims
        def late(*args):
            verify(*args)
            self.c.db.execute('SELECT 1')
        with patch.object(self.c,'_verify_claims',side_effect=late),patch('atc10.core.time.time',side_effect=[time.time(),10**12,10**12,10**12]):
            with self.assertRaises(ContractError):self.c.receive(e['request_id'],'w',r)
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'running')
        self.assertFalse(list(self.c.out.glob('artifacts/**/*.json')))

    def submitted(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'worker')
        self.c.receive(e['request_id'],'worker',self.result(e))
        return e

    def review_packet(self):
        self.submitted();e=self.c.dispatch('R1','reviewer');self.bind(e['request_id'],'reviewer')
        r={k:e[k] for k in ('request_id','task_id','contract_hash','input_hash','artifact_hash')}
        r.update(verdict='accept',acceptance_satisfied=True,
                 checks=[{'claim_id':'C1','supported':True,'reason':'Unit fixture verifies review structure only.'}],
                 criteria=[{'criterion_id':a['id'],'satisfied':True,'claim_refs':['C1'],'reason':'Unit fixture criterion references the claim.'} for a in e['order']['criteria']],
                 summary='Unit fixture, not a live semantic reviewer.')
        return e,r

    def test_compiler_copies_prd(self):
        self.prd['purpose']='MUTATED'
        self.assertNotEqual(self.bundle['prd']['purpose'],'MUTATED')

    def test_no_delivery_receipt_blocks_submission(self):
        e=self.c.dispatch('R1');self.c.bind(e['request_id'],'worker')
        with self.assertRaisesRegex(ContractError,'receipt'):self.c.receive(e['request_id'],'worker',self.result(e))

    def test_wrong_delivery_hash(self):
        e=self.c.dispatch('R1');self.c.bind(e['request_id'],'worker')
        with self.assertRaisesRegex(ContractError,'hash mismatch'):self.c.record_delivery(e['request_id'],'worker','a'*64,'host')

    def test_wrong_delivery_identity(self):
        e=self.c.dispatch('R1');self.c.bind(e['request_id'],'worker');p=self.c.delivery(e['request_id'])
        with self.assertRaisesRegex(ContractError,'identity'):self.c.record_delivery(e['request_id'],'other',p['prompt_sha256'],'host')

    def test_delivery_receipt_cannot_replay(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'worker');p=self.c.delivery(e['request_id'])
        with self.assertRaisesRegex(ContractError,'already'):self.c.record_delivery(e['request_id'],'worker',p['prompt_sha256'],'host')

    def test_persisted_prompt_has_context_and_schema(self):
        e=self.c.dispatch('R1');p=self.c.delivery(e['request_id'])
        self.assertIn(self.prd['purpose'],p['prompt']);self.assertIn(self.prd['audience'],p['prompt'])
        self.assertIn('RESPONSE SCHEMA',p['prompt']);self.assertIn(e['input_hash'],p['prompt'])

    def test_prompt_tamper_blocks_receive(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'worker');p=self.c.delivery(e['request_id'])
        (self.c.out/p['prompt_path']).write_text('tampered')
        with self.assertRaisesRegex(ContractError,'prompt changed'):self.c.receive(e['request_id'],'worker',self.result(e))

    def test_prompt_tamper_invalidates_accepted_report(self):
        e,r=self.review_packet();self.c.receive(e['request_id'],'reviewer',r)
        p=self.c.report()['requests'][e['request_id']]['delivery']['prompt_path']
        (self.c.out/p).write_text('tampered')
        report=self.c.report();self.assertEqual(report['product_status'],'incomplete');self.assertIn('R1',report['integrity_errors'])

    def test_missing_criterion(self):
        e,r=self.review_packet();r['criteria']=[]
        with self.assertRaises(ContractError):self.c.receive(e['request_id'],'reviewer',r)

    def test_unknown_criterion(self):
        e,r=self.review_packet();r['criteria'][0]['criterion_id']='UNKNOWN'
        with self.assertRaisesRegex(ContractError,'every acceptance'):self.c.receive(e['request_id'],'reviewer',r)

    def test_duplicate_criterion(self):
        e,r=self.review_packet();other=copy.deepcopy(r['criteria'][0]);other['reason']='Different reason but same criterion identifier.';r['criteria'].append(other)
        with self.assertRaisesRegex(ContractError,'duplicate'):self.c.receive(e['request_id'],'reviewer',r)

    def test_criterion_requires_claim_refs(self):
        e,r=self.review_packet();r['criteria'][0]['claim_refs']=[]
        with self.assertRaisesRegex(ContractError,'supporting claims'):self.c.receive(e['request_id'],'reviewer',r)

    def test_criterion_unknown_claim_ref(self):
        e,r=self.review_packet();r['criteria'][0]['claim_refs']=['UNKNOWN']
        with self.assertRaisesRegex(ContractError,'supporting claims'):self.c.receive(e['request_id'],'reviewer',r)

    def test_failed_criterion_cannot_hide_in_summary(self):
        e,r=self.review_packet();r['criteria'][0]['satisfied']=False
        with self.assertRaisesRegex(ContractError,'summary conflicts'):self.c.receive(e['request_id'],'reviewer',r)

    def test_satisfied_criterion_cannot_use_unsupported_claim(self):
        e,r=self.review_packet();r['checks'][0]['supported']=False
        with self.assertRaisesRegex(ContractError,'unsupported claim'):self.c.receive(e['request_id'],'reviewer',r)

    def test_multi_criterion_must_cover_all(self):
        self.prd['requirements'][0]['acceptance'].append('A second explicit acceptance criterion must also be reviewed.')
        self.c.close();self.c=Coordinator(compile_prd(self.prd,ROOT/'examples/atc10'),Path(self.tmp.name)/'two')
        self.addCleanup(self.c.close)
        e,r=self.review_packet();self.assertEqual([a['criterion_id'] for a in r['criteria']],['AC001','AC002'])
        r['criteria'].pop()
        with self.assertRaisesRegex(ContractError,'every acceptance'):self.c.receive(e['request_id'],'reviewer',r)

    def test_producer_identity_distinct_across_orders(self):
        e1=self.c.dispatch('R1');self.bind(e1['request_id'],'worker');e2=self.c.dispatch('R2')
        with self.assertRaisesRegex(ContractError,'distinct'):self.bind(e2['request_id'],'worker')

    def test_expiry_during_save_rolls_back_and_cleans_artifact(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'worker');original=self.c._save
        def expired(*args,**kwargs):
            with patch('atc10.core.time.time',return_value=10**12):return original(*args,**kwargs)
        with patch.object(self.c,'_save',side_effect=expired):
            with self.assertRaisesRegex(ContractError,'expired'):self.c.receive(e['request_id'],'worker',self.result(e))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'running')
        self.assertFalse(list(self.c.out.glob('artifacts/**/*.json')))
        self.c.fail(e['request_id'],'late result');self.assertEqual(self.c.dispatch('R1')['attempt'],2)

    def test_deep_reply_rejected_without_recursion_error(self):
        nested=[];root=nested
        for _ in range(50):child=[];nested.append(child);nested=child
        with self.assertRaises(ContractError):validate(root,'result')

    def test_large_valid_claims_rejected_before_schema_work(self):
        e=self.c.dispatch('R1');r=self.result(e);one=r['claims'][0]
        r['claims']=[{**copy.deepcopy(one),'id':f'C{i}'} for i in range(1700)]
        self.bind(e['request_id'],'worker');start=time.monotonic()
        with self.assertRaisesRegex(ContractError,'budget'):self.c.receive(e['request_id'],'worker',r)
        self.assertLess(time.monotonic()-start,0.5)

    def test_runtime_prompt_mismatch_is_rejected(self):
        import asyncio
        from atc10.runtime import CallbackHostRuntime
        async def forbidden(**kwargs):raise AssertionError('must not start')
        runtime=CallbackHostRuntime(forbidden,forbidden);e=self.c.dispatch('R1')
        with self.assertRaisesRegex(ContractError,'persisted delivery'):
            asyncio.run(runtime.start(instructions='rules',envelope=e,response_schema={},prompt='wrong'))

    def test_oversized_key_rejected_before_schema(self):
        e=self.c.dispatch('R1');r=self.result(e);r['x'*1000000]=0
        with self.assertRaisesRegex(ContractError,'key budget'):validate(r,'result')

    def test_total_string_bytes_bounded_before_schema(self):
        e=self.c.dispatch('R1');r=self.result(e);r['limitations']=['x'*9990+str(i) for i in range(64)]
        with self.assertRaisesRegex(ContractError,'budget'):validate(r,'result')

    def test_post_update_expiry_rolls_back_artifact(self):
        e=self.c.dispatch('R1');self.bind(e['request_id'],'worker');original=self.c._save
        current=time.time()
        def expires_after_update(*args,**kwargs):
            # _save calls time for event, pre-update guard, then post-update guard.
            with patch('atc10.core.time.time',side_effect=[current,current,10**12]):return original(*args,**kwargs)
        with patch.object(self.c,'_save',side_effect=expires_after_update):
            with self.assertRaisesRegex(ContractError,'during commit'):self.c.receive(e['request_id'],'worker',self.result(e))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'running')
        self.assertFalse(self.c.report()['requests'][e['request_id']]['consumed'])
        self.assertFalse(list(self.c.out.glob('artifacts/**/*.json')))
        self.c.fail(e['request_id'],'late');self.assertEqual(self.c.dispatch('R1')['attempt'],2)

    def test_delivery_setup_failure_marks_failed(self):
        import asyncio
        from atc10.runtime import HostDispatcher
        class Runtime:
            async def start(self,**kwargs):raise AssertionError('must not start')
        with patch.object(self.c,'delivery',side_effect=ContractError('disk failure')):
            with self.assertRaisesRegex(ContractError,'disk failure'):asyncio.run(HostDispatcher(self.c,Runtime()).execute('R1'))
        self.assertEqual(self.c.report()['tasks']['R1']['status'],'failed')

    def test_recovery_error_preserves_original_runtime_exception(self):
        import asyncio
        from atc10.runtime import HostDispatcher
        class Runtime:
            async def start(self,**kwargs):raise RuntimeError('original failure')
        with patch.object(self.c,'fail',side_effect=ContractError('recovery error')):
            with self.assertRaisesRegex(RuntimeError,'original failure'):asyncio.run(HostDispatcher(self.c,Runtime()).execute('R1'))
