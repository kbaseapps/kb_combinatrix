# -*- coding: utf-8 -*-
# BEGIN_HEADER
import logging
import os

from combinatrix.core import AppCore

# END_HEADER


class combinatrix:
    """
    Module Name:
    combinatrix

    Module Description:
    A KBase module: combinatrix
    """

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.4"
    GIT_URL = "https://github.com/kbaseapps/kb_combinatrix.git"
    GIT_COMMIT_HASH = "31769ebea3c7261c0dff37b9fdc33c20bd0dc44c"

    # BEGIN_CLASS_HEADER
    # END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        # BEGIN_CONSTRUCTOR
        logging.basicConfig(
            format="%(created)s %(levelname)s: %(message)s", level=logging.INFO
        )
        self.config = config
        # END_CONSTRUCTOR
        pass

    def run_combinatrix(self, ctx, params):
        """
        Run the Combinatrix to produce a report detailing all possible combinations of the inputs.
        :param params: instance of type "CombinatrixParams" (input params for
           the Combinatrix) -> structure: parameter "join_list" of list of
           type "JoinSpec" (dataset join information as specified in the UI)
           -> structure: parameter "t1_ref" of type "ws_ref" (a workspace
           object reference string (of the form wsid/objid/ver)), parameter
           "t2_ref" of type "ws_ref" (a workspace object reference string (of
           the form wsid/objid/ver)), parameter "t1_field" of String,
           parameter "t2_field" of String, parameter "workspace_id" of type
           "ws_id" (a workspace id)
        :returns: instance of type "ReportResults" (output from the
           KBaseReport app) -> structure: parameter "report_name" of String,
           parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        # BEGIN run_combinatrix
        print("Welcome to the combinatrix!")

        if not os.environ.get("SDK_CALLBACK_URL"):
            err_msg = "Combinatrix encountered the following errors:\nthe environment variable SDK_CALLBACK_URL must be set"
            raise RuntimeError(err_msg)

        if "jellybean" not in self.config:
            err_msg = "No jellybeans found"
            raise RuntimeError(err_msg)

        combinatrix = AppCore(self.config, ctx, os.environ["SDK_CALLBACK_URL"])
        output = combinatrix.run(params)
        # END run_combinatrix

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError(
                "Method run_combinatrix "
                + "return value output "
                + "is not type dict as required."
            )
        # return the results
        return [output]

    def status(self, ctx):
        # BEGIN_STATUS
        returnVal = {
            "state": "OK",
            "message": "It's fine. I'm fine. Everything is fine.",
            "version": self.VERSION,
            "git_url": self.GIT_URL,
            "git_commit_hash": self.GIT_COMMIT_HASH,
        }
        # END_STATUS
        return [returnVal]
