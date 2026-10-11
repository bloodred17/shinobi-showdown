"""Local maintenance is independent of upstream; approved bytes remain bound."""
from pathlib import Path
import re
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from execution_contracts import BoundaryFailure
import workflows


class OwnedSkillsTests(unittest.TestCase):
    def workflow(self, task='feature', selected=None, autonomy='standard', items=1):
        proposal = SimpleNamespace(task_type=task, guidance_ids=None)
        settings = SimpleNamespace(task_type=None, role_models={}, adversarial_models=[],
            guidance_ids=selected, engineering=None, lifecycle=object(),
            work_items=[object() for _ in range(items)], autonomy=autonomy)
        return workflows.select_workflow(proposal, settings, 'test/model')

    def test_every_registered_procedure_and_local_link_loads_without_network(self):
        self.assertEqual(set(workflows.SKILLS), {
            p.parent.name for p in workflows.SKILLS_ROOT.glob('*/SKILL.md')})
        with patch('socket.create_connection', side_effect=AssertionError('Network dependency')):
            for name in workflows.SKILLS:
                with self.subTest(skill=name):
                    record = workflows.skill_record(name)
                    self.assertTrue(record['text'].startswith('---\nname: '+name+'\n'))
                    for resource in record['resources']:
                        self.assertIsInstance(workflows.read_skill_resource(name, resource), str)
                    for link in re.findall(r'\]\(([^)]+)\)', record['text']):
                        if '://' not in link and not link.startswith('#'):
                            self.assertIn(link, record['resources'])

    def test_local_edit_is_allowed_but_invalidates_previous_approved_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in workflows.required_skills('feature'):
                shutil.copytree(workflows.SKILLS_ROOT / name, root / name)
            with patch.object(workflows, 'SKILLS_ROOT', root):
                before = self.workflow(selected=['behavior-tdd'])
                path = root / 'behavior-tdd' / 'references' / 'tests.md'
                path.write_text(path.read_text() + '\nA locally maintained regression scenario.\n')
                # Local content may evolve without editing the historical source hash.
                after = self.workflow(selected=['behavior-tdd'])
                self.assertNotEqual(before.fingerprint, after.fingerprint)
                with self.assertRaises(BoundaryFailure):
                    workflows.skill_tools(before)[0].invoke({
                        'skill_id':'behavior-tdd', 'resource':'references/tests.md'})
                self.assertIn('locally maintained regression', workflows.skill_tools(after)[0].invoke({
                    'skill_id':'behavior-tdd', 'resource':'references/tests.md'}))

    def test_routing_distinguishes_investigation_refactor_feature_and_optional_work(self):
        selected = lambda workflow: {r['id'] for r in workflow.guidance}
        for task in ('investigation', 'refactor'):
            ids = selected(self.workflow(task))
            self.assertNotIn('behavior-tdd', ids)
            self.assertNotIn('requirements-interview', ids)
        ids = selected(self.workflow())
        self.assertIn('behavior-tdd', ids)
        self.assertFalse(any(workflows.SKILLS.get(key, {}).get('category') == 'maintenance' for key in ids))
        self.assertNotIn('application-verification', ids)
        self.assertNotIn('bounded-autonomy', ids)
        self.assertIn('bounded-autonomy', selected(self.workflow(autonomy='within_contract')))
        self.assertNotIn('dependency-execution', ids)
        self.assertIn('dependency-execution', selected(self.workflow(items=2)))
        self.assertTrue({'requirements-interview','domain-modeling'} <= selected(
            self.workflow(selected=['requirements-discovery'])))

    def test_unselected_specialist_is_not_readable_during_execution(self):
        tool = workflows.skill_tools(self.workflow())[0]
        with self.assertRaisesRegex(ValueError, 'outside the approved selection'):
            tool.invoke({'skill_id':'security-review'})
        with self.assertRaises(ValueError):
            workflows.read_skill_resource('behavior-tdd', '../../agent.py')
