"""Tests for the converter."""

from typing import Any

import pytest
from combinatrix.constants import DATA, DL, FN, INFO
from combinatrix.converter import (
    convert_data,
    convert_list_of_dicts_to_list_of_lists,
    convert_matrix,
    convert_samples,
    convert_ws_object,
)
from combinatrix.util import get_upa

UPA_DATA = {
    INFO: {
        "objid": 89,
        "version": 67,
        "wsid": 12345,
    }
}


@pytest.mark.parametrize(
    "param",
    [
        "sample_set",
        "KBaseMatrix.SampleSet-1.1",
        "SomeRandomMadeUpType-6.66",
    ],
)
def test_convert_ws_object_fail(param: str) -> None:
    """Check that data types without a converter or with too many converters throw an error."""
    with pytest.raises(
        RuntimeError,
        match=f"12345/89/67: no dedicated converter found for {param}",
    ):
        convert_ws_object(
            {
                INFO: {
                    "type": param,
                    "objid": 89,
                    "version": 67,
                    "wsid": 12345,
                }
            },
        )


@pytest.mark.parametrize(
    (DL, FN, "expected"),
    [
        ([{"a": 1, "b": 2}], {"a", "b"}, [["a", "b"], [1, 2]]),
        (
            [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
            {"a", "b"},
            [["a", "b"], [1, 2], [3, 4]],
        ),
        ([{"a": 1, "b": 2}, {"a": 3}], {"a", "b"}, [["a", "b"], [1, 2], [3, None]]),
        ([{"a": 1, "b": 2}, {"a": 3}], ["a", "b"], [["a", "b"], [1, 2], [3, None]]),
        (
            [
                {"a": 1, "b": 2, "name": "blah", "id": 12345},
                {"a": 3, "id": 12365},
                {"b": 2, "name": "blob"},
            ],
            {"a", "b", "id", "name"},
            [
                ["id", "name", "a", "b"],
                [12345, "blah", 1, 2],
                [12365, None, 3, None],
                [None, "blob", None, 2],
            ],
        ),
        (
            [{"a": 1, "b": 2, "id": 123}, {"id": 124, "a": 3}],
            ["id", "a", "b"],
            [["id", "a", "b"], [123, 1, 2], [124, 3, None]],
        ),
        (
            [{"a": 1, "b": 2}, {"a": 3}],
            ["b", "a"],
            [["a", "b"], [1, 2], [3, None]],
        ),
        ([{}, {}], ["b", "a"], [["a", "b"], [None, None], [None, None]]),
    ],
)
def test_convert_list_of_dicts_to_list_of_lists(
    dict_list: list[dict[str, Any]], fieldnames: set[str], expected: list[list[Any]]
) -> None:
    """Check that a list of dicts is correctly converted to a list of lists."""
    result = convert_list_of_dicts_to_list_of_lists(dict_list, fieldnames)
    assert result == expected


@pytest.mark.parametrize(
    (DL, FN),
    [([], set()), ([{"a": 1, "b": 2}], set()), ([], {"a", "b"})],
)
def test_convert_list_of_dicts_to_list_of_lists_fail(
    dict_list: list[dict[str, Any]],
    fieldnames: set[str],
) -> None:
    """Check that an error is thrown if the dict_list or the fieldnames are empty."""
    with pytest.raises(
        ValueError,
        match="Must supply both a list of dictionaries and fieldnames for conversion to a list of lists",
    ):
        convert_list_of_dicts_to_list_of_lists(dict_list, fieldnames)


EXAMPLE_MATRIX = {
    "col_ids": ["A", "B"],
    "row_ids": ["X", "Y"],
    "values": [[1, 2], [3, 4]],
}

EXPECTED_DICT_LIST = [
    {"column_id": "A", "row_id": "X", "value": 1, "id": "A___X___1"},
    {"column_id": "A", "row_id": "Y", "value": 3, "id": "A___Y___3"},
    {"column_id": "B", "row_id": "X", "value": 2, "id": "B___X___2"},
    {"column_id": "B", "row_id": "Y", "value": 4, "id": "B___Y___4"},
]


def test_convert_matrix() -> None:
    """Ensure that matrices are correctly converted."""
    matrix = {DATA: {DATA: EXAMPLE_MATRIX}}
    result = convert_matrix(matrix)
    data_result = convert_ws_object(
        {INFO: {"type": "SuperCoolMatrix"}, DATA: {DATA: EXAMPLE_MATRIX}}
    )

    # Check if the fieldnames set contains the expected fields
    expected_fieldnames = {"id", "column_id", "row_id", "value"}
    assert result[FN] == expected_fieldnames
    assert data_result[FN] == result[FN]

    # Check if the dict_list is generated correctly
    assert result[DL] == EXPECTED_DICT_LIST
    assert data_result[DL] == result[DL]


@pytest.mark.parametrize(
    "param",
    [
        {**UPA_DATA},
        {**UPA_DATA, DATA: {}},
        {**UPA_DATA, DATA: {DATA: None}},
        {**UPA_DATA, DATA: {DATA: {}}},
    ],
)
def test_convert_matrix_fail_no_data(param: dict[str, Any]) -> None:
    """Failure scenarios for matrix conversion."""
    with pytest.raises(ValueError, match="12345/89/67: no 'data.data' field found"):
        convert_matrix(param)


@pytest.mark.parametrize(
    "param",
    [
        pytest.param(
            {
                "input": {**UPA_DATA, DATA: {DATA: {"key": "value"}}},
                "err_msg": "col_ids, row_ids, values",
            },
            id="no_keys",
        ),
        pytest.param(
            {
                "input": {
                    **UPA_DATA,
                    DATA: {DATA: {"col_ids": [], "row_ids": None}},
                },
                "err_msg": "col_ids, row_ids, values",
            },
            id="empty_values",
        ),
        pytest.param(
            {
                "input": {
                    **UPA_DATA,
                    DATA: {DATA: {"col_ids": [1, 2, 3], "row_ids": [1, 2, 3]}},
                },
                "err_msg": "values",
            },
            id="one_missing",
        ),
    ],
)
def test_convert_matrix_fail_missing_keys(param: dict[str, Any]) -> None:
    """Invalid data.data structures."""
    with pytest.raises(
        ValueError,
        match="12345/89/67: 'data.data' is missing required keys: " + param["err_msg"],
    ):
        convert_matrix(param["input"])


@pytest.mark.parametrize(
    "test_file",
    [
        "samples_b",
        "samples_all_controlled",
        "samples_no_fields",
        "samples_node_tree_multiple_under_node",
    ],
)
def test_convert_samples(request: pytest.FixtureRequest, test_file: str) -> None:
    """Check that a sample set can be converted into the appropriate format."""
    fixture_value = request.getfixturevalue(test_file)

    output = convert_samples(fixture_value["input"])
    assert fixture_value["output"] == output


@pytest.mark.parametrize(
    "param",
    [
        {**UPA_DATA},
        {**UPA_DATA, DATA: {}},
        {**UPA_DATA, DATA: {"sample_data": None}},
        {**UPA_DATA, DATA: {"sample_data": []}},
    ],
)
def test_convert_sample_fail_no_data(param: dict[str, Any]) -> None:
    """Failure scenarios for sample conversion."""
    with pytest.raises(
        ValueError, match="12345/89/67: no 'data.sample_data' field found"
    ):
        convert_samples(param)


@pytest.mark.parametrize(
    "test_file", ["samples_node_tree_0", "samples_node_tree_multiple"]
)
def test_convert_sample_fail_no_node_trees(
    request: pytest.FixtureRequest, test_file: str
) -> None:
    """Incorrect number of node trees for a given sample ID."""
    fixture_value = request.getfixturevalue(test_file)
    with pytest.raises(
        ValueError,
        match=fixture_value["error"],
    ):
        convert_samples(fixture_value["input"])


def test_convert_data_all_ok(
    samples_b: dict[str, Any],
    samples_all_controlled: dict[str, Any],
    samples_no_fields: dict[str, Any],
    samples_node_tree_multiple_under_node: dict[str, Any],
) -> None:
    """Ensure that all data is converted correctly."""
    matrix_data = {
        INFO: {"type": "AwesomeMatrix", "wsid": 12345, "objid": 67890, "version": 1},
        DATA: {DATA: EXAMPLE_MATRIX},
    }
    function_input = {get_upa(matrix_data): matrix_data}
    expected = {
        get_upa(matrix_data): {
            **matrix_data,
            FN: {"id", "column_id", "row_id", "value"},
            DL: EXPECTED_DICT_LIST,
        }
    }

    files_by_ref = {
        "12345/100/1": samples_all_controlled,
        "12345/1/1": samples_b,
        "12345/9/1": samples_no_fields,
        "12345/6/1": samples_node_tree_multiple_under_node,
    }

    for ref in files_by_ref:
        test_case = files_by_ref[ref]
        function_input[ref] = test_case["input"]
        expected[ref] = {**test_case["input"], **test_case["output"]}

    assert expected == convert_data(function_input)


def test_convert_data_fail_no_node_trees(
    samples_node_tree_0: dict[str, Any], samples_node_tree_multiple: dict[str, Any]
) -> None:
    """Incorrect number of node trees for a given sample ID."""
    function_input = {
        "samples_node_tree_0": samples_node_tree_0["input"],
        "samples_node_tree_multiple": samples_node_tree_multiple["input"],
    }

    with pytest.raises(
        RuntimeError,
        match="Errors running data conversion for the Combinatrix:",
    ) as e:
        convert_data(function_input)
    error_msg = e.value.args[0]
    assert samples_node_tree_multiple["error"] in error_msg
    assert samples_node_tree_0["error"] in error_msg
