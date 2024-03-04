"""Create the deployment configuration for the module."""

import os
import sys
from configparser import ConfigParser

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

    print("kicking off the prepare_deploy_config script!")

    with open(sys.argv[1]) as file:
        text = file.read()
    t = Template(text)
    config = ConfigParser()
    props = {}
    if os.path.isfile(sys.argv[2]):
        config.read(sys.argv[2])
        props = dict(config.items("global"))
    elif "KBASE_ENDPOINT" in os.environ:
        kbase_endpoint = os.environ.get("KBASE_ENDPOINT")
        props = {
            "kbase_endpoint": f"{kbase_endpoint}",
            "workspace_url": f"{kbase_endpoint}/ws",
            "sample_service_url": f"{kbase_endpoint}/sample_service",
            "auth_service_url_allow_insecure": f"{os.environ.get('AUTH_SERVICE_URL_ALLOW_INSECURE', 'false')}",
        }

        if "AUTH_SERVICE_URL" in os.environ:
            props["auth_service_url"] = f"{os.environ.get('AUTH_SERVICE_URL')}"

        for key in os.environ:
            if key.startswith("KBASE_SECURE_CONFIG_PARAM_"):
                param_name = key[len("KBASE_SECURE_CONFIG_PARAM_") :]
                props[f"{param_name}"] = f"{os.environ.get(key)}"
    else:
        err_msg = (
            "Neither " + sys.argv[2] + " file nor KBASE_ENDPOINT env-variable found"
        )
        raise ValueError(err_msg)

    output = t.render(props)
    with open(sys.argv[1] + ".orig", "w") as f:
        f.write(text)
    with open(sys.argv[1], "w") as f:
        f.write(output)
