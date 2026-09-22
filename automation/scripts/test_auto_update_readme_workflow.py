import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "auto-update-readme.yml"


class AutoUpdateReadmeWorkflowTests(unittest.TestCase):
    def _get_workflow(self, workflow_path=None):
        workflow_path = workflow_path or WORKFLOW_PATH
        self.assertTrue(workflow_path.is_file())

        try:
            import yaml
        except ImportError as exc:
            self.skipTest(f"PyYAML is required for workflow parsing: {exc}")

        workflow_text = workflow_path.read_text(encoding="utf-8")
        lines = workflow_text.splitlines(keepends=True)
        top_level_indent = None
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#"):
                top_level_indent = len(line) - len(line.lstrip())
                break

        normalized_lines = list(lines)
        if top_level_indent is not None:
            for index, line in enumerate(lines):
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith("#"):
                    continue

                if len(line) - len(line.lstrip()) != top_level_indent:
                    continue

                normalized_lines[index] = re.sub(
                    r'(?i)^(\s*)on(\s*):(.*)$',
                    r'\1"on"\2:\3',
                    line,
                    count=1,
                )
                if normalized_lines[index] != line:
                    break

        normalized_workflow_text = "".join(normalized_lines)
        return yaml.safe_load(normalized_workflow_text)

    def _get_push_config(self, workflow_path=None):
        workflow_on = self._get_workflow(workflow_path).get("on")
        self.assertIsNotNone(workflow_on, 'Workflow must define an "on" section')

        if isinstance(workflow_on, list):
            self.assertIn("push", workflow_on, 'Workflow "on" sequence must include "push"')
            self.fail('Workflow "on" must be a mapping so push branches can be restricted to "main"')

        self.assertIsInstance(workflow_on, dict, 'Workflow "on" section must be a mapping')
        self.assertIn("push", workflow_on, 'Workflow "on" section must define a push trigger')

        push_config = workflow_on["push"]
        self.assertIsInstance(push_config, dict, 'Workflow "push" trigger must be a mapping')
        return push_config

    def _get_update_readme_job(self, workflow_path=None):
        jobs = self._get_workflow(workflow_path).get("jobs")
        self.assertIsInstance(jobs, dict, 'Workflow must define a "jobs" mapping')
        self.assertIn("update-readme", jobs, 'Workflow "jobs" must define "update-readme"')

        update_readme_job = jobs["update-readme"]
        self.assertIsInstance(update_readme_job, dict, 'Workflow job "update-readme" must be a mapping')
        return update_readme_job

    def _get_step_list(self, workflow_path=None):
        steps = self._get_update_readme_job(workflow_path).get("steps")
        self.assertIsInstance(steps, list, 'Workflow job "update-readme" must define a steps list')
        return steps

    def _find_step_by_uses(self, action, workflow_path=None):
        for step in self._get_step_list(workflow_path):
            self.assertIsInstance(step, dict, "Workflow steps must be mappings")
            if step.get("uses") == action:
                return step
        self.fail(f"Expected step using {action!r}")

    def _find_step_containing_run(self, text, workflow_path=None):
        for step in self._get_step_list(workflow_path):
            self.assertIsInstance(step, dict, "Workflow steps must be mappings")
            if text in step.get("run", ""):
                return step
        self.fail(f"Expected step containing run text {text!r}")

    def test_workflow_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_get_workflow_normalizes_unquoted_top_level_on_key(self):
        workflow_text = """name: Example
on:
  push:
    branches:
      - main
jobs:
  update-readme:
    runs-on: ubuntu-latest
    steps: []
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_workflow_path = Path(temp_dir) / "workflow.yml"
            temp_workflow_path.write_text(workflow_text, encoding="utf-8")
            workflow = self._get_workflow(temp_workflow_path)

        self.assertIn("on", workflow)
        self.assertTrue(all(isinstance(key, str) for key in workflow))
        self.assertEqual(workflow["on"]["push"]["branches"], ["main"])

    def test_workflow_triggers_on_push_to_main(self):
        self.assertEqual(self._get_push_config().get("branches"), ["main"])

    def test_workflow_runs_on_ubuntu_latest(self):
        self.assertEqual(self._get_update_readme_job().get("runs-on"), "ubuntu-latest")

    def test_workflow_sets_up_python_and_generates_readme(self):
        self._find_step_by_uses("actions/checkout@v5")
        setup_python_step = self._find_step_by_uses("actions/setup-python@v5")
        self.assertTrue(setup_python_step.get("with", {}).get("python-version"))
        self._find_step_containing_run("python automation/scripts/generate-readme.py")

    def test_workflow_commits_updated_readme(self):
        install_step = self._find_step_containing_run("automation/scripts/requirements.txt")
        self.assertIn("python -m pip install -r automation/scripts/requirements.txt", install_step.get("run", ""))

        commit_step = self._find_step_containing_run("git add README.md")
        self.assertIn('git commit -m "Auto-update README"', commit_step.get("run", ""))
        self.assertIn("git push", commit_step.get("run", ""))


if __name__ == "__main__":
    unittest.main()
