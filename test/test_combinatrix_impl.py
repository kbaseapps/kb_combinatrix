"""Tests for the Combinatrix Impl."""

import os
import re
from collections.abc import Callable, Generator
from pathlib import PosixPath
from test.conftest import body_match_vcr as vcr
from typing import Any

import pytest
from combinatrix import renderer
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
WS_ID = 12345


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
    tmp_path: PosixPath,
) -> None:
    """Test a run through of the app_core functionality."""
    expected = {"name": "some name", REF: "some ref"}

    def mock_create_ext_report(*args: list[Any]) -> dict[str, str]:
        """Mock of the create_extended_report method.

        :param args: list of arguments. The first is the KBase Report instance.
        :type args: list[Any]
        :return: mock report output
        :rtype: dict[str, str]
        """
        (report, report_args) = args
        assert isinstance(report, KBaseReport)
        assert isinstance(report_args, dict)
        report_name = report_args.get("report_object_name")
        assert report_name is not None
        report_name_regex = r"combinatrix_output_\d{4}-\d{2}-\d{2}_\d{6}_UTC"
        assert re.match(report_name_regex, report_name) is not None

        assert report_args.get("workspace_id") == WS_ID

        assert "html_links" in report_args
        assert isinstance(report_args.get("html_links"), list)
        assert len(report_args.get("html_links")) == 1  # type: ignore
        html_links = report_args["html_links"][0]  # type: ignore
        assert html_links.get("name") == "report.html"
        assert html_links.get("path").endswith("output")
        assert report_args.get("direct_html_link_index") == 0

        return expected

    def render_template_wrapper(file_path: str, template_data: dict[str, Any]) -> str:
        """Perform checks on input before executing the template render function.

        :param file_path: template output file path
        :type file_path: str
        :param template_data: data for the template
        :type template_data: dict[str, Any]
        :return: template output file path
        :rtype: str
        """
        assert file_path.endswith("report.html")
        object_data = template_data.get("object_data")
        assert object_data is not None
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
        return renderer.render_template(file_path, template_data)

    # monkeypatch the `create_extended_report` method so that it doesn't get called
    monkeypatch.setattr(KBaseReport, "create_extended_report", mock_create_ext_report)

    # monkeypatch the template rendering function to check the output is as expected
    monkeypatch.setattr(renderer, "render_template", render_template_wrapper)

    config_with_tmp_path = {**config, "scratch": tmp_path}

    combi = combinatrix(config_with_tmp_path)

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
                "workspace_id": WS_ID,
                "no_report": param,
            },
        )

        if not param:
            assert output == [{"report_name": "some name", "report_ref": "some ref"}]
        else:
            assert output == [
                {
                    "directory": f"{tmp_path}/output",
                    "72724/19/1": "72724_19_1.csv",
                    "72724/21/1": "72724_21_1.csv",
                    "72724/23/1": "72724_23_1.csv",
                    "template_data": "template_data.json",
                }
            ]
            # ensure the paths exist
            for f in [
                "72724_19_1.csv",
                "72724_21_1.csv",
                "72724_23_1.csv",
                "template_data.json",
            ]:
                file_path = os.path.join(tmp_path, "output", f)
                assert os.path.exists(file_path)
                assert os.path.isfile(file_path)


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
