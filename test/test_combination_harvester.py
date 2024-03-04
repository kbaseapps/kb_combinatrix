"""Tests for combining data."""

from test.conftest import TEST_UPA, paramify
from typing import Any

import pytest
from combinatrix.combination_harvester import combine_data
from combinatrix.constants import (
    DL,
    FIELD,
    FN,
    JOIN_LIST,
    REF,
    REQD_FIELDS,
    T1,
    T2,
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
ID = "id"
FIELD_A = "some_field"
FIELD_B = "blah blah blah"
FIELD_B_EDIT = "blah_blah_blah"
FIELD_C = "Mr Blobby"
FIELD_C_EDIT = "mr_blobby"
FIELD_AMPL = "some_other_field"

VALID_JOIN_DICT = {
    f"{T1}_{REF}": TEST_UPA["SAMPLESET_A"],
    f"{T1}_{FIELD}": FIELD_A,
    f"{T2}_{REF}": TEST_UPA["AMPLICON"],
    f"{T2}_{FIELD}": FIELD_AMPL,
}

VALID_JOIN_DICT_CLEANED = {
    T1: {REF: TEST_UPA["SAMPLESET_A"], FIELD: FIELD_A},
    T2: {REF: TEST_UPA["AMPLICON"], FIELD: FIELD_AMPL},
}

DATA_REF = {
    "A": [
        {ID: "a0", A: "pip", B: "snap", C: "chump"},
        {ID: "a1", A: "pap", B: "snip", C: "champ"},
        {ID: "a2", A: "pop", B: "snxp", C: "chimp"},
    ],
    "B": [
        {ID: "b0", Z: 1, Y: "chimp", X: "pop"},
        {ID: "b1", Z: 4, Y: "chump", X: "pip"},
        {ID: "b2", Z: 7, Y: "chomp", X: "pip"},
    ],
    "C": [
        {ID: "c0", L: 1, M: "chump", N: "snop"},
        {ID: "c1", L: 4, M: "chimp", N: "snip"},
        {ID: "c2", L: 7, M: "chump", N: "snap"},
    ],
}
FETCHED_DATA = {
    REF_A: {FN: {A, B, C}, DL: DATA_REF["A"]},
    REF_B: {FN: {X, Y, Z}, DL: DATA_REF["B"]},
    REF_C: {FN: {L, M, N}, DL: DATA_REF["C"]},
    REF_D: {FN: {A, B, C}, DL: DATA_REF["A"]},
    REF_E: {FN: {X, Y, Z}, DL: DATA_REF["B"]},
    REF_F: {FN: {L, M, N}, DL: DATA_REF["C"]},
}


@pytest.mark.parametrize(
    "param",
    paramify(
        [
            {
                "join": {REQD_FIELDS: {REF_A: {A}, REF_B: {"not_found"}}},
                "err_msg": "ref_b: fields not found: not_found",
                "id": "one_not_found",
            },
            {
                "join": {
                    REQD_FIELDS: {
                        REF_A: {A, "not_found"},
                        REF_B: {B},
                    }
                },
                "err_msg": "ref_a: fields not found: not_found",
                "id": "one_valid_one_not_found",
            },
            {
                "join": {
                    REQD_FIELDS: {
                        REF_A: {"zebra", "this"},
                        REF_B: {"that", "wildebeest"},
                    }
                },
                "err_msg": "ref_a: fields not found: this, zebra\nref_b: fields not found: that, wildebeest",
                "id": "multiple_not_found",
            },
        ]
    ),
)
def test_combine_data_fail_fields_not_found(param: dict[str, Any]) -> None:
    """Ensure that combination fails if one or other of the data sources lacks the correct fields."""
    with pytest.raises(
        RuntimeError,
        match=f"Errors in dataset field specifications:\n{param['err_msg']}",
    ):
        combine_data(param["join"], FETCHED_DATA)


@pytest.mark.parametrize(
    "param",
    paramify(
        [
            {
                "join": {
                    REQD_FIELDS: {REF_A: {B}, REF_B: {Y}},
                    JOIN_LIST: [
                        {  # A-B fail
                            T1: {REF: REF_A, FIELD: B},
                            T2: {REF: REF_B, FIELD: Y},
                        }
                    ],
                },
                "err_msg": f"{REF_A} '{B}' and {REF_B} '{Y}'",
                "id": "one_join_no_isect",
            },
            {
                "join": {
                    REQD_FIELDS: {
                        REF_A: {A},
                        REF_B: {X, Y},
                        REF_C: {L},
                    },
                    JOIN_LIST: [
                        {  # A-B OK
                            T1: {REF: REF_A, FIELD: A},
                            T2: {REF: REF_B, FIELD: X},
                        },
                        {  # B-C fail
                            T1: {REF: REF_B, FIELD: Y},
                            T2: {REF: REF_C, FIELD: L},
                        },
                    ],
                },
                "err_msg": f"{REF_B} '{Y}' and {REF_C} '{L}'",
                "id": "two_joins_one_isect",
            },
            {
                "join": {
                    REQD_FIELDS: {REF_A: {A, C}, REF_B: {Y, Z}, REF_C: {M}},
                    JOIN_LIST: [
                        {  # A-B fail
                            T1: {REF: REF_A, FIELD: A},
                            T2: {REF: REF_B, FIELD: Y},
                        },
                        {  # B-C fail
                            T1: {REF: REF_B, FIELD: Z},
                            T2: {REF: REF_C, FIELD: M},
                        },
                    ],
                },
                "err_msg": f"{REF_A} '{A}' and {REF_B} '{Y}'\n{REF_B} '{Z}' and {REF_C} '{M}'",
                "id": "two_joins_no_isect",
            },
            {
                "join": {
                    REQD_FIELDS: {REF_A: {A, C}, REF_B: {Y, X}, REF_C: {L}},
                    JOIN_LIST: [
                        {  # A-B OK
                            T1: {REF: REF_A, FIELD: A},
                            T2: {REF: REF_B, FIELD: X},
                        },
                        {  # A-C fail
                            T1: {REF: REF_A, FIELD: C},
                            T2: {REF: REF_C, FIELD: L},
                        },
                        {  # B-C fail
                            T1: {REF: REF_B, FIELD: Y},
                            T2: {REF: REF_C, FIELD: L},
                        },
                    ],
                },
                "err_msg": f"{REF_A} '{C}' and {REF_C} '{L}': You are trying to merge on object and int64 columns for key 'ref_a__c'. If you wish to proceed you should use pd.concat\n{REF_B} '{Y}' and {REF_C} '{L}': You are trying to merge on object and int64 columns for key 'ref_b__y'. If you wish to proceed you should use pd.concat",
                "id": "three_joins_one_isect",
            },
        ]
    ),
)
def test_combine_data_fail_no_intersections(param: dict[str, Any]) -> None:
    """Ensure that errors are thrown if there are no intersections between datasets."""
    with pytest.raises(
        RuntimeError,
        match="No matching values found between the following datasets:\n"
        + param["err_msg"],
    ):
        combine_data(param["join"], FETCHED_DATA)


@pytest.mark.parametrize(
    "param",
    paramify(
        [
            {
                "id": "three_set_join_two_missing",
                "input": {
                    JOIN_LIST: [
                        # B.X, A.A: T1: {"b0", "b1", "b2"}, T2: {"a0", "a2"}, b0==a2
                        {T1: {REF: REF_B, FIELD: X}, T2: {REF: REF_A, FIELD: A}},
                        # A.C, C.M: T1: {"a0", "a2"} T2: {"c0", "c1", "c2"}
                        {T1: {REF: REF_A, FIELD: C}, T2: {REF: REF_C, FIELD: M}},
                    ],
                    REQD_FIELDS: {REF_A: {A, C}, REF_B: {X}, REF_C: {M}},
                },
                "expected": {
                    REF_A: {"a0", "a2"},
                    REF_B: {"b0", "b1", "b2"},
                    REF_C: {"c0", "c1", "c2"},
                },
            },
            {
                "id": "three_set_join_one_missing",
                "input": {
                    JOIN_LIST: [
                        # A.A, B.X: T1: {"a0", "a2"}, T2: {"b0", "b1", "b2"}
                        {T1: {REF: REF_A, FIELD: A}, T2: {REF: REF_B, FIELD: X}},
                        # B.Z, C.L: T1: {"b0", "b1", "b2"}, T2: {"c0", "c1", "c2"}
                        {T1: {REF: REF_B, FIELD: Z}, T2: {REF: REF_C, FIELD: L}},
                    ],
                    REQD_FIELDS: {REF_A: {A}, REF_B: {X, Z}, REF_C: {L}},
                },
                "expected": {
                    REF_A: {"a0", "a2"},
                    REF_B: {"b0", "b1", "b2"},
                    REF_C: {"c0", "c1", "c2"},
                },
            },
            {
                "id": "two_set_join_missing",
                "input": {
                    JOIN_LIST: [
                        {T1: {REF: REF_A, FIELD: A}, T2: {REF: REF_B, FIELD: X}},
                    ],
                    REQD_FIELDS: {REF_A: {A}, REF_B: {X}},
                },
                "expected": {REF_A: {"a0", "a2"}, REF_B: {"b0", "b1", "b2"}},
            },
            {
                "id": "two_set_join_no_missing",
                "input": {
                    JOIN_LIST: [
                        {T1: {REF: REF_B, FIELD: Z}, T2: {REF: REF_C, FIELD: L}},
                    ],
                    REQD_FIELDS: {REF_B: {Z}, REF_C: {L}},
                },
                "expected": {
                    REF_B: {"b0", "b1", "b2"},
                    REF_C: {"c0", "c1", "c2"},
                },
            },
            {
                "id": "insane_six_table_join",
                "input": {
                    JOIN_LIST: [
                        # a0, a2, b0-2
                        {T1: {REF: REF_A, FIELD: A}, T2: {REF: REF_B, FIELD: X}},
                        # full overlap
                        {T1: {REF: REF_B, FIELD: Z}, T2: {REF: REF_C, FIELD: L}},
                        # c0-2, a0, a2
                        {T1: {REF: REF_C, FIELD: M}, T2: {REF: REF_D, FIELD: C}},
                        # a0, a2, b0, b1
                        {T1: {REF: REF_D, FIELD: C}, T2: {REF: REF_E, FIELD: Y}},
                        # full overlap
                        {T1: {REF: REF_E, FIELD: Z}, T2: {REF: REF_F, FIELD: L}},
                    ],
                    REQD_FIELDS: {
                        REF_A: {A},
                        REF_B: {X, Z},
                        REF_C: {L, M},
                        REF_D: {C},
                        REF_E: {Y, Z},
                        REF_F: {L},
                    },
                },
                "expected": {
                    REF_A: {"a0", "a2"},
                    REF_B: {"b0", "b1", "b2"},
                    REF_C: {"c0", "c1", "c2"},
                    REF_D: {"a0", "a2"},
                    REF_E: {"b0", "b1"},
                    REF_F: {"c0", "c1"},
                },
            },
        ]
    ),
)
def test_combine_data_success(param: dict[str, Any]) -> None:
    """Ensure that intersecting datasets do not throw an error."""
    output = combine_data(param["input"], FETCHED_DATA)
    assert output == param["expected"]
