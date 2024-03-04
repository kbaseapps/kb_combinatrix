"""Convert data from various input formats to delimiter-separated data."""

import csv
import json
import os
from copy import deepcopy
from typing import Any

from combinatrix.constants import DATA, DL, FN, KEYS
from combinatrix.util import get_data_type, get_upa, resort_fieldnames


def convert_data(fetched_data: dict[str, Any]) -> dict[str, Any]:
    """Convert data into a format that can be used in `combine_data`.

    :param fetched_data: data from the workspace, indexed by ref
    :type fetched_data: dict[str, Any]
    :raises RuntimeError: if there are errors in converting the data
    :return: fetched_data with converted data integrated into it
    :rtype: dict[str, Any]
    """
    errors = []
    for ref in fetched_data:
        try:
            fetched_data[ref] = {
                **fetched_data[ref],
                **convert_ws_object(fetched_data[ref]),
            }
        except (ValueError, RuntimeError) as e:
            errors.append(e.args[0])

    if errors:
        errors = ["Errors running data conversion for the Combinatrix:", *errors]
        big_error_message = "\n".join(errors)
        raise RuntimeError(big_error_message)

    return fetched_data


def convert_ws_object(object_data: dict[str, Any]) -> dict[str, Any]:
    """Convert workspace data into a tabular form for further processing.

    :param object_data: the workspace data for an object
    :type object_data: dict[str, dict[str, Any]]
    :raises ValueError: if there is any issue in finding an appropriate converter
    :return: amended object_data structure with info in tabular form
    :rtype: dict[str, dict[str, Any]]
    """
    converters = {
        "SampleSet": convert_samples,
        "Matrix": convert_matrix,
    }

    object_data_type = get_data_type(object_data)
    matching_converters = [k for k in converters if k in object_data_type]
    if len(matching_converters) != 1:
        err_msg = f"{get_upa(object_data)}: no dedicated converter found for {object_data_type}"
        raise RuntimeError(err_msg)

    conv = matching_converters[0]
    # run the converter
    return converters[conv](object_data)


def convert_samples(object_data: dict[str, Any]) -> dict[str, Any]:
    """Parse sample data and flatten it out for combinatrixing.

    :param sample_list: the `sample_data` value
    :type sample_list: list[dict[str, Any]]
    :return: dict containing the fieldnames and a list of samples data dicts
    :rtype: dict[str, Any]
    """
    sample_data = object_data.get(DATA, {}).get("sample_data")
    if not sample_data:
        err_msg = f"{get_upa(object_data)}: no 'data.sample_data' field found"
        raise ValueError(err_msg)

    keys = {
        "all": set(),
        "user": set(),
        "controlled": set(),
    }
    parsed_samples = []
    for sample in sample_data:
        sample_data = deepcopy(sample)
        del sample_data["node_tree"]

        # move the interesting data from under 'node_tree' up
        sample_name = sample["name"]
        sample_node_trees = [
            nt for nt in sample["node_tree"] if sample_name == nt["id"]
        ]
        if len(sample_node_trees) != 1:
            err_msg = f"{get_upa(object_data)}: incorrect number of sample node trees for sample {sample['id']}, {sample['name']}"
            raise ValueError(err_msg)

        snt = sample_node_trees[0]
        sample_data["type"] = snt["type"]

        # the data is in `snt` under the keys
        # "meta_controlled" and "meta_user"
        for key_type in ["user", "controlled"]:
            m_key = f"meta_{key_type}"
            if m_key in snt and snt.get(m_key, []):
                keys[key_type].update(snt.get(m_key).keys())
                for key in snt.get(m_key, []):
                    node_value = snt[m_key][key]
                    value = None
                    # check if it's in value/units form
                    if set(node_value.keys()) == {"value", "units"}:
                        value = f"{node_value['value']} {node_value['units']}"
                    elif set(node_value.keys()) == {"value"}:
                        value = node_value["value"]
                    else:
                        print(
                            f"unrecognised configuration: keys: {', '.join(node_value.keys())}"
                        )
                        value = json.dumps(node_value, indent=0)
                    sample_data[key] = value

        parsed_samples.append(sample_data)
        keys["all"].update(sample_data.keys())

    return {
        KEYS: {
            "controlled": keys["controlled"],
            "user": keys["user"],
        },
        FN: keys["all"],
        DL: parsed_samples,
    }


