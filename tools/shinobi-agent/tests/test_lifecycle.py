"""Adversarial contract and controller tests for requirements-grounded execution."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_openrouter import ChatOpenRouter
from contracts import Request
from execution import execute_run
from execution_store import Runs
from execution_helpers import scripted_execution_generate
from helpers import output
from lifecycle_helpers import plan_for, stage_generate
from runner import dispatch
import test_execution


class LifecycleTests(unittest.TestCase):
    setUp = test_execution.ExecutionTests.setUp
    tearDown = test_execution.ExecutionTests.tearDown
    request = test_execution.ExecutionTests.request
    approve = test_execution.ExecutionTests.approve
    execute = test_execution.ExecutionTests.execute

    def grounding(self):
        row=self.store.db.execute("SELECT request_id,query,response FROM turns WHERE session_id=? ORDER BY rowid DESC LIMIT 1",(self.session,)).fetchone()
        return plan_for(json.loads(row['response'])['outcome']['proposal'],self.settings,row['request_id'],row['query'])

    def test_missing_requirement_lineage_cannot_draft(self):
        with self.assertRaisesRegex(ValueError,'lifecycle plan'):
            dispatch(Request(operation='contract',request_id='missing',session_id=self.session,execution=self.settings),self.store)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM approvals').fetchone()[0],0)

    def test_fabricated_origins_orphan_tasks_and_unresolved_decisions_block(self):
        for kind in ('origin','orphan','uncertain','coverage'):
            plan=self.grounding()
            if kind=='origin':plan['requirements']['requirements'][0]['source_quote']='The user never said this'
            if kind=='orphan':plan['assignments'][0]['requirement_ids']=['invented']
            if kind=='uncertain':plan['requirements']['uncertainties']=['Should the timeout change?']
            if kind=='coverage':plan['scenarios'].pop()
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                self.request('contract',identity=kind,execution={**self.settings,'lifecycle':plan})

    def test_planning_reviewer_can_reject_misleading_green_check(self):
        self.settings['lifecycle']=self.grounding()
        def reject(model,messages,**kwargs):
            result=stage_generate(messages)
            call=result.generations[0].message.tool_calls[0]
            call['args'].update(verdict='changes_required',summary='The check never exercises the public API',findings=[
                {'category':'test_design','requirement_ids':['R0'],'explanation':'A constant assertion can pass with broken behavior'}])
            return result
        with patch.object(ChatOpenRouter,'_generate',reject):
            result = dispatch(Request(operation='contract',request_id='review-fail',session_id=self.session,execution=self.settings),self.store)
        self.assertIsNone(result['contract'])
        self.assertEqual(result['planning_review']['findings'][0]['category'],'test_design')
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM planning_reviews').fetchone()[0],1)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM contracts').fetchone()[0],0)

    def test_final_validation_cannot_be_replaced_by_quality_pass(self):
        run_id=self.approve()
        def reject(model,messages,**kwargs):
            result=scripted_execution_generate(model,messages,**kwargs)
            if any('Stage: validation' in str(m.content) for m in messages):
                call=result.generations[0].message.tool_calls[0]
                call['args'].update(verdict='needs_amendment',summary='The required user path was never exercised',findings=[
                    {'category':'test_design','requirement_ids':['R0'],'explanation':'Wrong surface'}])
            return result
        with patch.object(ChatOpenRouter,'_generate',reject):execute_run(self.store.root,run_id)
        info=Runs(self.store).info(run_id)
        self.assertEqual(info['status'],'waiting_approval',info['message'])
        self.assertEqual(info['reviews'][-1]['verdict'],'pass')
        self.assertIsNone(info['artifact'])

    def admission_settings(self):
        self.settings['checks'].append({'id':'regression','argv':['python3.12','-B','-m','unittest','test_new']})
        self.settings['work_items'].insert(0,{'id':'tests','instruction':'Add the cap regression test','paths':['test_new.py']})
        self.settings['work_items'][1]['depends_on']=['tests']
        self.settings['work_items'][2]['depends_on']=['tests']
        row=self.store.db.execute('SELECT response FROM turns WHERE session_id=?',(self.session,)).fetchone()
        value=json.loads(row['response']);value['outcome']['proposal']['affected_paths'].append('test_new.py')
        with self.store.db:self.store.db.execute('UPDATE turns SET response=? WHERE session_id=?',(json.dumps(value),self.session))
        plan=self.grounding()
        plan['scenarios'][1]['check_ids']=['behavior']
        plan['assignments'][0].update(requirement_ids=['R0'], scenario_ids=['S0'])
        plan['test_admissions']=[{'item_id':'tests','paths':['test_new.py'],'scenario_ids':['S0'],'check_ids':['regression']}]
        self.settings['lifecycle']=plan

    def test_new_regression_test_is_reviewed_frozen_and_then_used_for_delivery(self):
        self.admission_settings()
        run_id=self.approve()
        def generate(model,messages,**kwargs):
            prompt='\n'.join(str(m.content) for m in messages if m.type=='system')
            if 'bounded, user-approved repository work item' in prompt:
                payload,_=json.JSONDecoder().raw_decode(prompt[prompt.index('{"contract":'):])
                if payload['assignment']['id']=='tests':
                    if not any(isinstance(m,ToolMessage) and m.name=='write_source' for m in messages):
                        return output(AIMessage(content='',tool_calls=[{'name':'write_source','id':'new-test','args':{
                            'path':'test_new.py','content':'import unittest\nfrom reconnect import retry_delay\nclass Regression(unittest.TestCase):\n    def test_cap(self): self.assertEqual(retry_delay(100), 10)\n'}}]))
                    return output(AIMessage(content='',tool_calls=[{'name':'WorkerReport','id':'test-report','args':{'summary':'Added a public behavior regression test'}}]))
            return scripted_execution_generate(model,messages,**kwargs)
        with patch.object(ChatOpenRouter,'_generate',generate):execute_run(self.store.root,run_id)
        info=Runs(self.store).info(run_id)
        self.assertEqual(info['status'],'verified',info['message'])
        admission=info['admissions']['tests']
        self.assertEqual(admission['checks'][0]['outcome'],'failed')
        self.assertEqual(next(c for c in info['checks'] if c['id']=='regression')['outcome'],'passed')
        self.assertEqual(admission['review']['stage'],'test_admission')
        artifact=json.loads(Path(info['artifact']['evidence']).read_text())
        self.assertEqual(artifact['validation']['artifact_hash'],info['artifact']['artifact_hash'])
        self.assertIn('test_new.py',artifact['admissions']['tests']['inputs'])
        self.assertFalse((self.repository/'test_new.py').exists())
        from lifecycle_execution import validate_admissions
        from execution import Context
        (Path(info['workspace'])/'test_new.py').write_text('pass\n')
        with self.assertRaisesRegex(Exception,'Admitted test changed'):
            validate_admissions(Context(self.store.root,run_id),Path(info['workspace']))

    def test_test_authoring_cannot_be_parallel_with_implementation_or_overwrite_an_oracle(self):
        self.admission_settings()
        self.settings['work_items'][1]['depends_on']=[]
        with self.assertRaisesRegex(ValueError,'depend on test admission'):
            self.request('contract',execution=self.settings)

    def test_stage_review_cannot_omit_a_requirement(self):
        run_id=self.approve()
        def omit(model,messages,**kwargs):
            result=scripted_execution_generate(model,messages,**kwargs)
            for call in result.generations[0].message.tool_calls:
                if call['name']=='StageReview':call['args']['coverage'].pop()
            return result
        with patch.object(ChatOpenRouter,'_generate',omit):execute_run(self.store.root,run_id)
        info=Runs(self.store).info(run_id)
        self.assertNotEqual(info['status'],'verified')
        self.assertIn('coverage',info['message'])
        self.assertIsNone(info['artifact'])

    def test_owned_skill_exposes_local_resources_and_rejects_traversal(self):
        from workflows import skill_record,read_skill_resource
        record=skill_record('behavior-tdd')
        self.assertEqual(record['attribution']['owner'], 'Shinobi')
        self.assertIn('tests.md',read_skill_resource('behavior-tdd'))
        with self.assertRaises(ValueError):read_skill_resource('behavior-tdd','../../AGENTS.md')

    def test_requirement_revisions_and_removal_need_explicit_lineage(self):
        from engineering import RequirementRecord
        from lifecycle import validate_requirement_update
        before = RequirementRecord.model_validate(self.grounding()['requirements'])
        validate_requirement_update(before, before)
        after = before.model_copy(deep=True)
        after.requirements[0].statement = 'A revised requested bound'
        with self.assertRaisesRegex(ValueError, 'revision'):
            validate_requirement_update(before, after)
        after.revision += 1
        validate_requirement_update(before, after)
        removed = after.requirements.pop().id
        with self.assertRaisesRegex(ValueError, 'supersedes'):
            validate_requirement_update(before, after)
        after.supersedes[removed] = 'Explicitly replaced by the revised bound'
        validate_requirement_update(before, after)

    def test_optional_adversarial_review_cannot_be_silently_ignored(self):
        self.settings['adversarial_models'] = ['test/independent']
        run_id = self.approve()
        def reject(model, messages, **kwargs):
            result = scripted_execution_generate(model, messages, **kwargs)
            if any('Stage: adversarial' in str(m.content) for m in messages):
                call = result.generations[0].message.tool_calls[0]
                call['args'].update(verdict='needs_amendment', summary='Uncovered requirement boundary', findings=[
                    {'category':'test_design', 'requirement_ids':['R0'], 'explanation':'The approved checks omit a required boundary'}])
            return result
        with patch.object(ChatOpenRouter, '_generate', reject):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info['status'], 'waiting_approval', info['message'])
        self.assertEqual(info['adversarial_reviews'][0]['model'], 'test/independent')
        self.assertIsNone(info['artifact'])

    def test_adversarial_models_must_be_explicit_and_distinct(self):
        for models in (['test/offline'], ['test/other', 'test/other']):
            with self.subTest(models=models), self.assertRaises(ValueError):
                self.request('contract', execution={**self.settings, 'adversarial_models':models})


if __name__=='__main__':unittest.main()
