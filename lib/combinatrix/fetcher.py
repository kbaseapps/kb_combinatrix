"""Fetch data from various locations."""

import json
import uuid
from typing import Any

import requests
from combinatrix.constants import DATA
from combinatrix.util import get_data_type, get_upa
from installed_clients.WorkspaceClient import Workspace


class DataFetcher:
    """Class for fetching data from various places."""

    def __init__(
        self: "DataFetcher", config: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """Initialise an instance of the class."""
        err_msg = "'config.kbase-endpoint' and 'context.token' are required by the DataFetcher"

        if not config or not context:
            raise ValueError(err_msg)
        self.config = config
        kbase_endpoint = config.get("kbase-endpoint")
        self.token = context.get("token")
        if not kbase_endpoint or not self.token:
            raise ValueError(err_msg)

        self.workspace_url = f"{kbase_endpoint}/ws"
        self.sample_service_url = f"{kbase_endpoint}/sampleservice"

    def fetch_samples(
        self: "DataFetcher", sample_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Retrieve sample data from the sample service.

        :param self: class instance
        :type self: DataFetcher
        :param sample_list: list of dicts containing sample IDs and version
        :type sample_list: list[dict[str, Any]]
        :raises RuntimeError: if there are any issues with fetching from the Sample Service
        :return: list containing data from the Sample Service
        :rtype: list[dict[str, Any]]
        """
        headers = {"Authorization": self.token, "Content-Type": "application/json"}
        payload = {
            "method": "SampleService.get_samples",
            "id": str(uuid.uuid4()),
            "params": [
                {
                    "samples": [
                        {"id": sample["id"], "version": sample["version"]}
                        for sample in sample_list
                    ],
                }
            ],
            "version": "1.1",
        }

        resp = requests.post(
            url=self.sample_service_url, headers=headers, data=json.dumps(payload)
        )
        resp_json = resp.json()
        if resp_json.get("error"):
            err_msg = f"Error from SampleService - {resp_json['error']}"
            raise RuntimeError(err_msg)
        return resp_json["result"][0]

    def fetch_objects_by_ref(
        self: "DataFetcher", ref_list: list[str]
    ) -> dict[str, Any]:
        """Retrieve a list of objects.

        :param self: class instance
        :type self: DataFetcher
        :param ref_list: list of KBase UPAs to fetch
        :type ref_list: list[str]
        :raises ValueError: if any of the results are not found
        :return: _description_
        :rtype: dict[str, Any]
        """
        ws_client = Workspace(self.workspace_url, token=self.token)

        # fetch the data sources from the workspace
        # results are in the same order as the input
        results = ws_client.get_objects2(
            {
                "objects": [{"ref": ref} for ref in ref_list],
                "ignoreErrors": 1,
                "infostruct": 1,
                "skip_external_system_updates": 1,
            }
        )[DATA]

        # check for missing results
        if not all(results):
            not_found = [
                item[0] for item in zip(ref_list, results, strict=True) if not item[1]
            ]
            err_msg = f"The following KBase objects could not be retrieved: {', '.join(not_found)}"
            raise ValueError(err_msg)

        output = {}
        for item in results:
            # check for any samplesets that need to be populated
            if "SampleSet" in get_data_type(item):
                item[DATA]["sample_data"] = self.fetch_samples(item[DATA]["samples"])
            # store in a dict indexed by UPA
            output[get_upa(item)] = item  # {INFO: item[INFO], DATA: item[DATA]}

        return output
