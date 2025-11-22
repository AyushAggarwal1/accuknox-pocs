"""
    This is the base module class which all other modules inherit from. It contains common functionality for all modules like
    installing dependencies, initializing and returning error messages back to the master.
"""
from typing import Dict

import itertools
import json
import os
import re
import time
import traceback
from datetime import datetime
from enum import Enum

# boto3 import moved to methods that actually use it (lazy import)


class StatusCode(Enum):
    EMPTY_ATTRIBUTE = 1001
    INSTALL_DEPENDENCY = 1003
    CLONE_ERROR = 1004
    UNEXPECTED_ERROR = 1005
    SUBPROCESS_ERROR = 1006
    DOCKER_ERROR = 1007
    AWS_ERROR = 1008
    FILE_ERROR = 1009
    PACKAGE_NOT_FOUND = 1010
    THIRD_PARTY_API_ERROR = 1011
    SEND_S3_ERROR = 1012
    FIELD_VALUE_ERROR = 1013
    OS_ERROR = 1014
    CODE_ERROR = 1015
    MODULE_PROCESSING_ERROR = 1016
    KEY_ERROR = 1017
    JSON_ENCODE_ERROR = 1018
    SUBPROCESS_OUTPUT_DECODE_ERROR = 1019
    SUCCESS = 2000
    NO_DATA = 2001


class ErrorMessage(Enum):
    CLIENT_CREATION_ERROR = "Could not instantiate the boto3 client to upload to S3."
    UPLOAD_ERROR = "Error uploading to S3."
    METADATA_RETRIEVAL_ERROR = "Error during filesize verification. Could not retrive S3 metadata for verification."
    METADATA_FORMAT_ERROR = (
        "Error during filesize verification. The S3 metadata for verification was in an unexpected format."
    )
    FILE_SIZE_CONVERT_TO_INT_ERROR = (
        "Error during filesize verification. The file size could not be converted to an integer."
    )
    FILE_SIZE_MISMATCH = "Error during filesize verification. The local file size did not match the remote file size."
    BAD_ZIP_FILE = "The file provided is not a zip file."


class ModuleException(Exception):
    """
    Custom module exception that is used in every module
    """

    def __init__(
        self,
        msg,
        status_code: StatusCode,
        additional_info: str = None,
        subprocess_return_code: int = None,
        subprocess_standard_output: bytes = None,
        subprocess_standard_error: bytes = None,
    ):
        self.status_code = status_code
        self.additional_info = additional_info
        self.subprocess_return_code = subprocess_return_code
        self.subprocess_standard_output = subprocess_standard_output
        self.subprocess_standard_error = subprocess_standard_error
        super().__init__(msg)


