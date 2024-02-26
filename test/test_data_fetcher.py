"""Tests for the data fetching code."""
import logging
from test.conftest import TEST_UPA, paramify
from test.conftest import body_match_vcr as vcr
from typing import Any

import pytest
from combinatrix.constants import DATA, INFO
from combinatrix.fetcher import DataFetcher

INVALID_DATA_FETCHER_PARAMS = [
    pytest.param([None, None], id="two_nones"),
    pytest.param([{}, {}], id="two_empty_dicts"),
    pytest.param([{"kbase-endpoint": "whatever"}, {"token": None}], id="no_token"),
    pytest.param([{"kbase-endpoint": "whatever"}, {"token": ""}], id="empty_token"),
    pytest.param([{"kbase-endpoint": None}, {"token": "whatever"}], id="no_endpt"),
    pytest.param([{"kbase-endpoint": ""}, {"token": "whatever"}], id="empty_endpt"),
]

# enable extra vcrpy logging for troubleshooting purposes
logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.DEBUG)



@pytest.mark.parametrize(
    "param", INVALID_DATA_FETCHER_PARAMS
)
def test_init(param: list[Any]) -> None:
    """Test that initialisation fails if params are not supplied."""
    with pytest.raises(
        ValueError,
        match="'config.kbase-endpoint' and 'context.token' are required by the DataFetcher",
    ):
        DataFetcher(*param)


@pytest.mark.parametrize(
    "param",
    paramify(
        [{
            "ref_list": [TEST_UPA["INVALID_A"], TEST_UPA["INVALID_B"]],
            "missing": f"{TEST_UPA["INVALID_A"]}, {TEST_UPA["INVALID_B"]}",
            "id": "all_missing",
        },
        {
            "ref_list": [TEST_UPA["INVALID_A"], TEST_UPA["AMPLICON"]],
            "missing": TEST_UPA["INVALID_A"],
            "id": "one_missing",
        },
    ])
)
def test_fetch_objects_by_ref_missing_items(
    param: dict[str, Any], data_fetcher: DataFetcher
) -> None:
    """Check that missing refs are reported correctly."""
    with vcr.use_cassette(
        f"test/data/cassettes/{param["id"]}.yaml",
    ), pytest.raises(
            ValueError,
            match=f"The following KBase objects could not be retrieved: {param['missing']}",
        ):
            data_fetcher.fetch_objects_by_ref(param["ref_list"])


@pytest.mark.parametrize(
    "param",
    paramify([
        {
             "ref_list": [TEST_UPA["AMPLICON"]], "sample_data_expected": [], "id": "no_sampleset"
        },
        {
             "ref_list": [TEST_UPA["SAMPLESET_A"]], "sample_data_expected": [TEST_UPA["SAMPLESET_A"]], "id": "single_sampleset"
        },
        {
             "ref_list": [TEST_UPA["AMPLICON"], TEST_UPA["SAMPLESET_A"], TEST_UPA["SAMPLESET_B"]],
                "sample_data_expected": [TEST_UPA["SAMPLESET_A"], TEST_UPA["SAMPLESET_B"]], "id": "multi_sampleset"
        }
    ])
)
def test_fetch_objects_by_ref_with_samples(
    param: dict[str, Any], data_fetcher: DataFetcher
) -> None:
    """Ensure that samples are fetched from the sampleset."""
    with vcr.use_cassette(
        f"test/data/cassettes/{param["id"]}.yaml",
    ):
        output = data_fetcher.fetch_objects_by_ref(param["ref_list"])

    for ref in param["ref_list"]:
        assert ref in output
        assert INFO in output[ref]
        assert DATA in output[ref]
        if ref in param["sample_data_expected"]:
            assert output[ref][INFO]["type"] == "KBaseSets.SampleSet-2.0"
            assert str(len(output[ref][DATA]["sample_data"])) == output[ref][INFO]["meta"]["num_samples"]
            assert "sample_data" in output[ref][DATA]
            assert {item["id"] for item in output[ref][DATA]["samples"]} == {
                item["id"] for item in output[ref][DATA]["sample_data"]
            }
        else:
            assert "sample_data" not in output[ref][DATA]
