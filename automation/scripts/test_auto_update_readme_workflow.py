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

        class WorkflowLoader(yaml.SafeLoader):
            pass

        WorkflowLoader.yaml_implicit_resolvers = {
            key: [resolver for resolver in value if resolver[0] != "tag:yaml.org,2002:bool"]
            for key, value in yaml.SafeLoader.yaml_implicit_resolvers.items()
        }

        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        return yaml.load(workflow_text, Loader=WorkflowLoader)

    def _get_push_config(self):
        workflow_on = self._get_workflow()["on"]
        self.assertIsInstance(workflow_on, dict, 'Workflow "on" section must be a mapping')
        self.assertIn("push", workflow_on, 'Workflow "on" section must define a push trigger')

        push_config = workflow_on["push"]
        self.assertIsInstance(push_config, dict, 'Workflow "push" trigger must be a mapping')
        return push_config

    def _get_steps(self):
        return self._get_workflow()["jobs"]["update-readme"]["steps"]

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
        self.assertEqual(self._get_workflow()["name"], "Auto-Update README")
        self.assertEqual(self._get_push_config()["branches"], ["main"])

    def test_workflow_sets_up_python_and_generates_readme(self):
        self.assertEqual(self._find_step_by_uses("actions/checkout@v5")["name"], "Checkout repository")
        setup_python_step = self._find_step_by_uses("actions/setup-python@v5")
        self.assertEqual(setup_python_step["with"]["python-version"], "3.11")
        self.assertEqual(
            self._find_step_containing_run("python automation/scripts/generate-readme.py")["name"],
            "Generate README",
        )

    def test_workflow_commits_updated_readme(self):
        install_step = self._find_step_containing_run("automation/scripts/requirements.txt")
        self.assertEqual(install_step["name"], "Install dependencies")

        commit_step = self._find_step_containing_run("git add README.md")
        self.assertEqual(commit_step["name"], "Commit updated README")
        self.assertIn('git commit -m "Auto-update README"', commit_step["run"])
        self.assertIn("git push", commit_step["run"])


if __name__ == "__main__":
    unittest.main()
