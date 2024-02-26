"""Fetch workspace data from the commandline."""

import argparse
import os
import sys
from argparse import Namespace
from configparser import ConfigParser
from os import environ

from combinatrix.constants import DATA
from combinatrix.converter import convert_matrix, convert_samples, save_as_csv
from combinatrix.fetcher import DataFetcher
from combinatrix.util import log_this, remove_special_chars

DEPLOY = "KB_DEPLOYMENT_CONFIG"
SERVICE = "KB_SERVICE_NAME"
SERVICE_NAME = "combinatrix"
AUTH = "auth-service-url"


def get_config_file() -> str:
    """Get the path to the config file.

    :return: path to the config file
    :rtype: str
    """
    return environ.get(DEPLOY, "./test/deploy.cfg")


def get_service_name() -> str:
    """Get the service name.

    :return: service name
    :rtype: str
    """
    return environ.get(SERVICE, SERVICE_NAME)


def get_config() -> dict[str, str]:
    """Retrieve the config from the config file.

    :return: parsed config as a dictionary
    :rtype: dict[str, str]
    """
    if not get_config_file():
        err_msg = "Config file not specified"
        raise RuntimeError(err_msg)
    retconfig = {}
    config = ConfigParser()
    config.read(get_config_file())
    for nameval in config.items(get_service_name() or SERVICE_NAME):
        retconfig[nameval[0]] = nameval[1]
    return retconfig


def parse_args(args: list[str]) -> Namespace:
    """Parse input arguments.

    :param args: input argument list
    :type args: list[str]
    :raises RuntimeError: if one or more of the parameters are missing
    :return: parsed arguments
    :rtype: dict[str, str]
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        "upa",
        metavar="UPA",
        nargs="+",
        help="UPA(s) to retrieve from the KBase workspace",
    )
    p.add_argument("-t", "--token", dest="token", required=True, help="User auth token")
    p.add_argument(
        "-e",
        "--env",
        dest="env",
        help="KBase environment",
        choices=["prod", "ci", "appdev"],
        default="prod",
    )
    p.add_argument(
        "-f",
        "--format",
        dest="format",
        help="output format",
        choices=["json", "csv"],
        default="json",
    )
    p.add_argument(
        "-o",
        "--outfile",
        dest="outfile",
        help="output file name",
        default="ws_results",
    )
    return p.parse_args(args)


def main(args: list[str]) -> None:
    """Run!

    :param args: input args as a list
    :type args: list[str]
    """
    parsed_args = parse_args(args)
    endpt = "kbase.us/services/"
    env = parsed_args.env + "."
    if env == "prod.":
        env = ""
    endpt = f"https://{env}{endpt}"

    config = get_config()

    scratch_dir = (
        config["scratch"]
        if os.path.isabs(config["scratch"])
        else os.path.abspath(config["scratch"])
    )

    config["auth-service-url"] = endpt + "auth/api/legacy/KBase/Sessions/Login"
    data_fetcher = DataFetcher(config, {"token": parsed_args.token})
    print(f"Fetching the following UPAs from {parsed_args.env}:")
    print(", ".join(parsed_args.upa))
    output = data_fetcher.fetch_objects_by_ref(parsed_args.upa)
    if parsed_args.format == "csv":

        for ref in output:
            data = output[ref]
            parsed_data = {}
            if data.get(DATA, {}).get("sample_data"):
                parsed_data = convert_samples(data)
            elif data.get(DATA, {}).get(DATA):
                parsed_data = convert_matrix(data)
            else:
                err_msg = "Input data structure not recognised"
                raise ValueError(err_msg)

            save_as_csv(parsed_data, scratch_dir + f"/{remove_special_chars(ref)}.csv")
        sys.exit(0)

    log_this({"scratch": scratch_dir}, parsed_args.outfile, output)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