class BaseModule:
    # provide module name
    _module_name = ""

    # fields that should be required in the module
    _fields = []

    _access_exception_list = [
        "InvalidAccessException",  # cloudsploit,securityhub (AWS)
        "accessNotConfigured",  # GCP
        "AccessDeniedException",  # macie
        "Authorization_RequestDenied",  # steampipe azure
        "invalid_client",
        "InvalidSignatureException",
        "InvalidAuthenticationToken",
        "GetCallerIdentity",
        "UnknownError",
    ]

    def __init__(
        self,
        kwargs: Dict,
    ):
        """
        This section of code intializes, and loops through all of the keyword argument or pillar parameters passed into the module and sets them as attributes
        of the class.
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

    def main(self) -> Dict:
        current_time = time.time()
        print(f"Starting the main function at {current_time}")

        try:
            self._check_fields()  # Verifies that required fields for running the module are filled and raises an error if a field is empty

            response = self.run()  # Runs code in module subclass

            return response

        except ModuleException as e:
            return self._generate_error_response(
                str(e),
                e.status_code,
                e.additional_info,
                e.subprocess_return_code,
                e.subprocess_standard_output,
                e.subprocess_standard_error,
            )

        except ModuleNotFoundError:
            return self._generate_error_response(
                "Couldn't properly initialize or import a package",
                StatusCode.PACKAGE_NOT_FOUND,
            )

        except Exception as ex:
            return self._generate_error_response(
                f"Unexpected error {ex} {traceback.format_exc()}",
                StatusCode.UNEXPECTED_ERROR,
            )

        finally:
            print(f"It took {time.time() - current_time} seconds to execute the playbook {self.__class__.__name__}")

    def _check_fields(self):
        """
        Checking all required fields
        """
        print("Checking all required fields were passed")
        for field in self._fields:
            if not getattr(self, field):
                raise ModuleException(
                    f"Provide {field} value",
                    StatusCode.EMPTY_ATTRIBUTE,
                )

        print("All fields were checked")

    def construct_filename(self, parser_prefix, file_extension, keep_integral=True):
        if keep_integral:
            time_suffix = str(time.time()).split(".")[0]
        else:
            time_suffix = str(time.time())
        filename = os.path.join("/tmp", f"{self.label}-{parser_prefix}-{time_suffix}.{file_extension}")
        return filename

    def _write_to_file(
        self,
        filename,
        data,
        decode: bool = False,
        jsonify: bool = False,
        binary: bool = False,
    ):
        """
        This is a common function that is used to write data to files and perform encoding and decoding.
        Parameters:
        filename: The absolute path of the file to write to.
        data: The data to write to the file
        decode: a boolean parameter that determines whether or not to decode data into UTF-8 format. This is used if the data comes from subprocess
        output where it is in bytes format.
        jsonify: a boolean parameter that determines whether or not the data should be converted to JSON with the json.dumps method.
        binary: Writes to file in binary mode instead of regular mode.

        Note that if both decode and jsonify are true it will always perform the decode operation first because it can't convert a bytes data type to JSON.
        """
        if binary:
            write_mode = "wb"
        else:
            write_mode = "w"
        if decode:
            try:
                data = data.decode("utf-8")
            except Exception:
                raise ModuleException(
                    "<error>Results data could not decoded to UTF-8 format.</error>",
                    StatusCode.SUBPROCESS_OUTPUT_DECODE_ERROR,
                )
        if jsonify:
            try:
                data = json.dumps(data, default=str)
            except Exception:
                raise ModuleException(
                    "<error>Results data could not be JSON encoded.</error>",
                    StatusCode.JSON_ENCODE_ERROR,
                )
        with open(filename, write_mode) as f:
            try:
                f.write(data)
            except Exception:
                raise ModuleException(
                    "<error>Could not write results data to file.</error>",
                    StatusCode.FILE_ERROR,
                )

    def run(self) -> Dict:
        """
        By default, raises NotImplementedError
        The module code should be added in the children
        """
        raise NotImplementedError()

    def _generate_error_response(
        self,
        msg: str,
        status_code: StatusCode,
        additional_info: str = None,
        subprocess_return_code: int = None,
        subprocess_standard_output=None,
        subprocess_standard_error=None,
    ) -> Dict:
        """
        Generates a custom response dictionary for errors
        :msg: message
        :status_code: one of the StatusCode enum
        :additional_info: additional info that you want to send to divy backend
        :subprocess_return_code If a subprocess call fails, this should be sent to the method. Otherwise, it is not used.
        :stdout and stderr If a subprocess call fails, this should be sent to the method. Otherwise, it is not used.
        """

        trace = traceback.format_exc()
        pattern = r"(?:AWS|aws_secret_access_key).*?(?:[A-Za-z0-9/+]{40})"
        trace = re.sub(pattern, "", trace)
        print(msg)

        return {
            "response": f"<error>[{self._module_name}]: {msg}</error>",
            "status_code": status_code.value,
            "trace": trace,
            "additional_info": additional_info,
            "subprocess_return_code": subprocess_return_code,
            "subprocess_standard_output": subprocess_standard_output,
            "subprocess_standard_error": "<error>subprocess_standard_error</error>",
        }

    def setup_aws_env_vars(self):
        """A helper method to setup commonly used AWS Env vars"""
        print("Setting up AWS Env vars")
        self.setup_aws_access_key_and_secret_key()

        if self.source_key_token:
            os.environ["AWS_SESSION_TOKEN"] = self.source_key_token

    def setup_aws_access_key_and_secret_key(self):
        """A helper method to setup AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars"""
        print("Setting up AWS Access key id and secret key vars")
        os.environ["AWS_ACCESS_KEY_ID"] = self.source_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = self.source_key

    def _get_data(self, client, method: str, key: str) -> Dict:
        """
        client: The boto3 client object.
        Method: The name of the method on the client object, such as "describe buckets"
        key: The JSON key where the data is stored.

        get_data: The boto3 method stored in a variable
        Page data: a single page of data
        Data: The entire dataset.
        
        Note: This method requires boto3 to be installed if used.
        """
        get_data = getattr(client, method)
        page_data = get_data()
        data = {}
        data[key] = []
        data[key].append(page_data[key])
        while "nextToken" in page_data:
            page_data = get_data(nextToken=page_data["nextToken"])
            data[key].append(page_data[key])

        # This is now in nested list structure if there was more than one page. Flatten into a single list.
        data[key] = list(itertools.chain(*data[key]))
        return data

    def _create_folder(self, path: str):
        os.makedirs(path, exist_ok=True)
        os.chdir(path)

        print(f"Created directory {path}")

    def has_authentication_error(self, exception):
        if isinstance(exception, ModuleException):
            error_string = exception.subprocess_standard_error
        else:
            error_string = exception

        if isinstance(error_string, bytes):
            error_string = error_string.decode("utf-8", "ignore")

        for exception_identifier in self._access_exception_list:
            if exception_identifier in error_string:
                return exception_identifier
        return False

    def assume_role_if_role_arn_provided(self):
        # todo: if assume role with 12 hour duration failes, then assume role again, get the max duration of role
        # then assume role again based on max duration
        if hasattr(self, "role_arn") and self.role_arn:
            print(f"assuming role")
            try:
                import boto3
            except ImportError:
                raise ModuleException(
                    "boto3 is required for AWS role assumption but is not installed",
                    StatusCode.PACKAGE_NOT_FOUND,
                )
            sts_client = boto3.client(
                "sts", **{"aws_access_key_id": self.source_key_id, "aws_secret_access_key": self.source_key}
            )
            assume_role_kwargs = {
                "RoleArn": f"{self.role_arn}",
                "RoleSessionName": f"{datetime.now().timestamp()}",
                "DurationSeconds": 43200,  # 12 hours
            }
            if hasattr(self, "external_id") and self.external_id:
                assume_role_kwargs["ExternalId"] = self.external_id

            response = sts_client.assume_role(**assume_role_kwargs)

            # role_creds = {
            #     "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            #     "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            #     "aws_session_token": response["Credentials"]["SessionToken"]
            # }
            # iam_client = boto3.client('iam', **role_creds)
            # response = iam_client.get_role(RoleName="AccuknoxOrgRole")
            # max_duration = response['Role']['MaxSessionDuration']
            # response = sts_client.assume_role(
            #     RoleArn=f"{self.role_arn}",
            #     RoleSessionName=f"{datetime.now().timestamp()}",
            #     DurationSeconds=max_duration,  # 4 hours
            # )

            self.source_key_id = response["Credentials"]["AccessKeyId"]
            self.source_key = response["Credentials"]["SecretAccessKey"]
            self.source_key_token = response["Credentials"]["SessionToken"]
