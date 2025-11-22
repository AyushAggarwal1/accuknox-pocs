#!/usr/bin/env python3
"""
    The OCI Asset Inventory module collects metadata on Oracle Cloud resources using Steampipe
    and writes the results to a JSON file.
"""
import os
import pwd
import re
from typing import List, Optional, Union
from base_module import StatusCode
from asset_inventory_base import AssetInventoryBase


def run(
    tenancy_ocid=None,
    user_ocid=None,
    fingerprint=None,
    private_key=None,
    regions=None,
    label=None,
    compartment_id=None,
):
    kwargs = dict(
        tenancy_ocid=tenancy_ocid,
        user_ocid=user_ocid,
        fingerprint=fingerprint,
        private_key=private_key,
        regions=regions,
        label=label,
        compartment_id=compartment_id,
    )
    return OCIAsset(kwargs).main()


class OCIAsset(AssetInventoryBase):
    """
    Pillar Example:
        tenancy: 'ocid1.tenancy.oc1..xxxxx'
        user: 'ocid1.user.oc1..xxxxx'
        fingerprint: 'xx:xx:xx:xx:xx'
        key_file: '/path/to/key_file.pem'
        regions: 'us-ashburn-1, us-phoenix-1'  # You can enter one region or multiple. If entering multiple regions
                                               # It must be a comma separated list
        label: 'TEST'
        compartment_id: 'ocid1.compartment.oc1..xxxxx'
    """

    _module_name = "oci_asset_inventory"
    _access_exception_list = list(
        set(
            AssetInventoryBase._access_exception_list
            + [
                "NotAuthorizedOrNotFound",
                "AuthorizationFailed",
                "Forbidden",
                "NotAuthenticated",
                "FREE_TIER_NOT_SUPPORTED",  # Free tier limitations
                "InvalidParameter",  # Invalid parameters like compartmentId
                "no such host",  # DNS resolution issues
                "ServiceError",  # General service errors
                "Cloudguard subscription is not available",  # Cloud Guard subscription issues
                "subscription is not available",  # General subscription issues
                "missing 2 required quals",  # Missing required qualifiers
                "missing 3 required quals",  # Missing required qualifiers (KMS)
                "compartmentId is not available",  # Compartment parameter issues
                'column "compartment_id" does not exist',  # Schema mismatch issues
                "SQLSTATE 42703",  # Column doesn't exist SQL error
                "SQLSTATE HV000",  # Missing qualifiers SQL error
            ],
        ),
    )

    _fields = [
        "tenancy_ocid",
        "user_ocid",
        "fingerprint",
        "private_key",
        "regions",
        "label",
    ]

    # Explicit attribute annotations to satisfy static analysis
    tenancy_ocid: str
    user_ocid: str
    fingerprint: str
    private_key: str
    regions: Union[str, List[str]]
    label: str
    compartment_id: Optional[str] = None

    global_table_list = [
        # Identity and Access Management
        "oci_identity_tenancy",
        "oci_identity_user",
        "oci_identity_group",
        "oci_identity_policy",
        "oci_identity_compartment",
        "oci_identity_api_key",
        "oci_identity_auth_token",
        "oci_identity_authentication_policy",
        "oci_identity_availability_domain",
        "oci_identity_customer_secret_key",
        "oci_identity_db_credential",
        "oci_identity_domain",
        "oci_identity_dynamic_group",
        "oci_identity_network_source",
        "oci_identity_tag_default",
        "oci_identity_tag_namespace",
        # Regional information
        "oci_region",
    ]

    # Compartment-level tables that require compartment_id filtering
    compartment_level_tables = [
        # Application Development & Management
        "oci_adm_knowledge_base",
        "oci_adm_vulnerability_audit",
        "oci_ai_anomaly_detection_ai_private_endpoint",
        "oci_ai_anomaly_detection_data_asset",
        "oci_ai_anomaly_detection_model",
        "oci_ai_anomaly_detection_project",
        "oci_analytics_instance",
        # API Gateway
        "oci_apigateway_api",
        # Application Migration
        "oci_application_migration_migration",
        "oci_application_migration_source",
        # Container Registry & Artifacts
        "oci_artifacts_container_image",
        "oci_artifacts_container_image_signature",
        "oci_artifacts_container_repository",
        "oci_artifacts_generic_artifact",
        "oci_artifacts_repository",
        # Auto Scaling
        "oci_autoscaling_auto_scaling_configuration",
        "oci_autoscaling_auto_scaling_policy",
        # Bastion
        "oci_bastion_bastion",
        # Big Data Service
        "oci_bds_bds_instance",
        # Budget
        "oci_budget_alert_rule",
        "oci_budget_budget",
        # Certificates
        "oci_certificates_management_association",
        "oci_certificates_management_ca_bundle",
        "oci_certificates_management_certificate",
        "oci_certificates_management_certificate_authority",
        # Cloud Guard
        "oci_cloud_guard_detector_recipe",
        "oci_cloud_guard_managed_list",
        "oci_cloud_guard_responder_recipe",
        "oci_cloud_guard_target",
        # Container Instances
        "oci_container_instances_container",
        "oci_container_instances_container_instance",
        # Container Engine (OKE)
        "oci_containerengine_cluster",
        # Core Compute & Networking
        "oci_core_instance",
        "oci_core_instance_configuration",
        "oci_core_instance_metric_cpu_utilization",
        "oci_core_instance_metric_cpu_utilization_daily",
        "oci_core_instance_metric_cpu_utilization_hourly",
        "oci_core_image",
        "oci_core_image_custom",
        "oci_core_cluster_network",
        "oci_core_vcn",
        "oci_core_subnet",
        "oci_core_internet_gateway",
        "oci_core_nat_gateway",
        "oci_core_service_gateway",
        "oci_core_local_peering_gateway",
        "oci_core_drg",
        "oci_core_route_table",
        "oci_core_security_list",
        "oci_core_network_security_group",
        "oci_core_dhcp_options",
        "oci_core_public_ip",
        "oci_core_public_ip_pool",
        "oci_core_vnic_attachment",
        # Block & Boot Volumes
        "oci_core_volume",
        "oci_core_volume_attachment",
        "oci_core_volume_backup",
        "oci_core_volume_backup_policy",
        "oci_core_volume_group",
        "oci_core_block_volume_replica",
        "oci_core_boot_volume",
        "oci_core_boot_volume_attachment",
        "oci_core_boot_volume_backup",
        "oci_core_boot_volume_replica",
        "oci_core_boot_volume_metric_read_ops",
        "oci_core_boot_volume_metric_read_ops_daily",
        "oci_core_boot_volume_metric_read_ops_hourly",
        "oci_core_boot_volume_metric_write_ops",
        "oci_core_boot_volume_metric_write_ops_daily",
        "oci_core_boot_volume_metric_write_ops_hourly",
        # Load Balancers
        "oci_core_load_balancer",
        "oci_core_network_load_balancer",
        # Database Services
        "oci_database_db_system",
        "oci_database_db_home",
        "oci_database_db",
        "oci_database_autonomous_database",
        "oci_database_autonomous_db_metric_cpu_utilization",
        "oci_database_autonomous_db_metric_cpu_utilization_daily",
        "oci_database_autonomous_db_metric_cpu_utilization_hourly",
        "oci_database_autonomous_db_metric_storage_utilization",
        "oci_database_autonomous_db_metric_storage_utilization_daily",
        "oci_database_autonomous_db_metric_storage_utilization_hourly",
        "oci_database_cloud_vm_cluster",
        "oci_database_exadata_infrastructure",
        "oci_database_pluggable_database",
        "oci_database_software_image",
        # DevOps
        "oci_devops_project",
        "oci_devops_repository",
        # DNS
        "oci_dns_rrset",
        "oci_dns_tsig_key",
        "oci_dns_zone",
        # Events
        "oci_events_rule",
        # File Storage
        "oci_file_storage_file_system",
        "oci_file_storage_mount_target",
        "oci_file_storage_snapshot",
        # Functions
        "oci_functions_application",
        "oci_functions_function",
        # Key Management
        "oci_kms_key",
        "oci_kms_key_version",
        "oci_kms_vault",
        # Logging
        "oci_logging_log",
        "oci_logging_log_group",
        "oci_logging_search",
        # MySQL Database Service
        "oci_mysql_backup",
        "oci_mysql_channel",
        "oci_mysql_configuration",
        "oci_mysql_configuration_custom",
        "oci_mysql_db_system",
        "oci_mysql_db_system_metric_connections",
        "oci_mysql_db_system_metric_connections_daily",
        "oci_mysql_db_system_metric_connections_hourly",
        "oci_mysql_db_system_metric_cpu_utilization",
        "oci_mysql_db_system_metric_cpu_utilization_daily",
        "oci_mysql_db_system_metric_cpu_utilization_hourly",
        "oci_mysql_db_system_metric_memory_utilization",
        "oci_mysql_db_system_metric_memory_utilization_daily",
        "oci_mysql_heat_wave_cluster",
        # Network Firewall
        "oci_network_firewall_firewall",
        "oci_network_firewall_policy",
        # NoSQL Database
        "oci_nosql_table",
        "oci_nosql_table_metric_read_throttle_count",
        "oci_nosql_table_metric_read_throttle_count_daily",
        "oci_nosql_table_metric_read_throttle_count_hourly",
        "oci_nosql_table_metric_storage_utilization",
        "oci_nosql_table_metric_storage_utilization_daily",
        "oci_nosql_table_metric_storage_utilization_hourly",
        "oci_nosql_table_metric_write_throttle_count",
        "oci_nosql_table_metric_write_throttle_count_daily",
        "oci_nosql_table_metric_write_throttle_count_hourly",
        # Object Storage
        "oci_objectstorage_bucket",
        # Notifications
        "oci_ons_notification_topic",
        "oci_ons_subscription",
        # Queue
        "oci_queue_queue",
        # Resource Search
        "oci_resource_search",
        # Resource Manager
        "oci_resourcemanager_stack",
        # Streaming
        "oci_streaming_stream",
        # Vault
        "oci_vault_secret",
    ]

    regional_table_list = [
        # Application Development & Management
        "oci_adm_knowledge_base",
        "oci_adm_vulnerability_audit",
        "oci_ai_anomaly_detection_ai_private_endpoint",
        "oci_ai_anomaly_detection_data_asset",
        "oci_ai_anomaly_detection_model",
        "oci_ai_anomaly_detection_project",
        "oci_analytics_instance",
        # API Gateway
        "oci_apigateway_api",
        # Application Migration
        "oci_application_migration_migration",
        "oci_application_migration_source",
        # Container Registry & Artifacts
        "oci_artifacts_container_image",
        "oci_artifacts_container_image_signature",
        "oci_artifacts_container_repository",
        "oci_artifacts_generic_artifact",
        "oci_artifacts_repository",
        # Auto Scaling
        "oci_autoscaling_auto_scaling_configuration",
        "oci_autoscaling_auto_scaling_policy",
        # Bastion
        "oci_bastion_bastion",
        # Big Data Service
        "oci_bds_bds_instance",
        # Budget
        "oci_budget_alert_rule",
        "oci_budget_budget",
        # Certificates
        "oci_certificates_management_association",
        "oci_certificates_management_ca_bundle",
        "oci_certificates_management_certificate",
        "oci_certificates_management_certificate_authority",
        # Cloud Guard
        "oci_cloud_guard_detector_recipe",
        "oci_cloud_guard_managed_list",
        "oci_cloud_guard_responder_recipe",
        "oci_cloud_guard_target",
        # Container Instances
        "oci_container_instances_container",
        "oci_container_instances_container_instance",
        # Container Engine (OKE)
        "oci_containerengine_cluster",
        # Core Compute & Networking
        "oci_core_instance",
        "oci_core_instance_configuration",
        "oci_core_instance_metric_cpu_utilization",
        "oci_core_instance_metric_cpu_utilization_daily",
        "oci_core_instance_metric_cpu_utilization_hourly",
        "oci_core_image",
        "oci_core_image_custom",
        "oci_core_cluster_network",
        "oci_core_vcn",
        "oci_core_subnet",
        "oci_core_internet_gateway",
        "oci_core_nat_gateway",
        "oci_core_service_gateway",
        "oci_core_local_peering_gateway",
        "oci_core_drg",
        "oci_core_route_table",
        "oci_core_security_list",
        "oci_core_network_security_group",
        "oci_core_dhcp_options",
        "oci_core_public_ip",
        "oci_core_public_ip_pool",
        "oci_core_vnic_attachment",
        # Block & Boot Volumes
        "oci_core_volume",
        "oci_core_volume_attachment",
        "oci_core_volume_backup",
        "oci_core_volume_backup_policy",
        "oci_core_volume_group",
        "oci_core_block_volume_replica",
        "oci_core_boot_volume",
        "oci_core_boot_volume_attachment",
        "oci_core_boot_volume_backup",
        "oci_core_boot_volume_replica",
        "oci_core_boot_volume_metric_read_ops",
        "oci_core_boot_volume_metric_read_ops_daily",
        "oci_core_boot_volume_metric_read_ops_hourly",
        "oci_core_boot_volume_metric_write_ops",
        "oci_core_boot_volume_metric_write_ops_daily",
        "oci_core_boot_volume_metric_write_ops_hourly",
        # Load Balancers
        "oci_core_load_balancer",
        "oci_core_network_load_balancer",
        # Database Services
        "oci_database_db_system",
        "oci_database_db_home",
        "oci_database_db",
        "oci_database_autonomous_database",
        "oci_database_autonomous_db_metric_cpu_utilization",
        "oci_database_autonomous_db_metric_cpu_utilization_daily",
        "oci_database_autonomous_db_metric_cpu_utilization_hourly",
        "oci_database_autonomous_db_metric_storage_utilization",
        "oci_database_autonomous_db_metric_storage_utilization_daily",
        "oci_database_autonomous_db_metric_storage_utilization_hourly",
        "oci_database_cloud_vm_cluster",
        "oci_database_exadata_infrastructure",
        "oci_database_pluggable_database",
        "oci_database_software_image",
        # DevOps
        "oci_devops_project",
        "oci_devops_repository",
        # DNS
        "oci_dns_rrset",
        "oci_dns_tsig_key",
        "oci_dns_zone",
        # Events
        "oci_events_rule",
        # File Storage
        "oci_file_storage_file_system",
        "oci_file_storage_mount_target",
        "oci_file_storage_snapshot",
        # Functions
        "oci_functions_application",
        "oci_functions_function",
        # Key Management
        "oci_kms_key",
        "oci_kms_key_version",
        "oci_kms_vault",
        # Logging
        "oci_logging_log",
        "oci_logging_log_group",
        "oci_logging_search",
        # MySQL Database Service
        "oci_mysql_backup",
        "oci_mysql_channel",
        "oci_mysql_configuration",
        "oci_mysql_configuration_custom",
        "oci_mysql_db_system",
        "oci_mysql_db_system_metric_connections",
        "oci_mysql_db_system_metric_connections_daily",
        "oci_mysql_db_system_metric_connections_hourly",
        "oci_mysql_db_system_metric_cpu_utilization",
        "oci_mysql_db_system_metric_cpu_utilization_daily",
        "oci_mysql_db_system_metric_cpu_utilization_hourly",
        "oci_mysql_db_system_metric_memory_utilization",
        "oci_mysql_db_system_metric_memory_utilization_daily",
        "oci_mysql_heat_wave_cluster",
        # Network Firewall
        "oci_network_firewall_firewall",
        "oci_network_firewall_policy",
        # NoSQL Database
        "oci_nosql_table",
        "oci_nosql_table_metric_read_throttle_count",
        "oci_nosql_table_metric_read_throttle_count_daily",
        "oci_nosql_table_metric_read_throttle_count_hourly",
        "oci_nosql_table_metric_storage_utilization",
        "oci_nosql_table_metric_storage_utilization_daily",
        "oci_nosql_table_metric_storage_utilization_hourly",
        "oci_nosql_table_metric_write_throttle_count",
        "oci_nosql_table_metric_write_throttle_count_daily",
        "oci_nosql_table_metric_write_throttle_count_hourly",
        # Object Storage
        "oci_objectstorage_bucket",
        # Notifications
        "oci_ons_notification_topic",
        "oci_ons_subscription",
        # Queue
        "oci_queue_queue",
        # Resource Search
        "oci_resource_search",
        # Resource Manager
        "oci_resourcemanager_stack",
        # Streaming
        "oci_streaming_stream",
        # Vault
        "oci_vault_secret",
    ]

    def construct_steampipe_select_query(self, table):
        columns, base_where = self._get_selection_params(table)

        # In compartment mode, always select * and filter only by compartment_id
        if (
            getattr(self, "compartment_id", None)
            and table not in self.global_table_list
            and not self._is_tenant_level_table(table)
        ):
            query = f"select * from {table} where compartment_id = '{self.compartment_id}'"
            print("steampipe query ------------",query)
            return query
        if getattr(self, "compartment_id", None) and table == "oci_identity_compartment":
            return f"select * from {table} where id = '{self.compartment_id}'"
        query = f"select {columns} from {table}"

        filters = []
        if base_where:
            filters.append(base_where)

        if filters:
            query += " where " + " and ".join(filters)
        print("steampipe query ------------",query)

        return query

    def _is_tenant_level_table(self, table):
        """
        Check if a table is tenant-level (doesn't have compartment_id column)
        These are typically identity/global services that exist at the tenancy level
        """
        tenant_level_tables = {
            # Identity and access management tables (tenant-level)
            "oci_identity_user",
            "oci_identity_group",
            "oci_identity_api_key",
            "oci_identity_auth_token",
            "oci_identity_authentication_policy",
            "oci_identity_customer_secret_key",
            "oci_identity_db_credential",
            "oci_identity_dynamic_group",
            "oci_identity_network_source",
            "oci_region",  # Regions are global
            # Certificate version tables (these have different structure)
            "oci_certificates_management_certificate_authority_version",
            "oci_certificates_management_certificate_version",
            # Volume backup policies (these are tenant-level)
            "oci_core_volume_default_backup_policy",
            # Some MySQL cluster tables
            "oci_mysql_heat_wave_cluster",
            # Object storage objects (these use different identifiers)
            "oci_objectstorage_object",
            # Tables with schema issues (no compartment_id column)
            "oci_bastion_session",
            "oci_certificates_authority_bundle",
            # Cloud Guard Configuration (tenant-level)
            "oci_cloud_guard_configuration",
        }
        return table in tenant_level_tables

    def run(self):
        data = {}

        # Support multiple regions 
        if not self.regions:
            raise ValueError("OCI regions are required")

        # Normalize regions into a list without mutating attribute type
        regions_value = self.regions
        if isinstance(regions_value, str):
            regions_list = [r for r in regions_value.replace(" ", "").split(",") if r]
        elif isinstance(regions_value, list):
            regions_list = regions_value
        else:
            raise ValueError("OCI regions must be a comma-separated string or a list")

        # Print mode: tenancy-wide or compartment-scoped
        if getattr(self, "compartment_id", None):
            print(f"<info>Mode: compartment (compartment_id={self.compartment_id})</info>")
        else:
            print("<info>Mode: tenancy</info>")
        
        if getattr(self, "compartment_id", None):
                print("<info>About to fetch: oci_identity_compartment (parent compartment)</info>")
                output = self.call_get_data("oci_identity_compartment")
                if output:
                    data.update({"oci_identity_compartment": output})
        # Fetch global tables (skip in compartment mode since they are tenancy-level)
        if not getattr(self, "compartment_id", None):
            for table in self.global_table_list:
                print(f"<info>About to fetch: {table}</info>")
                output = self.call_get_data(table)
                if output:
                    data.update({table: output})

        # Fetch regional tables (iterate through all regions like AWS)
        for table in self.regional_table_list:
            # In compartment mode, skip tenant-level tables that don't support compartment filters
            if getattr(self, "compartment_id", None) and self._is_tenant_level_table(table):
                print(f"<info>Skipping tenant-level table in compartment mode: {table}</info>")
                continue
            data_dict = {}
            for region in regions_list:
                os.environ["OCI_REGION"] = region
                print(f"<info>Fetching regional data: {table} in region {region}</info>")
                
                output = self.call_get_data(table)
                if output:
                    data_dict.update({region: output})
             
            if data_dict:
                data.update({table: data_dict})

        # Generate summary statistics
        total_tables_attempted = len(self.global_table_list) + len(self.regional_table_list)
        total_tables_with_data = len(data)
        
        filename = self.construct_filename("OCI", "json")
        if data:
            self._write_to_file(filename, data, decode=False, jsonify=True)
            print(f"<success> Success! {filename} written to /tmp folder</success>")
            print(f"<success> Data collected from {total_tables_with_data} tables across {len(self.global_table_list)} global and {len(self.regional_table_list)} regional tables in {len(regions_list)} region(s): {', '.join(regions_list)}</success>")
            return {
                "response": f"Success! {filename} written to /tmp folder with data from {total_tables_with_data} tables",
                "status_code": StatusCode.SUCCESS.value,
                "tables_scanned": total_tables_attempted,
                "tables_with_data": total_tables_with_data,
            }

        return {
            "response": "Scan completed but no data available to write to disk",
            "status_code": StatusCode.SUCCESS.value,
            "tables_scanned": total_tables_attempted,
            "tables_with_data": 0,
        }


