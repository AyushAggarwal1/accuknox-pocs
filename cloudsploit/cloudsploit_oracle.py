#!/usr/bin/env python3
"""
This module runs an open source tool called Cloudsploit against an Oracle Cloud account and writes the result to a JSON file.
"""
import os
import time

from base_module import BaseModule
from cloudsploit_base import CloudsploitSetUpMixin


def run(
    tenancy_ocid=None,
    user_ocid=None,
    fingerprint=None,
    private_key_path=None,
    region=None,
    label=None,
    compliance=None,
):
    kwargs = dict(
        tenancy_ocid=tenancy_ocid,
        user_ocid=user_ocid,
        fingerprint=fingerprint,
        private_key_path=private_key_path,
        region=region,
        label=label,
        compliance=compliance,
    )
    return CloudsploitOracle(kwargs).main()


class CloudsploitOracle(BaseModule, CloudsploitSetUpMixin):
    _module_name = "cloudsploit_oracle"

    _fields = [
        "tenancy_ocid",
        "user_ocid",
        "fingerprint",
        "private_key_path",
        "region",
        "label",
    ]

    def run(self):
        """
        This function collects Cloudsploit data from an Oracle Cloud account.
        Parameters:
        tenancy_ocid: Oracle Cloud tenancy OCID
        user_ocid: Oracle Cloud user OCID
        fingerprint: Key fingerprint for the user's API key
        private_key_path: Path to the private key used for authentication
        region: Oracle Cloud region
        label: Optional label for the scan
        compliance: Optional compliance types (e.g. cis, pci, hipaa)
        """

        print("Setting Oracle Cloud env vars")
        os.environ["OCI_TENANCY_OCID"] = self.tenancy_ocid
        os.environ["OCI_USER_OCID"] = self.user_ocid
        os.environ["OCI_FINGERPRINT"] = self.fingerprint
        os.environ["OCI_PRIVATE_KEY_PATH"] = self.private_key_path
        os.environ["OCI_REGION"] = self.region or "us-ashburn-1"

        filename = self.construct_filename("CS_ORACLE", "json")
        return self.execute_cloud_sploit_query(
            f"{time.time()}.json",
            filename,
        )


if __name__ == "__main__":
    run(
        tenancy_ocid="ocid1.compartment.oc1..",
        user_ocid="ocid1.user.oc1..",
        fingerprint="88:",
        private_key_path="-----BEGIN PRIVATE KEY---------END PRIVATE KEY-----",
        region="us-ashburn-1",
        label="Test",
        compliance=os.environ.get("compliance"),
    )