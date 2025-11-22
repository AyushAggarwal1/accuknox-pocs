"""
    This is the base class for asset inventory modules. These modules consist of aws_asset_inventory, gcp_asset_inventory,
    azure_asset_inventory, and ecr_inventory. It consists of a class that defines the installation dependencies for Steampipe so that
    they do not need to be defined in every module.
"""
from typing import Dict

import json
import os
import subprocess
import time
from json.decoder import JSONDecodeError

from base_module import BaseModule, ModuleException, StatusCode


class AssetInventoryBase(BaseModule):
    """Base class for all {aws,gcp,azure}_asset_inventory.py modules"""

    # For certain tables ReadOnlyAccess permission is not enough to do select * from. It does not allow to let query on certain columns, Mentioning the columns explicitly will make the module run.
    selection_string_dict = {
        "aws_kms_key": {
            "columns": "_ctx, account_id, akas, aliases, arn, aws_account_id, creation_date, customer_master_key_spec, deletion_date, description, enabled, id, key_manager, key_rotation_enabled, key_state, key_usage, origin, partition, policy, policy_std, region, title, valid_to",
        },
        "aws_iam_user": {"columns": "arn, akas, name, title, region, create_date, account_id, user_id, _ctx"},
        "gcp_project": {
            "columns": "_ctx, akas, create_time, labels, lifecycle_state, name, parent, project_id, project_number, self_link, tags, title",
        },
        "aws_accessanalyzer_analyzer": {
            "columns": "_ctx, account_id, akas, arn, created_at, last_resource_analyzed, last_resource_analyzed_at, name, region, status, status_reason, tags, title, type",
        },
        "aws_appautoscaling_target": {
            "columns": "_ctx, service_namespace, scalable_dimension, resource_id, creation_time, account_id, max_capacity, min_capacity, partition, region, role_arn, scalable_dimension, service_namespace, suspended_state, title",
            "where": "service_namespace = 'dynamodb'",
        },
        "aws_iam_role": {"columns": "*", "where": "inline_policies IS NOT NULL"},
        "aws_iam_policy": {"columns": "*", "where": "not is_aws_managed"},
        "aws_iam_policy_attachment": {"columns": "*", "where": "is_attached"},
    }

    def __init__(self, kwargs: Dict):
        super().__init__(kwargs)
        self.max_first_consecutive_allowed_fails = 5
        self.current_consecutive_fails = 0
        self.first_consecutively_failed = True

    def _get_selection_params(self, table):
        """
        This function returns the selection string from the dictionary for the two tables that are special cases. For all other tables it returns
        an asterisk by default, which means to select all fields from the table.
        """
        if table in self.selection_string_dict:
            params = self.selection_string_dict[table]
            columns = params["columns"]
            where = params.get("where", "")

            return columns, where
        return "*", ""

    def construct_steampipe_select_query(self, table):
        COLUMNS, WHERE = self._get_selection_params(table)
        query = f"select {COLUMNS} from {table}"
        if WHERE:
            query = f"{query} where {WHERE}"

        return query

    def _get_data(self, table):
        """
        This function gets the Steampipe data for a specific table and can be used in all Steampipe modules. It takes in the name of the table
        as a parameter.
        """
        print(f"<info>querying table {table}</info>")
        region_info = ""
        if self._module_name == "aws_asset_inventory":
            region_info = f"aws_region: {os.environ.get('AWS_DEFAULT_REGION', 'no region specified for aws')}"
        elif self._module_name == "oci_asset_inventory":
            region_info = f"oci_region: {os.environ.get('OCI_REGION', getattr(self, 'region', 'no region specified for oci'))}"

        steampipe_select_query = self.construct_steampipe_select_query(table)
        query = f'''steampipe query "{steampipe_select_query}" --output json'''
        # query = f'''su steampipeuser -m -c "steampipe query \\"{steampipe_select_query}\\" --output json"'''
        current_time = time.time()
        process = subprocess.run(
            query,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"It took {time.time() - current_time} seconds to fetch data for {table}")

        if process.returncode != 0:
            raise ModuleException(
                f"<error>Failed to run query on table: {table}, {region_info},  exc: {process.stderr} stdout: {process.stdout}</error>",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )
        if not process.stdout and process.stderr:
            raise ModuleException(
                f"<error>The process was killed when attempting to query table {table}, {region_info}, exc: {process.stderr} stdout: {process.stdout}</error>",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )
        if not process.stdout:
            raise ModuleException(
                f"<error>Failed to  run query on table: {table}, {region_info}, exc: {process.stderr} stdout:{process.stdout}</error>",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )
        try:
            return json.loads(process.stdout.decode("utf-8", "ignore"))
        except JSONDecodeError:
            # not logging process.stdout since it can contain sensitive information
            raise ModuleException(
                f"<error>An unexpected error occurred. The data was in an unexpected format, table: {table}, {region_info}, exc:{process.stderr}</error>",
                StatusCode.SUBPROCESS_ERROR,
                subprocess_return_code=process.returncode,
                subprocess_standard_output=process.stdout,
                subprocess_standard_error=process.stderr,
            )

    def call_get_data(self, table, retry_count=1):
        """
        calls get_data and if fails then retries with  retry_count times for given table for the failed query for
        authentication/authorization errors only else raise exception
        """
        try:
            data = self._get_data(table)
            self.first_consecutively_failed = False
            return data
        except ModuleException as ex:
            exception_identifier = self.has_authentication_error(ex)
            if retry_count > 0 and exception_identifier:
                print(f"<info>retrying for table {table} {retry_count} times</info>")
                time.sleep(5)
                return self.call_get_data(table, retry_count - 1)
            else:
                self.current_consecutive_fails += 1
                if exception_identifier:
                    # to email details error to the internal team
                    print(f"<INTERNAL-TEAM-ISSUE>{ex}</INTERNAL-TEAM-ISSUE>")
                    # mail short description of error to the clients
                    print(
                        f"<CUSTOMER-ISSUE>Steampipe failed to query table: {table} due to authorization/authentication issue {exception_identifier}</CUSTOMER-ISSUE>",
                    )
                    if (
                        self.first_consecutively_failed is True
                        and self.current_consecutive_fails >= self.max_first_consecutive_allowed_fails
                    ):
                        raise ex
                else:
                    # send detailed error message to the internal team
                    print(f"<INTERNAL-TEAM-ISSUE>{ex}</INTERNAL-TEAM-ISSUE>")
                    if (
                        self.first_consecutively_failed is True
                        and self.current_consecutive_fails >= self.max_first_consecutive_allowed_fails
                    ):
                        raise ex
