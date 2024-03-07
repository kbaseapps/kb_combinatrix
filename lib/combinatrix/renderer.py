"""Render the combinatrix output."""

from typing import Any

from combinatrix.constants import (
    JOIN_LIST,
)
from jinja2 import Environment, FileSystemLoader, select_autoescape

J2_SUFFIX = ".j2"


def render_template(file_path: str, template_data: dict[str, Any]) -> str:
    """Render the output page."""
    # Initialize a Jinja2 Environment with the loader pointing to your templates directory
    env = Environment(
        loader=FileSystemLoader("./"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # # export data for displaying in datatables
    # template_data = {
    #     "join_params": join_params[JOIN_LIST],
    #     "object_data": {
    #         ref: {
    #             "info": standardised_data[ref][INFO],
    #             "file": standardised_data[ref]["csv"],
    #             "display": {
    #                 "type": get_data_type(standardised_data[ref]),
    #                 KEYS: (
    #                     {
    #                         k: list(standardised_data[ref][KEYS][k])
    #                         for k in standardised_data[ref][KEYS]
    #                     }
    #                     if KEYS in standardised_data[ref]
    #                     else None
    #                 ),
    #             },
    #             # set
    #             "combined": list(resultset[ref]),
    #         }
    #         for ref in standardised_data
    #     },
    # }

    table_id = "combinatrix_output-table"
    tmpl_vars = {
        "join_params": template_data[JOIN_LIST],
        "table_id": "combinatrix_output-table",
        "page_title": "Combinatrix Report",
        "page_content": [
            {
                "name": "Join Summary",
                "name_lc": "join_summary",
                "template": "views/inc/some_template.j2",
            },
            {
                "name": "Combinatrix Output",
                "name_lc": "combinatrix_table",
                "content": "table",
                "table_config": {
                    "id": table_id,
                    "for_datatables_js": True,
                },
            },
        ],
    }

    # Load the template by name
    template = env.get_template("views/combinatrix" + J2_SUFFIX)

    # Render the template with the provided data
    rendered_template = template.render(tmpl_vars)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rendered_template)

    print(f"Template rendered and saved to {file_path}")

    return file_path
