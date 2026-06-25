from pathlib import Path

TEMPLATE_DIR = Path("templates")


def load_template(template_name: str) -> str:
    """
    Load an email template from the templates folder.
    """

    template_path = TEMPLATE_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()