import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "auto-update-readme.yml"


class AutoUpdateReadmeWorkflowTests(unittest.TestCase):
    def _get_workflow(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

        try:
            import yaml
        except ImportError as exc:
            self.skipTest(f"PyYAML is required for workflow parsing: {exc}")

        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        normalized_workflow_text = re.sub(r'(?m)^(\s*)on:(.*)$', r'\1"on":\2', workflow_text, count=1)
        return yaml.safe_load(normalized_workflow_text)

    def _get_push_config(self):
        workflow_on = self._get_workflow().get("on")
        self.assertIsNotNone(workflow_on, 'Workflow must define an "on" section')

        if isinstance(workflow_on, list):
            self.assertIn("push", workflow_on, 'Workflow "on" sequence must include "push"')
            self.fail('Workflow "on" must be a mapping so push branches can be restricted to "main"')

        self.assertIsInstance(workflow_on, dict, 'Workflow "on" section must be a mapping')
        self.assertIn("push", workflow_on, 'Workflow "on" section must define a push trigger')

        push_config = workflow_on["push"]
        self.assertIsInstance(push_config, dict, 'Workflow "push" trigger must be a mapping')
        return push_config

    def _get_steps(self):
        jobs = self._get_workflow().get("jobs")
        self.assertIsInstance(jobs, dict, 'Workflow must define a "jobs" mapping')
        self.assertIn("update-readme", jobs, 'Workflow "jobs" must define "update-readme"')

        update_readme_job = jobs["update-readme"]
        self.assertIsInstance(update_readme_job, dict, 'Workflow job "update-readme" must be a mapping')
        steps = update_readme_job.get("steps")
        self.assertIsInstance(steps, list, 'Workflow job "update-readme" must define a steps list')
        return steps

    def _find_step_by_uses(self, action):
        for step in self._get_steps():
            if step.get("uses") == action:
                return step
        self.fail(f"Expected step using {action!r}")

    def _find_step_containing_run(self, text):
        for step in self._get_steps():
            if text in step.get("run", ""):
                return step
        self.fail(f"Expected step containing run text {text!r}")

    def test_workflow_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_workflow_triggers_on_push_to_main(self):
        self.assertEqual(self._get_workflow().get("name"), "Auto-Update README")
        self.assertEqual(self._get_push_config().get("branches"), ["main"])

    def test_workflow_sets_up_python_and_generates_readme(self):
        self.assertEqual(self._find_step_by_uses("actions/checkout@v5").get("name"), "Checkout repository")
        setup_python_step = self._find_step_by_uses("actions/setup-python@v5")
        self.assertEqual(setup_python_step.get("with", {}).get("python-version"), "3.11")
        self.assertEqual(
            self._find_step_containing_run("python automation/scripts/generate-readme.py").get("name"),
            "Generate README",
        )

    def test_workflow_commits_updated_readme(self):
        install_step = self._find_step_containing_run("automation/scripts/requirements.txt")
        self.assertEqual(install_step.get("name"), "Install dependencies")

        commit_step = self._find_step_containing_run("git add README.md")
        self.assertEqual(commit_step.get("name"), "Commit updated README")
        self.assertIn('git commit -m "Auto-update README"', commit_step.get("run", ""))
        self.assertIn("git push", commit_step.get("run", ""))


if __name__ == "__main__":
    unittest.main()
