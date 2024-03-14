"""Test parameter checks and reordering."""

from test.conftest import TEST_UPA, paramify
from typing import Any

import pytest
from combinatrix.constants import (
    FIELD,
    JOIN_LIST,
    PARAM_ERROR_MESSAGE,
    REF,
    REFS,
    REQD_FIELDS,
    T1,
    T2,
)
from combinatrix.core import AppCore
from combinatrix.param_checker import (
    check_params,
    construct_graph,
    sort_params,
    validate_params,
)

REF_A = "ref_a"
REF_B = "ref_b"
REF_C = "ref_c"
REF_D = "ref_d"
REF_E = "ref_e"
REF_F = "ref_f"

A = "a"
B = "b"
C = "c"
Z = "z"
Y = "y"
X = "x"
L = "l"
M = "m"
N = "n"

FIELD_A = "some_field"
FIELD_B = "blah blah blah"
FIELD_B_EDIT = "blah_blah_blah"
FIELD_C = "Mr Blobby"
FIELD_C_EDIT = "mr_blobby"
FIELD_AMPL = "some_other_field"

SSA = "SAMPLESET_A"
SSB = "SAMPLESET_B"
AMP = "AMPLICON"

VALID_JOIN_DICT_A = {
    f"{T1}_{REF}": TEST_UPA[SSA],
    f"{T1}_{FIELD}": FIELD_A,
    f"{T2}_{REF}": TEST_UPA[AMP],
    f"{T2}_{FIELD}": FIELD_AMPL,
}

VALID_JOIN_DICT_B = {
    f"{T1}_{REF}": TEST_UPA[SSB],
    f"{T1}_{FIELD}": "    " + FIELD_B + "\n\r\n",
    f"{T2}_{REF}": "   " + TEST_UPA[SSA] + "  \n\n\n",
    f"{T2}_{FIELD}": FIELD_C,
}

VALID_JOIN_DICT_A_CLEANED = {
    T1: {REF: TEST_UPA[SSA], FIELD: FIELD_A},
    T2: {REF: TEST_UPA[AMP], FIELD: FIELD_AMPL},
}

VALID_JOIN_DICT_B_CLEANED = {
    T1: {REF: TEST_UPA[SSB], FIELD: FIELD_B_EDIT},
    T2: {REF: TEST_UPA[SSA], FIELD: FIELD_C_EDIT},
}

VALID_JOIN_LIST_A_B_ORDERED = [
    {
        T1: {REF: TEST_UPA[AMP], FIELD: FIELD_AMPL},
        T2: {REF: TEST_UPA[SSA], FIELD: FIELD_A},
    },
    {
        T1: {REF: TEST_UPA[SSA], FIELD: FIELD_C_EDIT},
        T2: {REF: TEST_UPA[SSB], FIELD: FIELD_B_EDIT},
    },
]


@pytest.mark.parametrize(
    "params",
    paramify(
        [
            {"input": None, "id": "none"},
            {"input": {}, "id": "empty_dict"},
            {"input": {"this": "that"}, "id": "invalid_keys"},
        ]
    ),
)
def test_check_params_none(params: dict[str, Any]) -> None:
    """Test that submitting no params throws an error."""
    with pytest.raises(
        RuntimeError, match=f"{PARAM_ERROR_MESSAGE}no '{JOIN_LIST}' parameter found"
    ):
        check_params(params["input"])


