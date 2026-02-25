#!/usr/bin/env python3
"""
    The AWS Asset Inventory module collects metadata on AWS resources using an open source tool
    called Steampipe and writes the results to a JSON file.
"""
import os
import time
from datetime import datetime

import boto3

from base_module import ModuleException, StatusCode
from asset_inventory_base import AssetInventoryBase


def run(
    source_key_id=None,
    source_key=None,
    source_key_token=None,
    regions=None,
    label=None,
    role_arn=None,
    external_id=None,
):
    kwargs = dict(
        source_key_id=source_key_id,
        source_key=source_key,
        source_key_token=source_key_token,
        regions=regions,
        label=label,
        role_arn=role_arn,
        external_id=external_id,
    )
    return AWSAsset(kwargs).main()


class AWSAsset(AssetInventoryBase):
    """
    Pillar Example:
        source_key_id: ''                          # aws key id for the account to use to scrape aws information
        source_key: ''                             # aws key for the account to use to scrape aws information
        source_key_token: ''                       # Optional parameter if using STS assume role.
        regions : 'us-east-1, us-east-2'           # You can enter one region or multiple. If entering multiple regions
                                                   # It must be a comma separated list
                                                   # example: us-east-1, us-east-2, us-west-2
        label: 'TEST'                              # label to attach to filename
    """

    _module_name = "aws_asset_inventory"
    _access_exception_list = list(
        set(
            AssetInventoryBase._access_exception_list
            + [
                "AccessDenied",
                "AccessDeniedException",
                "NotAuthorized",
                "UnauthorizedOperation",
                "UnrecognizedClientException",
                "AuthorizationError",
            ],
        ),
    )

    _fields = [
        "source_key_id",
        "source_key",
        "regions",
        "label",
    ]

    mandatory_table_list = [
        "aws_account",
    ]
    global_table_list = [
        # "aws_account",
        "aws_iam_user",
        "aws_iam_role",
        "aws_iam_group",
        # "aws_iam_access_key",
        # "aws_iam_account_summary",
        # "aws_iam_credential_report",  # not required as we do not create assets
        "aws_iam_policy",
        "aws_iam_policy_attachment",
        "aws_region",
        # "aws_account_alternate_contact",
        # "aws_account_contact",
        "aws_cloudfront_function",
        "aws_cloudfront_cache_policy",
        "aws_cloudfront_distribution",
        "aws_route53_domain",
        # "aws_route53_record",
        "aws_route53_zone",
        # "aws_s3_account_settings",
    ]
    regional_table_list = [
        "aws_accessanalyzer_analyzer",
        "aws_accessanalyzer_finding",
        "aws_acm_certificate",
        "aws_acmpca_certificate_authority",
        "aws_amplify_app",
        # "aws_api_gateway_api_key",
        "aws_api_gateway_authorizer",
        "aws_api_gateway_method",
        "aws_api_gateway_rest_api",
        "aws_api_gateway_stage",
        # "aws_athena_workgroup",
        "aws_auditmanager_assessment",
        "aws_auditmanager_evidence",
        "aws_auditmanager_evidence_folder",
        "aws_auditmanager_framework",
        # "aws_availability_zone",
        "aws_backup_job",
        "aws_backup_plan",
        # "aws_backup_protected_resource",
        "aws_backup_recovery_point",
        "aws_backup_selection",
        "aws_backup_vault",
        "aws_cloudformation_stack",
        "aws_cloudformation_stack_resource",
        "aws_cloudformation_stack_set",
        "aws_cloudtrail_channel",
        "aws_cloudwatch_alarm",
        "aws_cloudtrail_trail",
        # "aws_cloudwatch_metric",
        "aws_cloudwatch_log_group",
        # "aws_cloudwatch_log_stream",
        "aws_codeartifact_domain",
        "aws_codeartifact_repository",
        "aws_codebuild_project",
        "aws_codedeploy_deployment_config",
        "aws_codepipeline_pipeline",
        "aws_cognito_identity_pool",
        "aws_cognito_user_pool",
        "aws_config_configuration_recorder",
        "aws_dax_cluster",
        # "aws_dax_parameter",
        # "aws_dax_parameter_group",
        "aws_dax_subnet_group",
        "aws_docdb_cluster",
        "aws_docdb_cluster_instance",
        "aws_docdb_cluster_snapshot",
        "aws_dynamodb_backup",
        # "aws_dynamodb_metric_account_provisioned_read_capacity_util",
        "aws_dynamodb_table",
        "aws_ebs_volume",
        "aws_ebs_snapshot",
        "aws_ec2_instance",
        "aws_ec2_application_load_balancer",
        "aws_ec2_instance_availability",
        # "aws_ec2_instance_type",
        "aws_ec2_key_pair",
        "aws_ec2_launch_configuration",
        "aws_ec2_launch_template",
        "aws_ec2_launch_template_version",
        "aws_ec2_load_balancer_listener",
        "aws_ec2_managed_prefix_list",
        # "aws_ec2_managed_prefix_list_entry",
        "aws_ec2_network_interface",
        "aws_ec2_network_load_balancer",
        # "aws_ec2_regional_settings",
        # "aws_ec2_ssl_policy",
        "aws_ec2_target_group",
        # "aws_ecr_image",
        "aws_ec2_reserved_instance",
        # "aws_ecr_repository",
        "aws_kms_key",
        "aws_ecs_cluster",
        # "aws_efs_file_system",
        # "aws_efs_mount_target",
        # "aws_eks_addon",
        "aws_eks_cluster",
        "aws_elasticache_cluster",
        # "aws_elastic_beanstalk_application",
        # "aws_elastic_beanstalk_environment",
        # "aws_elasticache_parameter_group",
        # "aws_emr_block_public_access_configuration",
        # "aws_emr_cluster",
        # "aws_emr_instance_group",
        # "aws_eventbridge_bus",
        # "aws_eventbridge_rule",
        # "aws_glacier_vault",
        # "aws_glue_data_catalog_encryption_settings",
        # "aws_glue_job",
        # "aws_kinesis_stream",
        # "aws_kms_alias",
        "aws_lambda_function",
        # "aws_lambda_layer",
        # "aws_lambda_layer_version",
        # "aws_lambda_version",
        # "aws_msk_cluster",
        # "aws_msk_serverless_cluster",
        # "aws_neptune_db_cluster",
        # "aws_neptune_db_cluster_snapshot",
        # "aws_networkfirewall_firewall",
        # "aws_networkfirewall_firewall_policy",
        # "aws_networkfirewall_rule_group",
        "aws_rds_db_instance",
        "aws_rds_db_cluster",
        # "aws_rds_db_cluster_snapshot",
        # "aws_rds_db_cluster_parameter_group",
        # "aws_rds_db_instance_automated_backup",
        # "aws_rds_db_option_group",
        # "aws_rds_db_parameter_group",
        "aws_rds_db_proxy",
        # "aws_rds_db_snapshot",
        "aws_rds_db_subnet_group",
        "aws_redshift_cluster",
        "aws_redshift_subnet_group",
        "aws_redshiftserverless_namespace",
        "aws_redshiftserverless_workgroup",
        # "aws_route53_resolver_endpoint",
        # "aws_route53_resolver_rule",
        "aws_s3_access_point",
        "aws_s3_bucket",
        "aws_sagemaker_domain",
        # "aws_secretsmanager_secret",
        # "aws_service_discovery_namespace",
        # "aws_ses_domain_identity",
        "aws_sns_subscription",
        "aws_sns_topic",
        # "aws_sns_topic_subscription",
        "aws_sqs_queue",
        # "aws_ssm_association",
        # "aws_ssm_inventory",
        # "aws_ssoadmin_instance",
        # "aws_sts_caller_identity",
        # "aws_tagging_resource",
        # "aws_vpc_dhcp_options",
        "aws_vpc",
        "aws_vpc_subnet",
        "aws_vpc_eip",
        # "aws_vpc_endpoint",
        # "aws_vpc_flow_log",
        # "aws_vpc_internet_gateway",
        "aws_vpc_nat_gateway",
        # "aws_vpc_nat_gateway_metric_bytes_out_to_destination",
        "aws_vpc_security_group",
        "aws_vpc_security_group_rule",
        "aws_vpc_network_acl",
        "aws_vpc_route",
        "aws_vpc_route_table",
        # "aws_vpc_vpn_gateway",
        # "aws_vpc_peering_connection",
        # "aws_wafv2_ip_set",
        # "aws_wafv2_regex_pattern_set",
        # "aws_wafv2_rule_group",
        # "aws_wafv2_web_acl",
        # "aws_wellarchitected_lens",
        "aws_workspaces_workspace",
    ]

    def run(self):
        data = {}

        self.regions = self.regions.replace(" ", "")
        self.regions = self.regions.split(",")

        self.assume_role_if_role_arn_provided()

        # Setup AWS Env Variables
        self.setup_aws_env_vars()
        os.environ["AWS_DEFAULT_REGION"] = self.regions[0]
        for table in self.mandatory_table_list:
            print(f"<info>About to fetch: {table}</info>")
            attempts = 1
            while attempts <= 3:
                if attempts > 1:
                    print(f"retrying attempt {attempts} for table: {table}")

                try:
                    output = self._get_data(table)
                    if output:
                        data.update({table: output})
                    else:
                        raise ModuleException(
                            f"<error>Failed to run query on mandatory table: {table},  no output</error>",
                            StatusCode.NO_DATA,
                        )
                    break
                except Exception as ex:
                    time.sleep(1)
                    if attempts >= 3:
                        raise ex
                    attempts += 1

        for table in self.global_table_list:
            print(f"<info>About to fetch: {table}</info>")
            output = self.call_get_data(table)
            if output:
                data.update({table: output})

        attached_iam_policy_data = self.call_get_data("aws_iam_policy where is_attached", retry_count=5)
        if attached_iam_policy_data:
            data.update({"attached_aws_iam_policy": attached_iam_policy_data})

        for table in self.regional_table_list:
            data_dict = {}
            for region in self.regions:
                os.environ["AWS_DEFAULT_REGION"] = region
                output = self.call_get_data(table)
                if output:
                    data_dict.update({region: output})
                    data.update({table: data_dict})

        # Save to file
        filename = self.construct_filename("AM", "json")
        # in case all the query failed we should not end up writing blank file
        if data:
            self._write_to_file(filename, data, decode=False, jsonify=True)
            print(f"<success>Success! {filename} written to /tmp folder</success>")
            return {
                "response": f"Success!  {filename} written to /tmp folder",
                "status_code": StatusCode.SUCCESS.value,
            }
        return {
            "response": "Fail! no data available to write on the disk",
            "status_code": StatusCode.SUCCESS.value,
        }


if __name__ == "__main__":
    run(
        source_key_id=os.environ.get("source_key_id"),
        source_key=os.environ.get("source_key"),
        source_key_token=os.environ.get("source_key_token"),
        regions=os.environ.get("regions"),
        label=os.environ.get("label"),
        role_arn=os.environ.get("role_arn"),
        external_id=os.environ.get("external_id"),
    )


# export source_key_id=abc
# export source_key=abc
# export regions=us-east-1
# export label=TEST

# python3 aws_asset_inventory.py