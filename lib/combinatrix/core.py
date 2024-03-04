"""Fetches, combines, masticates, and spits out the appropriate data structure."""

import os
import time
from typing import Any

from combinatrix.combinatrix import combine_data
from combinatrix.constants import (
    DATA,
    DL,
    FN,
    INFO,
    JOIN_LIST,
    KEYS,
    REF,
    REFS,
)
from combinatrix.converter import (
    convert_data,
    convert_list_of_dicts_to_list_of_lists,
    save_as_csv,
)
from combinatrix.fetcher import DataFetcher
from combinatrix.param_checker import check_params
from combinatrix.util import get_data_type, log_this, remove_special_chars
from installed_clients.KBaseReportClient import KBaseReport


class AppCore:
    """Class for fetching and combining datasets."""

    def __init__(
        self: "AppCore",
        config: dict[str, Any],
        context: dict[str, Any],
        callback_url: str,
    ) -> None:
        """Instantiate a new AppCore class instance.

        :param self: class instance
        :type self: AppCore
        :param config: config dictionary
        :type config: dict[str, Any]
        :param context: KBase context
        :type context: dict[str, Any]
        :param callback_url: URL for the KBase callback server
        :type callback_url: str
        """
        self.config = config
        self.context = context
        self.callback_url = callback_url

    def run(
        self: "AppCore",
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Main execution routine for the core combinatrix functionality.

        :param self: class instance
        :type self: AppCore
        :param params: parameters for combinatrixing
        :type params: dict[str, Any]
        :return: KBase report name and reference
        :rtype: dict[str, Any]
        """
        fetcher = DataFetcher(self.config, self.context)
        reporter = KBaseReport(self.callback_url)

        timing = {}
        # Start timer for parameter validation
        start_time = time.time()
        join_params = check_params(params)
        # End timer and print duration
        timing["check_params"] = f"{time.time() - start_time:.2f} seconds"

        # Start timer for data fetching
        start_time = time.time()
        fetched_data = fetcher.fetch_objects_by_ref(sorted(join_params[REFS]))
        # End timer and print duration
        timing["fetch_objs"] = f"{time.time() - start_time:.2f} seconds"

        # Start timer for data conversion
        start_time = time.time()
        standardised_data = convert_data(fetched_data)
        # End timer and print duration
        timing["convert"] = f"{time.time() - start_time:.2f} seconds"

        # Start timer for data combining
        start_time = time.time()
        resultset = combine_data(join_params, standardised_data)
        # End timer and print duration
        timing["combine"] = f"{time.time() - start_time:.2f} seconds"

        for ref in standardised_data:
            csv_file_name = f"{remove_special_chars(ref)}.csv"
            outfile = os.path.join(self.config["scratch"], csv_file_name)
            standardised_data[ref]["csv"] = save_as_csv(standardised_data[ref], outfile)

        # export data for displaying in datatables
        template_data = {
            "join_params": join_params[JOIN_LIST],
            "object_data": {
                ref: {
                    "info": standardised_data[ref][INFO],
                    "file": standardised_data[ref]["csv"],
                    # DATA: convert_list_of_dicts_to_list_of_lists(
                    #     standardised_data[ref][DL],
                    #     standardised_data[ref][FN],
                    # ),
                    "display": {
                        "type": get_data_type(standardised_data[ref]),
                        KEYS: (
                            {
                                k: list(standardised_data[ref][KEYS][k])
                                for k in standardised_data[ref][KEYS]
                            }
                            if KEYS in standardised_data[ref]
                            else None
                        ),
                    },
                    # set
                    "combined": list(resultset[ref]),
                }
                for ref in standardised_data
            },
        }

        if "no_report" in params and params["no_report"]:
            return {
                # dump the data structure as JSON
                "template_data": log_this(self.config, "template_data", template_data),
                **{ref: standardised_data[ref]["csv"] for ref in standardised_data},
            }

        report_info: dict[str, Any] = reporter.create_extended_report(
            {
                "report_object_name": "Combinatrix output",
                "workspace_id": params["workspace_id"],
                "template": {
                    "template_file": "path/to/template",
                    "template_data_json": template_data,
                },
                # html_links: (optional list of dicts) HTML files to attach and display in the report (see the additional information below)
                # direct_html_link_index: (optional integer) index in html_links that you want to use as the main/default report view
                # message: (optional string) basic result message to show in the report
                # report_object_name: (optional string) a name to give the workspace object that stores the report.
                # workspace_id: (optional integer) id of your workspace. Preferred over workspace_name as it's immutable. Required if workspace_name is absent.
                # workspace_name: (optional string) string name of your workspace. Requried if workspace_id is absent.
                # direct_html: (optional string) raw HTML to show in the report
                # objects_created: (optional list of WorkspaceObject) data objects that were created as a result of running your app, such as assemblies or genomes
                # warnings: (optional list of strings) any warnings messages generated from running the app
                # file_links: (optional list of dicts) files to attach to the report (see the valid key/vals below)
                # html_window_height: (optional float) fixed pixel height of your report view
                # summary_window_height: (optional float) fixed pixel height of the summary within your report
            }
        )  # type: ignore
        return {
            "report_name": report_info["name"],
            "report_ref": report_info[REF],
        }
