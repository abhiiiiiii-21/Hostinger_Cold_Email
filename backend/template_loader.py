from pathlib import Path

TEMPLATE_DIR = Path("templates")


def load_template(template_name: str, country: str = "USA") -> str:
    """
    Load an email template from the country-specific templates folder.
    """
    # Fallback if country is somehow empty
    if not country:
        country = "USA"
        
    template_path = TEMPLATE_DIR / country / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {country}/{template_name}")

    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()