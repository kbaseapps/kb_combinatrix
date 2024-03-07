"""Render the combinatrix output."""

from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

J2_SUFFIX = ".j2"


def render_template(file_path: str, template_data: dict[str, Any]) -> str:
    """Render the output page."""
    # Initialize a Jinja2 Environment with the loader pointing to your templates directory
    env = Environment(
        loader=FileSystemLoader("./"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    tmpl_vars = {
        **template_data,
        "table_id": "combinatrix_output-table",
        "page_title": "Combinatrix Report",
    }

    # Load the template by name
    template = env.get_template("views/combinatrix" + J2_SUFFIX)

    # Render the template with the provided data
    rendered_template = template.render(tmpl_vars)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rendered_template)

    print(f"Template rendered and saved to {file_path}")

    return file_path