def convert_matrix(object_data: dict[str, Any]) -> dict[str, Any]:
    """Convert matrix data (as a dataframe-type rows/cols/values dump) into a list of lists.

    :param object_data: source, a dictionary with keys 'row_ids', 'col_ids', and 'values'
    :type object_data: dict[str, Any]
    :raises ValueError: if any of the required keys are not found
    :return: the dataset reorganised as a list of dicts (with an 'id' field added), a set of fieldnames.
    :rtype: list[list[Any]]
    """
    matrix_data = object_data.get(DATA, {}).get(DATA)
    if not matrix_data:
        err_msg = f"{get_upa(object_data)}: no 'data.data' field found"
        raise ValueError(err_msg)
    # ensure we have the correct keys
    missing_keys = [
        k for k in ["col_ids", "row_ids", "values"] if not matrix_data.get(k)
    ]
    if missing_keys:
        err_msg = (
            f"{get_upa(object_data)}: 'data.data' is missing required keys: "
            + ", ".join(missing_keys)
        )
        raise ValueError(err_msg)

    matrix_as_dicts = []
    # Iterate through the data and create dictionaries
    for i, column_id in enumerate(matrix_data["col_ids"]):
        for j, row_id in enumerate(matrix_data["row_ids"]):
            # Access the corresponding value from the nested list
            value = matrix_data["values"][j][i]
            # add in a generated ID
            entry = {
                "id": f"{column_id}___{row_id}___{value}",
                "column_id": column_id,
                "row_id": row_id,
                "value": value,
            }
            matrix_as_dicts.append(entry)

    return {
        FN: {"id", "column_id", "row_id", "value"},
        DL: matrix_as_dicts,
    }


def convert_list_of_dicts_to_list_of_lists(
    dict_list: list[dict[str, Any]], fieldnames: set[str] | list[str]
) -> list[list[Any]]:
    """Convert a list of dictionaries to a list of lists, ready for datatables.

    :param dict_list: list of dictionaries
    :type dict_list: list[dict[str, Any]]
    :param fieldnames: list or set containing all fieldnames present in the dicts
    :type fieldnames: set[str] | list[str]
    :return: list of lists containing all the data. Includes a header row.
    :rtype: list[list[Any]]
    """
    if not dict_list or not fieldnames:
        err_msg = "Must supply both a list of dictionaries and fieldnames for conversion to a list of lists"
        raise ValueError(err_msg)

    header_row = resort_fieldnames(fieldnames)

    all_rows = [
        [data_dict.get(header, None) for header in header_row]
        for data_dict in dict_list
    ]

    return [header_row, *all_rows]


def json_to_csv(json_file: str) -> None:
    """Convert a JSON file to CSV.

    :param json_file: path to the JSON file for conversion
    :type json_file: str
    """
    # Read the JSON file
    with open(json_file) as file:
        data = json.load(file)

    # Define the CSV file name (same as JSON but with .csv extension)
    csv_file = json_file.rsplit(".", 1)[0] + ".csv"

    return save_as_csv(data, csv_file)


def save_as_csv(data: dict[str, Any], csv_file: str) -> str:
    """Save a (possibly unparsed) workspace object to a CSV file.

    :param data: workspace object
    :type data: dict[str, Any]
    :param csv_file: full path of the CSV file
    :type csv_file: str
    :raises ValueError: if the WS object is not in a known format
    :return: full path of the new file
    :rtype: str
    """
    if not data[DL] or not data[FN]:
        err_msg = "Must supply both a list of dictionaries and fieldnames for conversion to CSV"
        raise ValueError(err_msg)

    fieldnames = resort_fieldnames(data[FN])

    path_to_file = csv_file if os.path.isabs(csv_file) else os.path.abspath(csv_file)

    # Write the data to a CSV file
    with open(path_to_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, restval=None)
        writer.writeheader()
        writer.writerows(data[DL])

    return path_to_file
