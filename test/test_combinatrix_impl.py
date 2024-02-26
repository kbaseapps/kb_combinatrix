"""Tests for the Combinatrix Impl."""

import os
from collections.abc import Callable, Generator
from test.conftest import body_match_vcr as vcr
from typing import Any

import pytest
from combinatrix.CombinatrixImpl import combinatrix
from combinatrix.constants import (
    FIELD,
    JOIN_LIST,
    KEYS,
    REF,
    T1,
    T2,
)
from installed_clients.KBaseReportClient import KBaseReport


# Fixture to manage an environment variable
@pytest.fixture()
def _manage_env_var(
    monkeypatch: Callable, request: pytest.FixtureRequest
) -> Generator[Any, Any, Any]:
    """Test fixture to allow an environment variable to be temporarily removed.

    :param monkeypatch: pytest monkeypatch
    :type monkeypatch: Callable
    :param request: test request object
    :type request: FixtureRequest
    """
    env_var_requests = request.param
    original = {}
    for env_var in env_var_requests:
        # Store the original value of the environment variable if it exists
        original[env_var] = os.environ.get(env_var)

        if env_var_requests[env_var] is None:
            # Delete the environment variable for the test
            monkeypatch.delenv(
                env_var, raising=False
            )  # Set `raising=False` to ignore if the env var does not exist
        else:
            os.environ[env_var] = env_var_requests[env_var]

    # Yield to run the test
    yield

    for env_var in env_var_requests:
        # Define the teardown action: Restore the original environment variable
        if original[env_var] is not None:
            os.environ[env_var] = original[env_var]
        else:
            monkeypatch.delenv(env_var, raising=False)


@pytest.mark.usefixtures("_manage_env_var")
@pytest.mark.parametrize("_manage_env_var", [{"SDK_CALLBACK_URL": None}], indirect=True)
def test_run_combinatrix_fail(context: dict[str, Any], config: dict[str, Any]) -> None:
    """The combinatrix should fail if there is no callback URL env var."""
    combi = combinatrix(config)
    # try running the combinatrix without the SDK_CALLBACK_URL env var present
    with pytest.raises(
        RuntimeError,
        match="Combinatrix encountered the following errors:\nthe environment variable SDK_CALLBACK_URL must be set",
    ):
        combi.run_combinatrix(context, {})


# These are on appdev and are cut-down versions of a representative dataset.
SOURCE = "72724/21/1"
SAMPLE = "72724/19/1"
MATRIX = "72724/23/1"


@pytest.mark.usefixtures("_manage_env_var")
@pytest.mark.parametrize("param", [True, False])
@pytest.mark.parametrize(
    "_manage_env_var", [{"SDK_CALLBACK_URL": "https://some.valid.url"}], indirect=True
)
def test_run_combinatrix(
    param: bool,
    config: dict[str, Any],
    context: dict[str, Any],
    monkeypatch: Callable,
) -> None:
    """Test a run through of the app_core functionality."""
    expected = {"name": "some name", REF: "some ref"}

    def mock_create_ext_report(*args: list[Any]) -> dict[str, str]:
        """Mock of the create_extended_report method.

        :param args: list of arguments. The first is the KBare Report instance.
        :type args: list[Any]
        :return: mock report output
        :rtype: dict[str, str]
        """
        (report, report_args) = args
        assert isinstance(report, KBaseReport)
        assert isinstance(report_args, dict)
        assert report_args.get("report_object_name") == "Combinatrix output"
        assert "template" in report_args
        assert "template_data_json" in report_args.get("template", {})

        object_data = (
            report_args.get("template", {})
            .get("template_data_json", {})
            .get("object_data")
        )
        assert set(object_data.keys()) == {SOURCE, SAMPLE, MATRIX}

        source_ids = {"16O.16C-unique-id", "16O.16W-unique-id", "18O.18C-unique-id"}
        sample_ids = {
            "16O.16C.5-unique-id",
            "16O.16C.6-unique-id",
            "16O.16C.8-unique-id",
            "16O.16C.9-unique-id",
            "16O.16W.6-unique-id",
            "16O.16W.7-unique-id",
            "16O.16W.8-unique-id",
            "16O.16W.9-unique-id",
            "18O.18C.7-unique-id",
            "18O.18C.8-unique-id",
            "18O.18C.9-unique-id",
        }

        assert set(object_data[SOURCE]["combined"]) == source_ids
        assert set(object_data[SAMPLE]["combined"]) == sample_ids
        for matrix_id in object_data[MATRIX]["combined"]:
            assert f"{matrix_id[:9]}-unique-id" in sample_ids

        assert object_data[MATRIX]["display"][KEYS] is None
        return expected

    # monkeypatch the `create_extended_report` method so that it doesn't get called
    monkeypatch.setattr(KBaseReport, "create_extended_report", mock_create_ext_report)
    combi = combinatrix(config)

    with vcr.use_cassette(
        "test/data/cassettes/test_run.yaml",
    ):
        output = combi.run_combinatrix(
            context,
            {
                JOIN_LIST: [
                    {
                        f"{T2}_{REF}": SOURCE,
                        f"{T2}_{FIELD}": "name",
                        f"{T1}_{REF}": SAMPLE,
                        f"{T1}_{FIELD}": "source_mat_id",
                    },
                    {
                        f"{T2}_{REF}": SAMPLE,
                        f"{T2}_{FIELD}": "name",
                        f"{T1}_{REF}": MATRIX,
                        f"{T1}_{FIELD}": "column_id",
                    },
                ],
                "workspace_id": 12345,
                "no_report": param,
            },
        )

        if not param:
            assert output == [{"report_name": "some name", "report_ref": "some ref"}]
        else:
            scratch_dir = (
                config["scratch"]
                if os.path.isabs(config["scratch"])
                else os.path.abspath(config["scratch"])
            )
            assert output == [
                {
                    "72724/19/1": f"{scratch_dir}/72724_19_1.csv",
                    "72724/21/1": f"{scratch_dir}/72724_21_1.csv",
                    "72724/23/1": f"{scratch_dir}/72724_23_1.csv",
                    "template_data": f"{scratch_dir}/template_data.json",
                }
            ]


def test_status(config: dict[str, Any]) -> None:
    """Test the status command."""
    combi = combinatrix(config)

    assert combi.status({}) == [
        {
            "state": "OK",
            "message": "It's fine. I'm fine. Everything is fine.",
            "version": combi.VERSION,
            "git_url": combi.GIT_URL,
            "git_commit_hash": combi.GIT_COMMIT_HASH,
        }
    ]
