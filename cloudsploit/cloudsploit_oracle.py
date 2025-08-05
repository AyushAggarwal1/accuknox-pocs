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
        tenancy_ocid="ocid1.compartment.oc1..aaaaaaaa5vid4ipdainve53mqnuovfvzsfycf52kqnbuhyrvcxrf3mpyeoma",
        user_ocid="ocid1.user.oc1..aaaaaaaabibbphgrf5ow3ybcxp7vxbasgil4ltowrji5etfzaaokw4zvugeq",
        fingerprint="88:2c:a5:2c:fb:ff:23:a2:b6:e9:24:72:17:a2:50:95",
        private_key_path="-----BEGIN PRIVATE KEY-----MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCnxJ5lo1GTaVQ8fAD/JvHYEITNeqK6bFz5TIOTd43J/TcrMpKcslaO129QHPw7quXb7MyjUuHKNbbpu8UkrgpuWTOJ4yhK/eJ9EnOORDrW8vgQaTDFphxcF7sjl1LjfrgUi0gvN2uKAvJvckb0JIHmKYBAFg9SuVZ8XBksCMTNsPEDoGaV4PiD3s8CK7qgUG+FbqZp8tRQe0JcSjBJxYVfo40oNUZtG+9bqMP0oRwssZnnSAx288RXTmDkao2QCJ2uAsVL6CKYkYoX8OgvZ6ldeINNK1LAqxfVNCHsQnvSGzBgkQXUch4JG/mApNvSekoqQc+geQUy4OkBF1rT5fUhAgMBAAECggEADQKSHwMmhxY2tlcOc7r3K8CCL/YX6vmOzzVoCbZOfFDC57ptBLJOxJZ/1xhcVhs3ZpHrP6okgNwgAmmxjNnjTLHlrYZ8YC5mkzjsVabEYllms80Yf2dVkS208TphrusrhspTT3gOgp4eY1abGoE/QpRK0g1z5EAjrRKuUAwhCOtUvTyjRFq+dRoaBPH/uu2ygdHrXm3mWIkgFNgEcRK711Sf1rvMlzPGgfckrUa+72KT8G3DVaLz6vys3oako0ldihpuqB1RZURHAzkKlytvvddOUzbxaFflRFzCeLfdwHvgZ7XaufXUPcEcfpntLNw4IwUc9mKc7GntgMksH37bbQKBgQDmyEolmmqjpkMa+Zi2o96ASAX+cdwgLnIxRsXuusRT7Y8qYhA2pe7zk3abEOtnniVpQBperefFszcYAEl2kVMKsqA7oBt7zZPXqnRYnnWbUkapZ1hiLfL1N/033A/qWhRfbZrXVs4pcth1gvqgi8GVTGEaPSSsrPIW1FYEi+qRtQKBgQC6GZ6WQu0UNYqFP6rE+aP4GrgevWezF0uQTG3WyrlEYcx/UQl0UbqeB1qjeOnqzNs7Sy1wXMv+vqg8U2/THEbxMM4hbNYiKSoI8MbhbyuO6uRFVsF3oSxWIY0ok0Wl3T3QlFnh4p6kyCn9bPOyZxpgdRe6QvMQJpZcRRNliQZpPQKBgC9JEogp33ewdUdtpLCnWsuF9lRwF94wJg2apquHcPqRTigs94166j7WFBMpoFIWwSuTitOjZj3Hvp4YUPUOSamDd/k/kOII+SXTMwuFTCuK7BeBqUZUi9dapXNwj4JA+rOizXsZuhwb/+Xz9E441G02vR6XMJCAzwmGcCl2UZWRAoGALWCJ1sHC5SaY/BymGxlz7c82DejJHFYVyr2YGsOboRznrDOqRn6XLmlEpI+bGfGRk0elcLxv0VHT28HMhoFimvT3jhbnr7Sx1zQ+ikF9MX/84RtiWTUnhmjv7nDajrL/m5hQwk9rt2pHMtAaK+oP+G0UuAoTEmEWULFXJW7f7VECgYB//EEAtThenwP5VpIk2B/TBzi1LItEqDYL4NVu9wrEnkscow9JIFjUgY0pRwTjGNTm7KiuRH6boUyDSctL81LVdwJUFjjtIwK35kWvZs4bxyjUopmTTnp526Z5NL8BAvZ2xGbfZww0lCd8vSytNV4gyI60H4dX2lTlcmQTv0Or3A==-----END PRIVATE KEY-----",
        region="us-ashburn-1",
        label="Test",
        compliance=os.environ.get("compliance"),
    )