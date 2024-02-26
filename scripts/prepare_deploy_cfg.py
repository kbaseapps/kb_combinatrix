"""Create the deployment configuration for the module."""

import os
import os.path
import sys
from configparser import ConfigParser
from io import StringIO

from jinja2 import Template

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: <program> <deploy_cfg_template_file> <file_with_properties>")
        print(
            "Properties from <file_with_properties> will be applied to <deploy_cfg_template_file>"
        )
        print(
            "template which will be overwritten with .orig copy saved in the same folder first."
        )
        sys.exit(1)
    with open(sys.argv[1]) as file:
        text = file.read()
    t = Template(text)
    config = ConfigParser()
    if os.path.isfile(sys.argv[2]):
        config.read(sys.argv[2])
    elif "KBASE_ENDPOINT" in os.environ:
        kbase_endpoint = os.environ.get("KBASE_ENDPOINT")
        props = (
            "[global]\n"
            + f"kbase_endpoint = {kbase_endpoint}\n"
            + f"workspace_url = {kbase_endpoint}/ws\n"
            + f"sample_service_url = {kbase_endpoint}/sampleservice"
        )
        if "AUTH_SERVICE_URL" in os.environ:
            props += f"auth_service_url = {os.environ.get('AUTH_SERVICE_URL')}\n"
        props += (
            "auth_service_url_allow_insecure = "
            + os.environ.get("AUTH_SERVICE_URL_ALLOW_INSECURE", "false")
            + "\n"
        )
        for key in os.environ:
            if key.startswith("KBASE_SECURE_CONFIG_PARAM_"):
                param_name = key[len("KBASE_SECURE_CONFIG_PARAM_") :]
                props += f"{param_name} = {os.environ.get(key)}\n"
        config.readfp(StringIO(props))
    else:
        raise ValueError(
            "Neither " + sys.argv[2] + " file nor KBASE_ENDPOINT env-variable found"
        )
    props = dict(config.items("global"))
    output = t.render(props)
    with open(sys.argv[1] + ".orig", "w") as f:
        f.write(text)
    with open(sys.argv[1], "w") as f:
        f.write(output)
