from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = SCRIPT_DIR.parent
REPO_ROOT = AUTOMATION_DIR.parent

TEMPLATE_PATH = AUTOMATION_DIR / "templates" / "readme-template.md"
README_PATH = REPO_ROOT / "README.md"


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def generate_sections() -> dict[str, str]:
    return {
        "project_name": "Turbo Adventure",
        "overview": "Automation + profile metadata + scripts.",
        "latest_updates": "- Added README auto-update workflow",
        "skills": "- Python\n- Automation\n- Metadata processing",
        "projects": "- ProjectData extractor\n- Profile metadata builder",
    }


def render(template: str, data: dict[str, str]) -> str:
    rendered = template
    for key, value in data.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def main() -> None:
    template = load_template()
    data = generate_sections()
    readme = render(template, data)
    README_PATH.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