@pytest.mark.parametrize(
    "params",
    paramify(
        [
            {
                "input": {
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A,
                        {
                            f"{T1}_{REF}": "1/2/3",
                            f"{T1}_{FIELD}": "blah",
                            f"{T2}_{REF}": "1/2/3",
                            f"{T2}_{FIELD}": "blob",
                        },
                    ],
                },
                "err": ["1/2/3 cannot be joined to itself"],
                "id": "identical_t1_t2",
            },
            {
                "input": {
                    JOIN_LIST: [
                        {
                            f"{T2}_{REF}": "   ",
                            f"{T2}_{FIELD}": None,
                            f"{T1}_{FIELD}": "",
                        }
                    ]
                },
                "err": [
                    f"Invalid value for {T1}_{REF}: 'None'",
                    f"Invalid value for {T1}_{FIELD}: ''",
                    f"Invalid value for {T2}_{REF}: '   '",
                    f"Invalid value for {T2}_{FIELD}: 'None'",
                ],
                "id": "blank_or_missing",
            },
            {
                "input": {JOIN_LIST: []},
                "err": ["no valid join data found"],
                "id": "empty_join_list",
            },
            {
                "input": {
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A,
                        {
                            f"{T1}_{REF}": "1/2/4",
                            f"{T1}_{FIELD}": "blah",
                            f"{T2}_{REF}": "1/2/5",
                            f"{T2}_{FIELD}": "blob",
                        },
                        {
                            f"{T1}_{REF}": "1/2/6",
                            f"{T1}_{FIELD}": "blah",
                            f"{T2}_{REF}": "1/2/7",
                            f"{T2}_{FIELD}": "blob",
                        },
                        {
                            f"{T1}_{REF}": "1/2/8",
                            f"{T1}_{FIELD}": "blah",
                            f"{T2}_{REF}": "1/2/9",
                            f"{T2}_{FIELD}": "blob",
                        },
                    ],
                },
                "err": [
                    "The Combinatrix is currently limited to combining 3 datasets."
                ],
                "id": "too_many_joins",
            },
        ]
    ),
)
def test_check_params_fail(params: dict[str, Any], app_core: AppCore) -> None:
    """Check for various input parameter errors."""
    with pytest.raises(
        RuntimeError,
        match="Combinatrix encountered the following errors in the input parameters:\n"
        + "\n".join(params["err"]),
    ):
        app_core.run(params["input"])


@pytest.mark.parametrize(
    "params",
    paramify(
        [
            {
                "input": {
                    JOIN_LIST: [VALID_JOIN_DICT_A, VALID_JOIN_DICT_B],
                },
                "output": {
                    REFS: {TEST_UPA[ref] for ref in [SSA, AMP, SSB]},
                    JOIN_LIST: [VALID_JOIN_DICT_A_CLEANED, VALID_JOIN_DICT_B_CLEANED],
                    REQD_FIELDS: {
                        TEST_UPA[SSB]: {FIELD_B_EDIT},
                        TEST_UPA[SSA]: {FIELD_A, FIELD_C_EDIT},
                        TEST_UPA[AMP]: {FIELD_AMPL},
                    },
                },
                "id": "despaced",
            },
            {
                "input": {
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A,
                        VALID_JOIN_DICT_A,
                        VALID_JOIN_DICT_A,
                        VALID_JOIN_DICT_A,
                    ],
                },
                "output": {
                    REFS: {TEST_UPA[SSA], TEST_UPA[AMP]},
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A_CLEANED,
                    ],
                    REQD_FIELDS: {
                        TEST_UPA[AMP]: {FIELD_AMPL},
                        TEST_UPA[SSA]: {FIELD_A},
                    },
                },
                "id": "repeated_entry",
            },
            {
                "input": {
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A,
                        {
                            f"{T2}_{REF}": TEST_UPA[SSA],
                            f"{T2}_{FIELD}": FIELD_A,
                            f"{T1}_{REF}": TEST_UPA[AMP],
                            f"{T1}_{FIELD}": FIELD_AMPL,
                        },
                    ],
                },
                "output": {
                    REFS: {TEST_UPA[SSA], TEST_UPA[AMP]},
                    JOIN_LIST: [
                        VALID_JOIN_DICT_A_CLEANED,
                    ],
                    REQD_FIELDS: {
                        TEST_UPA[AMP]: {FIELD_AMPL},
                        TEST_UPA[SSA]: {FIELD_A},
                    },
                },
                "id": "ignore_reversed",
            },
            {
                "input": {
                    JOIN_LIST: [
                        {
                            f"{T2}_{REF}": TEST_UPA[SSA],
                            f"{T2}_{FIELD}": "id",
                            f"{T1}_{REF}": TEST_UPA[AMP],
                            f"{T1}_{FIELD}": "col_id",
                        },
                    ],
                },
                "output": {
                    REFS: {TEST_UPA[SSA], TEST_UPA[AMP]},
                    JOIN_LIST: [
                        {
                            T2: {REF: TEST_UPA[SSA], FIELD: "name"},
                            T1: {REF: TEST_UPA[AMP], FIELD: "column_id"},
                        },
                    ],
                    REQD_FIELDS: {
                        TEST_UPA[AMP]: {"column_id"},
                        TEST_UPA[SSA]: {"name"},
                    },
                },
                "id": "name_coercion",
            },
            {
                "input": {
                    JOIN_LIST: [
                        {
                            f"{T2}_{REF}": TEST_UPA[SSA],
                            f"{T2}_{FIELD}": "row",
                            f"{T1}_{REF}": TEST_UPA[AMP],
                            f"{T1}_{FIELD}": "column",
                        },
                    ],
                },
                "output": {
                    REFS: {TEST_UPA[SSA], TEST_UPA[AMP]},
                    JOIN_LIST: [
                        {
                            T2: {REF: TEST_UPA[SSA], FIELD: "row_id"},
                            T1: {REF: TEST_UPA[AMP], FIELD: "column_id"},
                        },
                    ],
                    REQD_FIELDS: {
                        TEST_UPA[AMP]: {"column_id"},
                        TEST_UPA[SSA]: {"row_id"},
                    },
                },
                "id": "more_name_coercion",
            },
        ]
    ),
)
def test_validate_params(params: dict[str, Any]) -> None:
    """Ensure that input params are coerced correctly."""
    assert validate_params(params["input"]) == params["output"]


