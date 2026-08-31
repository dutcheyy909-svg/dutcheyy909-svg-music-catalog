import json
from pathlib import Path

def load_template():
    return Path("automation/templates/readme-template.md").read_text()

def generate_sections():
    return {
        "project_name": "Turbo Adventure",
        "overview": "Automation + profile metadata + scripts.",
        "latest_updates": "- Added README auto-update workflow",
        "skills": "- Python\n- Automation\n- Metadata processing",
        "projects": "- ProjectData extractor\n- Profile metadata builder"
    }

def render(template, data):
    for key, value in data.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

if __name__ == "__main__":
    template = load_template()
    data = generate_sections()
    readme = render(template, data)
    Path("README.md").write_text(readme)
