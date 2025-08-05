"""
This is the base module that the Cloudsploit modules inherit from. It contains common functions to install the Cloudsploit tool and
check subprocess return codes.
"""
import json
import logging
import os
import re
import shutil
import subprocess
import time

from base_module import ModuleException, StatusCode


class CloudsploitSetUpMixin:
    """
    The mixin class that sets up the Cloudspoilt additional software and create all the required stuff
    """

    _subprocess_error_message = "An error occurred when running Cloudsploit"
    compliance_attrs = (
        "hipaa",
        "pci",
        "cis",
        "cis1",
        "cis2",
    )

    def _check_subprocess(self, process):
        if not process.returncode == 0:
            # TODO hacky solution to get around the warning being raised as an exception
            # TODO Need to understand why this got raised suddenly
            if b"We are formalizing our plans to enter AWS SDK for JavaScript" not in process.stderr:
                print(
                    f"<error>Error occured: returncode: {process.returncode} stdout: {process.stdout} stderr: {process.stderr}</error>",
                )
                raise ModuleException(
                    f"{self._subprocess_error_message}, exc:{process.stderr}",
                    StatusCode.SUBPROCESS_ERROR,
                    subprocess_return_code=process.returncode,
                    subprocess_standard_output=process.stdout,
                    subprocess_standard_error=process.stderr,
                )

    def construct_cloudsploit_query(
        self,
        output_file,
        module_name,
    ):
        """Helper Method to construct CloudSploit Queries"""

        # Construct common query string
        query = f"./index.js --json={output_file} "

        if module_name == "cloudsploit_aws":
            query += f"--console=none"

        elif module_name == "cloudsploit_gcp":
            query += "--config=/home/ayush/accuknox/accuknox-pocs/configs/cloudsploit/config.js --console=none"

        elif module_name == "cloudsploit_azure":
            query += "--config=/home/ayush/accuknox/accuknox-pocs/configs/cloudsploit/config.js --console=none"
        
        elif module_name == "cloudsploit_oracle":
            query += "--config=/home/ayush/accuknox/accuknox-pocs/configs/cloudsploit/config.js --console=none"

        if self.compliance is not None and self.compliance != "":
            attrs = " ".join(f"--compliance={each}" for each in self.compliance_attrs)
            query += f" {attrs}"

        print(f"<debug>Successfully  constructed the CloudSploit query {query}</debug>")
        return query

    def execute_cloud_sploit_query(
        self,
        output_file,
        filename,
    ):
        """Executes the constructed CloudSploit query."""

        print("Executing constructed CloudSploit query")
        process = subprocess.run(
            self.construct_cloudsploit_query(
                output_file,
                self._module_name,
            ),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="cs-accuknox",
        )

        self._check_subprocess(process)

        if os.path.getsize(f"cs-accuknox/{output_file}") == 0:
            print(f"<error>The size of the cs-accuknox/{output_file} is 0!</error>")
            raise ModuleException(
                f"{self._subprocess_error_message}, exc:{process.stderr}",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )

        if self.check_inbuilt_cloudsploit_error(file_location=f"cs-accuknox/{output_file}"):
            print(f"<error>The security token included in the request is invalid!</error>")
            raise ModuleException(
                f"{self._subprocess_error_message}, exc:{process.stderr}",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )

        shutil.move(f"cs-accuknox/{output_file}", filename)
        print(f"<success>Success! {filename} written to /tmp folder</success>")
        return {
            "response": f"Success! {filename} written to /tmp folder",
            "status_code": StatusCode.SUCCESS.value,
        }

    @staticmethod
    def check_inbuilt_cloudsploit_error(file_location):
        with open(file_location, "r") as file:
            cloudsploit_data = json.load(file)
            for data in cloudsploit_data:
                resource = data.get("resource", "")
                status = data.get("status", "")
                message = data.get("message", "")

                error_message = "The security token included in the request is invalid"
                if resource == "N/A" and status == "UNKNOWN" and re.search(error_message, message):
                    return True
        return False