def test_validate_params_with_max_refs() -> None:
    """Ensure that the max_refs value is respected."""
    input_params = {
        JOIN_LIST: [
            {
                f"{T1}_{REF}": REF_A,
                f"{T1}_{FIELD}": X,
                f"{T2}_{REF}": REF_B,
                f"{T2}_{FIELD}": X,
            },
            {
                f"{T1}_{REF}": REF_C,
                f"{T1}_{FIELD}": X,
                f"{T2}_{REF}": REF_D,
                f"{T2}_{FIELD}": X,
            },
            {
                f"{T1}_{REF}": REF_E,
                f"{T1}_{FIELD}": X,
                f"{T2}_{REF}": REF_F,
                f"{T2}_{FIELD}": X,
            },
            {
                f"{T1}_{REF}": REF_C,
                f"{T1}_{FIELD}": X,
                f"{T2}_{REF}": REF_B,
                f"{T2}_{FIELD}": X,
            },
            {
                f"{T1}_{REF}": REF_D,
                f"{T1}_{FIELD}": X,
                f"{T2}_{REF}": REF_E,
                f"{T2}_{FIELD}": X,
            },
        ]
    }

    ref_set = {REF_A, REF_B, REF_C, REF_D, REF_E, REF_F}
    output = validate_params(input_params, 6)
    assert output[REFS] == ref_set
    assert output[REQD_FIELDS] == {item: {X} for item in ref_set}

    with pytest.raises(
        RuntimeError,
        match="The Combinatrix is currently limited to combining 5 datasets.",
    ):
        validate_params(input_params, 5)

    # default value
    with pytest.raises(
        RuntimeError,
        match="The Combinatrix is currently limited to combining 3 datasets.",
    ):
        validate_params(input_params)


def test_construct_graph_valid_minimal() -> None:
    """Construct a graph from minimal valid parameters."""
    input_params = [
        {T1: {REF: REF_A}, T2: {REF: REF_B}},
    ]
    join_graph = construct_graph(input_params)
    assert len(join_graph.edges) == len(input_params)
    assert set(join_graph.nodes) == {REF_A, REF_B}


def test_construct_graph_valid() -> None:
    """Construct a graph from valid parameters."""
    input_params = [
        {T1: {REF: REF_A}, T2: {REF: REF_B}},
        {T1: {REF: REF_C}, T2: {REF: REF_B}},
        {T1: {REF: REF_C}, T2: {REF: REF_D}},
        {T1: {REF: REF_E}, T2: {REF: REF_F}},
        {T1: {REF: REF_D}, T2: {REF: REF_E}},
    ]
    join_graph = construct_graph(input_params)
    assert len(join_graph.edges) == len(input_params)
    assert set(join_graph.nodes) == {REF_A, REF_B, REF_C, REF_D, REF_E, REF_F}


def test_construct_graph_fail_too_many_connections() -> None:
    """Test failure due to too many connections to a ref."""
    input_params = [
        {T1: {REF: REF_A}, T2: {REF: REF_B}},
        {T1: {REF: REF_A}, T2: {REF: REF_C}},
        {T1: {REF: REF_A}, T2: {REF: REF_D}},
        {T1: {REF: REF_E}, T2: {REF: REF_D}},
        {T1: {REF: REF_F}, T2: {REF: REF_D}},
    ]
    with pytest.raises(
        RuntimeError,
        match=f"The following refs are connected to too many other refs:\n{REF_A}, {REF_D}",
    ):
        construct_graph(input_params)


