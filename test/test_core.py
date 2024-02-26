"""Tests for the combinatrix core."""

from test.test_data_fetcher import INVALID_DATA_FETCHER_PARAMS
from typing import Any

import pytest
from combinatrix.core import AppCore


@pytest.mark.parametrize("param", INVALID_DATA_FETCHER_PARAMS)
def test_run_fail_cannot_init_data_fetcher(param: list[Any]) -> None:
    """Test that initialisation fails if params are not supplied."""
    core = AppCore(*param, "None")
    with pytest.raises(
        ValueError,
        match="'config.kbase-endpoint' and 'context.token' are required by the DataFetcher",
    ):
        core.run({})


@pytest.mark.parametrize(
    "param",
    [
        pytest.param({"input": None, "err": "A url is required"}, id="None"),
        pytest.param({"input": ""}, id="empty"),
        pytest.param({"input": "pop"}, id="string"),
        pytest.param({"input": "not.an.url"}, id="url format invalid"),
        pytest.param({"input": "123.456.789.10"}, id="IP address, invalid"),
    ],
)
def test_run_fail_cannot_init_report_client(
    config: dict[str, Any], context: dict[str, Any], param: dict[str, Any]
) -> None:
    """Test that initialisations fails if the callback_url is not set."""
    core = AppCore(config, context, param["input"])  # type: ignore
    err_msg = param.get("err", f"{param["input"]} isn't a valid http url")
    with pytest.raises(ValueError, match=err_msg):
        core.run({})
