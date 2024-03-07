"""Fetches, combines, masticates, and spits out the appropriate data structure."""
import os
import time
from datetime import datetime
from typing import Any

from combinatrix.combination_harvester import combine_data
from combinatrix.constants import (
    INFO,
    JOIN_LIST,
    KEYS,
    REF,
    REFS,
)
from combinatrix.converter import (
    convert_data,
    save_as_csv,
)
from combinatrix.fetcher import DataFetcher
from combinatrix.param_checker import check_params
from combinatrix.renderer import render_template
from combinatrix.util import get_data_type, log_this, remove_special_chars
from installed_clients.KBaseReportClient import KBaseReport

J2_SUFFIX = ".j2"
REPORT_FILE_NAME = "report.html"

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
        print(f"Check params: {timing["check_params"]}")

        # Start timer for data fetching
        start_time = time.time()
        fetched_data = fetcher.fetch_objects_by_ref(sorted(join_params[REFS]))
        # End timer and print duration
        timing["fetch_objs"] = f"{time.time() - start_time:.2f} seconds"
        print(f"fetch objects: {timing["fetch_objs"]}")

        # Start timer for data conversion
        start_time = time.time()
        standardised_data = convert_data(fetched_data)
        # End timer and print duration
        timing["convert"] = f"{time.time() - start_time:.2f} seconds"
        print(f"convert data: {timing["convert"]}")

        # Start timer for data combining
        start_time = time.time()
        resultset = combine_data(join_params, standardised_data)
        # End timer and print duration
        timing["combine"] = f"{time.time() - start_time:.2f} seconds"
        print(f"combine data: {timing["combine"]}")

        output_dir = os.path.join(self.config["scratch"], "output")
        # create the dir if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        for ref in standardised_data:
            csv_file_name = f"{remove_special_chars(ref)}.csv"
            outfile = os.path.join(output_dir, csv_file_name)
            save_as_csv(standardised_data[ref], outfile)
            standardised_data[ref]["csv_file"] = csv_file_name

        # export data for displaying in datatables
        template_data = {
            "join_params": join_params[JOIN_LIST],
            "object_data": {
                ref: {
                    "info": standardised_data[ref][INFO],
                    "file": standardised_data[ref]["csv_file"],
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

        # for local / development use only
        if "no_report" in params and params["no_report"]:
            return {
                # dump the data structure as JSON
                "template_data": log_this(self.config, "template_data", template_data),
                **{ref: standardised_data[ref]["csv_file"] for ref in standardised_data},
            }

        template_output_path = os.path.join(output_dir, REPORT_FILE_NAME)
        render_template(template_output_path, template_data)

        # Get current date and time
        now = datetime.now(tz=None)

        # Format the date and time
        date_time_str = now.strftime("%Y%m%d_%H%M%S")
        report_info: dict[str, Any] = reporter.create_extended_report(
            {
                "report_object_name": f"combinatrix_output_{date_time_str}",
                "workspace_id": params["workspace_id"],
                "html_links": [{
                    "path": output_dir,
                    "name": REPORT_FILE_NAME,
                }],
                "direct_html_link_index": 0
            }
        )  # type: ignore

        return {
            "report_name": report_info["name"],
            "report_ref": report_info[REF],
        }