@pytest.mark.parametrize(
    "param",
    [
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},
                    {T1: {REF: REF_E}, T2: {REF: REF_F}},  # Disconnected component
                ]
            },
            id="disconnected_component",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},
                    {T1: {REF: REF_B}, T2: {REF: REF_C}},
                    {T1: {REF: REF_C}, T2: {REF: REF_A}},  # cycle
                ]
            },
            id="cycle",
        ),
    ],
)
def test_sort_params_fail(param: dict[str, Any]) -> None:
    """Ensure that a disconnected or cyclical graph raises an error."""
    with pytest.raises(
        RuntimeError, match="Error: the joins specified do not create a single dataset"
    ):
        sort_params(param["input"])


EXPECTED_OUTPUT = [
    {T1: {REF: REF_A}, T2: {REF: REF_B}},
    {T1: {REF: REF_B}, T2: {REF: REF_C}},
    {T1: {REF: REF_C}, T2: {REF: REF_D}},
]

INVERTED_OUTPUT = [
    {T1: {REF: REF_D}, T2: {REF: REF_C}},
    {T1: {REF: REF_C}, T2: {REF: REF_B}},
    {T1: {REF: REF_B}, T2: {REF: REF_A}},
]


@pytest.mark.parametrize(
    "param",
    [
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},
                    {T1: {REF: REF_B}, T2: {REF: REF_C}},
                    {T1: {REF: REF_C}, T2: {REF: REF_D}},
                ]
            },
            id="no_reorder_standard",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_D}, T2: {REF: REF_C}},
                    {T1: {REF: REF_C}, T2: {REF: REF_B}},
                    {T1: {REF: REF_B}, T2: {REF: REF_A}},
                ],
                "output": INVERTED_OUTPUT,
            },
            id="no_reorder_inverted",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_B}, T2: {REF: REF_C}},
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},  # out of order
                    {T1: {REF: REF_C}, T2: {REF: REF_D}},
                ]
            },
            id="incorrect_list_order",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_C}, T2: {REF: REF_B}},  # inverted pair
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},
                    {T1: {REF: REF_D}, T2: {REF: REF_C}},  # inverted
                ]
            },
            id="incorrect_pair_order",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_C}, T2: {REF: REF_B}},  # inverted pair
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},  # out of order
                    {T1: {REF: REF_D}, T2: {REF: REF_C}},  # inverted
                ],
                "output": EXPECTED_OUTPUT,
            },
            id="incorrect_list_pair_standard_order",
        ),
        pytest.param(
            {
                "input": [
                    {T1: {REF: REF_D}, T2: {REF: REF_C}},
                    {T1: {REF: REF_A}, T2: {REF: REF_B}},
                    {T1: {REF: REF_C}, T2: {REF: REF_B}},
                ],
                "output": INVERTED_OUTPUT,
            },
            id="incorrect_list_pair_inverted",
        ),
    ],
)
def test_sort_params_incorrect_list_pair_order(param: dict[str, Any]) -> None:
    """Correct a list with both pairs and the list itself being incorrectly ordered."""
    expected = param.get("output", EXPECTED_OUTPUT)
    assert sort_params(param["input"]) == expected


@pytest.mark.parametrize(
    "param",
    [
        pytest.param(
            {
                "input": {JOIN_LIST: [VALID_JOIN_DICT_A, VALID_JOIN_DICT_B]},
                "output": {
                    JOIN_LIST: VALID_JOIN_LIST_A_B_ORDERED,
                    REFS: {
                        TEST_UPA[SSA],
                        TEST_UPA[SSB],
                        TEST_UPA[AMP],
                    },
                    REQD_FIELDS: {
                        TEST_UPA[SSA]: {FIELD_A, FIELD_C_EDIT},
                        TEST_UPA[SSB]: {FIELD_B_EDIT},
                        TEST_UPA[AMP]: {FIELD_AMPL},
                    },
                },
            },
            id="invert_order",
        )
    ],
)
def test_check_params(param: dict[str, Any]) -> None:
    """Check the whole thing."""
    assert check_params(param["input"]) == param["output"]