# Local testing (optional)
if __name__ == "__main__":
    # Set up environment variables for Steampipe OCI plugin
    # These are the correct environment variable names that Steampipe expects
    os.environ["OCI_TENANCY"] = os.environ.get("OCI_TENANCY_ID", "")
    os.environ["OCI_USER"] = os.environ.get("OCI_USER_ID", "")
    os.environ["OCI_FINGERPRINT"] = os.environ.get("OCI_FINGERPRINT", "")
    os.environ["OCI_PRIVATE_KEY"] = os.environ.get("OCI_key_file", "")
    os.environ["OCI_REGION"] = os.environ.get("OCI_REGION", "")

    # Create OCI config file from environment variables
    import os
    from pathlib import Path
    
    # Create the OCI config directory if it doesn't exist
    oci_config_dir = Path.home() / ".oci"
    oci_config_dir.mkdir(exist_ok=True)
    
    # Create the OCI config file
    oci_config_file = oci_config_dir / "config"
    config_content = f"""[DEFAULT]
    user={os.environ.get('OCI_USER_ID', '')}
    fingerprint={os.environ.get('OCI_FINGERPRINT', '')}
    key_file={os.environ.get('OCI_key_file', '')}
    tenancy={os.environ.get('OCI_TENANCY_ID', '')}
    region={os.environ.get('OCI_REGION', '')}
    """
    
    with open(oci_config_file, 'w') as f:
        f.write(config_content)
    
    print(f"OCI config file created at: {oci_config_file}")

    run(
        tenancy_ocid=os.environ.get("OCI_TENANCY_ID", ""),
        user_ocid=os.environ.get("OCI_USER_ID", ""),
        fingerprint=os.environ.get("OCI_FINGERPRINT", ""),
        private_key=os.environ.get("OCI_key_file", ""),
        regions=os.environ.get("OCI_REGION", ""),
        label="TEST",
        compartment_id=os.environ.get("OCI_COMPARTMENT_ID", ""),
    )
