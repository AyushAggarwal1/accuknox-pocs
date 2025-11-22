#!/usr/bin/env python3
"""
    The Azure Asset Inventory module collects metadata on Azure resources using an open source tool
    called Steampipe and writes the results to a JSON file.
"""

import logging
import os
import subprocess

from base_module import StatusCode
from asset_inventory_base import AssetInventoryBase

logger = logging.getLogger(__name__)


def run(
    subscription_id=None,
    tenant_id=None,
    client_id=None,
    client_secret=None,
    label=None,
):
    kwargs = dict(
        subscription_id=subscription_id,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        label=label,
    )
    return AzureAsset(kwargs).main()


class AzureAsset(AssetInventoryBase):
    """
    Required fields:
    @subscription_id
    @tenant_id
    @client_id
    @client_secret
    @label
    """

    _module_name = "azure_asset"
    _access_exception_list = list(
        set(
            AssetInventoryBase._access_exception_list
            + [
                "NoAuthenticationInformation",
                "InvalidAuthenticationInfo",
                "AccountIsDisabled",
                "UnauthorizedOperation",
                "UnrecognizedClientException",
                "AuthorizationError",
                "AuthenticationFailed",
                "InsufficientAccountPermissions",
                "Authorization_RequestDenied",
                "AuthorizationFailed",
            ],
        ),
    )

    _fields = [
        "subscription_id",
        "tenant_id",
        "client_id",
        "client_secret",
        "label",
    ]
    table_list = [
         "azure_subscription",
        "azure_resource_group",
        "azure_storage_container",
        "azure_compute_virtual_machine",
        "azure_network_interface",
        "azure_virtual_network",
        "azure_subnet",
        "azure_public_ip"]



    table_list1 = [
        "azure_subscription",
        "azure_resource_group",
        "azure_storage_container",
        "azure_compute_virtual_machine",
        "azure_network_interface",
        "azure_virtual_network",
        "azure_subnet",
        "azure_public_ip",
        "azure_network_security_group",
        "azure_application_security_group",
        # # Commented out due to issue in steampipe
        # # https://github.com/turbot/steampipe-plugin-azure/issues/808
        "azure_role_assignment",
        "azure_role_definition",
        # "azure_ad_group", # DEPRECATED
        # "azure_ad_service_principal", # DEPRECATED
        # "azure_ad_user", # DEPRECATED
        # "azuread_group",
        # "azuread_service_principal",
        # "azuread_user",
        "azure_lb",
        "azure_key_vault",
        "azure_key_vault_key",
        "azure_kubernetes_cluster",
        "azure_redis_cache",
        "azure_sql_database",
        "azure_route_table",
        # "azure_log_profile",
        "azure_log_alert",
        "azure_compute_disk",
        # "azure_alert_management",
        "azure_api_management",
        "azure_app_configuration",
        "azure_app_service_environment",
        "azure_app_service_function_app",
        "azure_app_service_plan",
        "azure_app_service_web_app",
        "azure_app_service_web_app_slot",
        "azure_application_gateway",
        "azure_application_insight",
        "azure_automation_account",
        "azure_automation_variable",
        "azure_bastion_host",
        "azure_batch_account",
        "azure_cognitive_account",
        "azure_compute_availability_set",
        "azure_compute_disk_access",
        "azure_compute_disk_encryption_set",
        # "azure_compute_resource_sku",
        "azure_compute_snapshot",
        "azure_compute_ssh_key",
        "azure_compute_virtual_machine_scale_set",
        "azure_compute_virtual_machine_scale_set_vm",
        # "azure_consumption_usage",
        "azure_container_group",
        "azure_container_registry",
        "azure_data_factory",
        "azure_data_factory_dataset",
        "azure_data_factory_pipeline",
        "azure_databricks_workspace",
        "azure_dns_zone",
        "azure_eventgrid_domain",
        "azure_eventgrid_topic",
        "azure_eventhub_namespace",
        "azure_express_route_circuit",
        "azure_firewall",
        "azure_firewall_policy",
        "azure_hpc_cache",
        "azure_iothub",
        "azure_key_vault_key_version",
        "azure_key_vault_managed_hardware_security_module",
        "azure_kusto_cluster",
        # "azure_lb_backend_address_pool",
        "azure_lb_nat_rule",
        "azure_lb_outbound_rule",
        "azure_lb_probe",
        "azure_lb_rule",
        "azure_machine_learning_workspace",
        "azure_maintenance_configuration",
        # "azure_management_group",
        "azure_management_lock",
        # "azure_monitor_log_profile",
        "azure_mssql_elasticpool",
        "azure_mssql_managed_instance",
        "azure_mysql_flexible_server",
        "azure_nat_gateway",
        "azure_network_watcher",
        # "azure_policy_assignment",
        # "azure_policy_definition", # DATALIST
        "azure_postgresql_flexible_server",
        "azure_postgresql_server",
        "azure_private_dns_zone",
        # "azure_recovery_services_backup_job",
        "azure_recovery_services_vault",
        "azure_search_service",
        # "azure_security_center_auto_provisioning",
        "azure_servicebus_namespace",
        "azure_signalr_service",
        "azure_spring_cloud_service",
        "azure_sql_server",
        "azure_storage_account",
        "azure_storage_blob_service",
        "azure_storage_queue",
        "azure_storage_share_file",
        "azure_storage_sync",
        "azure_storage_table",
        "azure_storage_table_service",
        "azure_stream_analytics_job",
        # "azure_synapse_workspace",
        "azure_tenant",
        "azure_virtual_network_gateway",
        # "azure_api_management_backend",
        # "azure_backup_policy",
        # "azure_compute_disk_metric_read_ops", # NOT REQUIRED
        # "azure_compute_disk_metric_read_ops_daily",
        # "azure_compute_disk_metric_read_ops_hourly",
        # "azure_compute_disk_metric_write_ops",
        # "azure_compute_disk_metric_write_ops_daily",
        # "azure_compute_disk_metric_write_ops_hourly",
        # "azure_compute_image",
        # "azure_compute_virtual_machine_metric_available_memory", # NOT REQUIRED
        # "azure_compute_virtual_machine_metric_available_memory_daily",
        # "azure_compute_virtual_machine_metric_available_memory_hourly",
        # "azure_compute_virtual_machine_metric_cpu_utilization",
        # "azure_compute_virtual_machine_metric_cpu_utilization_daily",
        # "azure_compute_virtual_machine_metric_cpu_utilization_hourly",
        # "azure_compute_virtual_machine_scale_set_network_interface",
        # "azure_cosmosdb_account",
        # "azure_cosmosdb_mongo_collection", # REQUIRES IDENTIFIER
        # "azure_cosmosdb_mongo_database",
        # "azure_cosmosdb_restorable_database_account",
        # "azure_cosmosdb_sql_database",
        # "azure_data_lake_analytics_account",
        # "azure_data_lake_store", # REVISIT
        # "azure_databox_edge_device", # REVISIT
        # "azure_diagnostic_setting",
        # "azure_frontdoor",
        # "azure_hdinsight_cluster", # REVISIT
        # "azure_healthcare_service",  # REVISIT
        # "azure_hybrid_compute_machine", # REVISIT
        # "azure_hybrid_kubernetes_connected_cluster", # REVISIT
        # "azure_iothub_dps",
        # "azure_key_vault_deleted_vault",
        # "azure_key_vault_secret", # REVISIT
        # "azure_kubernetes_service_version", #Not an asset, gives thousand of results which are of no concern
        # "azure_location", #DATALIST
        # "azure_logic_app_workflow",
        # "azure_mariadb_server", # DEPRECATED
        # # Commented out due to issue in steampipe
        # # https://github.com/turbot/steampipe-plugin-azure/issues/807
        # "azure_monitor_activity_log_event",
        # "azure_mssql_virtual_machine",
        # "azure_mysql_server",
        # "azure_network_watcher_flow_log",
        # # "azure_provider", # DATALIST
        # "azure_resource_link", # REVISIT
        # "azure_security_center_automation",
        # "azure_security_center_contact",
        # "azure_security_center_jit_network_access_policy",
        # "azure_security_center_setting",
        # "azure_security_center_sub_assessment",
        # "azure_security_center_subscription_pricing",
        # "azure_service_fabric_cluster",
        # "azure_storage_blob" #REQUIRES IDENTIFIER
    ]

    @staticmethod
    def _modify_config():
        return subprocess.run(
            [
                "sed",
                "-i",
                's/#ignore_error_codes = \[/ignore_error_codes = ["ResourceGroupNotFound", /g',
                "/home/ayush/.steampipe/config/azure.spc",
            ],
        )

    def run(self):
        data = {}
        os.environ["AZURE_TENANT_ID"] = self.tenant_id
        os.environ["AZURE_SUBSCRIPTION_ID"] = self.subscription_id
        os.environ["AZURE_CLIENT_ID"] = self.client_id
        os.environ["AZURE_CLIENT_SECRET"] = self.client_secret

        # Update Azure Config
        self._modify_config()

        for table in self.table_list:
            output = self.call_get_data(table)
            if output:
                data.update({table: output})

        # Save to file
        filename = self.construct_filename("AZM", "json")
        # in case all the query failed we should not end up writing blank file
        if data:
            self._write_to_file(filename, data, decode=False, jsonify=True)
            print(f"Success! {filename} written to /tmp folder")
            return {
                "response": f"Success! {filename} written to /tmp folder",
                "status_code": StatusCode.SUCCESS.value,
            }

        return {
            "response": "Fail!  no data available to write on the disk",
            "status_code": StatusCode.SUCCESS.value,
        }


if __name__ == "__main__":
    run(
        subscription_id=os.environ["subscription_id"],
        tenant_id=os.environ["tenant_id"],
        client_id=os.environ["client_id"],
        client_secret=os.environ["client_secret"],
        label=os.environ.get("label"),
    )


