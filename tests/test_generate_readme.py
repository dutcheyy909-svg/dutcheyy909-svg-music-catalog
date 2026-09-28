import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "automation" / "scripts" / "generate-readme.py"


spec = importlib.util.spec_from_file_location("generate_readme", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load README generator script from {SCRIPT_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GenerateReadmeTests(unittest.TestCase):
    def test_generator_paths_are_resolved_from_script_location(self):
        script_dir = SCRIPT_PATH.parent
        automation_dir = script_dir.parent
        repo_root = automation_dir.parent
        self.assertEqual(module.SCRIPT_DIR, script_dir)
        self.assertEqual(module.AUTOMATION_DIR, automation_dir)
        self.assertEqual(module.REPO_ROOT, repo_root)
        self.assertEqual(module.TEMPLATE_PATH, automation_dir / "templates" / "readme-template.md")
        self.assertEqual(module.DATA_PATH, automation_dir / "templates" / "readme-data.json")
        self.assertEqual(module.README_PATH, repo_root / "README.md")

    def test_repository_has_single_canonical_readme_generator(self):
        generator_paths = sorted(REPO_ROOT.rglob("generate-readme.py"))
        self.assertEqual(generator_paths, [SCRIPT_PATH])

    def test_template_matches_canonical_sections(self):
        self.assertEqual(
            module.load_template(),
            "# {{project_name}}\n\n"
            "## Overview\n"
            "{{overview}}\n\n"
            "## Repository Layout\n"
            "{{repository_layout}}\n\n"
            "## Automation\n"
            "{{automation}}\n\n"
            "## Validation\n"
            "{{validation}}\n",
        )

    def test_render_raises_on_template_data_mismatch(self):
        with self.assertRaises(ValueError):
            module.render("# {{project_name}}\n{{overview}}", {"project_name": "x"})

    def test_render_raises_on_unused_data_key(self):
        with self.assertRaises(ValueError):
            module.render("# {{project_name}}", {"project_name": "x", "overview": "y"})

    def test_render_allows_placeholder_like_text_in_values(self):
        rendered = module.render("# {{project_name}}", {"project_name": "Guide for {{name}} placeholders"})
        self.assertEqual(rendered, "# Guide for {{name}} placeholders")

    def test_render_does_not_reprocess_placeholder_like_value_text(self):
        rendered = module.render(
            "# {{project_name}}\n{{overview}}",
            {"project_name": "Literal {{overview}} text", "overview": "must not be injected"},
        )
        self.assertEqual(rendered, "# Literal {{overview}} text\nmust not be injected")

    def test_repository_readme_matches_template_render(self):
        expected_readme = module.render(module.load_template(), module.load_sections())
        self.assertEqual(module.README_PATH.read_text(encoding="utf-8"), expected_readme)

    def test_main_writes_readme_from_non_repo_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_path = temp_path / "readme-template.md"
            data_path = temp_path / "readme-data.json"
            output_path = temp_path / "README.md"

            template_path.write_text("# {{project_name}}\n\n{{overview}}\n", encoding="utf-8")
            data_path.write_text(
                '{"project_name": "Repo", "overview": "Generated from template"}',
                encoding="utf-8",
            )

            original_template = module.TEMPLATE_PATH
            original_data = module.DATA_PATH
            original_output = module.README_PATH
            original_cwd = Path.cwd()
            try:
                module.TEMPLATE_PATH = template_path
                module.DATA_PATH = data_path
                module.README_PATH = output_path
                os.chdir(temp_path)
                module.main()
            finally:
                os.chdir(original_cwd)
                module.TEMPLATE_PATH = original_template
                module.DATA_PATH = original_data
                module.README_PATH = original_output

            self.assertEqual(output_path.read_text(encoding="utf-8"), "# Repo\n\nGenerated from template\n")

    def test_cli_uses_canonical_script_paths_even_with_shadow_structure_in_cwd(self):
        original_readme = module.README_PATH.read_text(encoding="utf-8")
        try:
            module.README_PATH.write_text("# stale\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                shadow_template = temp_path / "automation" / "templates"
                shadow_template.mkdir(parents=True)
                (shadow_template / "readme-template.md").write_text(
                    "# SHADOW\n{{project_name}}\n", encoding="utf-8"
                )
                (shadow_template / "readme-data.json").write_text(
                    '{"project_name": "shadow"}', encoding="utf-8"
                )

                subprocess.run(
                    [sys.executable, str(SCRIPT_PATH)],
                    cwd=temp_path,
                    check=True,
                )

                self.assertFalse((temp_path / "README.md").exists())
                self.assertEqual(module.README_PATH.read_text(encoding="utf-8"), original_readme)
        finally:
            module.README_PATH.write_text(original_readme, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
