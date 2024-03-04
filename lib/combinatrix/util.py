"""General utility functions."""

import json
import os
import re
from typing import Any

from combinatrix.constants import INFO

SPECIAL_CHAR_REGEX = re.compile(r"\W+")
MULTISPACE_REGEX = re.compile(r"\s+")


def get_info(ws_output: dict[str, Any]) -> dict[str, Any]:
    """Get the "infostruct" dictionary from a workspace object.

    :param ws_output: object from the workspace
    :type ws_output: dict[str, Any]
    :raises KeyError: if there is no "infostruct" key
    :return: contents of infostruct
    :rtype: dict[str, Any]
    """
    if not ws_output.get(INFO):
        err_msg = f"Cannot find an '{INFO}' key"
        raise KeyError(err_msg)
    return ws_output[INFO]


def get_upa(ws_output: dict[str, Any]) -> str:
    """Retrieve the UPA from a workspace infostruct.

    :param ws_output: workspace object, including the "infostruct" key/value
    :type ws_output: dict[str, Any]
    :return: KBase UPA
    :rtype: str
    """
    infostruct = get_info(ws_output)
    return f"{infostruct['wsid']}/{infostruct['objid']}/{infostruct['version']}"


def get_data_type(ws_output: dict[str, Any]) -> str:
    """Retrieve the data type from a workspace infostruct.

    :param ws_output: workspace object, including the "infostruct" key/value
    :type ws_output: dict[str, Any]
    :return: ws object type
    :rtype: str
    """
    infostruct = get_info(ws_output)
    return infostruct["type"]


def remove_special_chars(text: str) -> str:
    """Remove all special characters from a string and replace runs of spec chars with an underscore.

    :param string: the input string to remove the special chars from
    :type string: str
    :return: the sanitised output string
    :rtype: str
    """
    return re.sub(SPECIAL_CHAR_REGEX, "_", text)


def resort_fieldnames(unsorted_fieldnames: list[str] | set[str]) -> list[str]:
    """Re-sort the fieldnames of a dataset to ensure that name and ID are first.

    :param unsorted_fieldnames: unsorted fieldnames
    :type unsorted_fieldnames: list[str] | set[str]
    :return: re-sorted fieldnames
    :rtype: list[str]
    """
    fieldnames = sorted(unsorted_fieldnames)
    # name and id headers should go to the front of the list
    for field in ["name", "id"]:
        if field in fieldnames:
            fieldnames.remove(field)
            fieldnames.insert(0, field)

    return fieldnames


def log_this(config: dict[str, str], file_name: str, output_obj: dict | list) -> str:
    """Utility function for printing JSON data to a file.

    :param config: configuration object
    :type config: dict[str, str]
    :param file_name: file to log to
    :type file_name: string
    :param output_obj: object to log. Must be a JSON-dumpable object.
    :type output_obj: dict|list
    :return: full path of the new file
    :rtype: str
    """
    cleaned_file_name = remove_special_chars(file_name)

    scratch_dir = (
        config["scratch"]
        if os.path.isabs(config["scratch"])
        else os.path.abspath(config["scratch"])
    )

    output_file = f"{scratch_dir}/{cleaned_file_name}.json"
    with open(output_file, "w") as f:
        f.write(json.dumps(output_obj, indent=2, sort_keys=True))

    return output_file
