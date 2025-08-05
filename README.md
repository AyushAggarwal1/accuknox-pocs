# accuknox-pocs
poc of security tools

1. Create `keys` folder

2. For `steampipe` 
    - Install steampipe and oci Plugin
    - In `.oci` folder create config
    ```shell
        [DEFAULT]
        user=ocid1.user.
        fingerprint=88:2c
        key_file=/key-path/steampipe_key.pem
        tenancy=ocid1.tenancy.
        region=us-ashburn-1
    ```
    - In `.steampipe/config` folder create 
    ```shell
        connection "oci" {
        plugin = "oci"
        config_file_profile = "DEFAULT"
        #config_file_path = "/home/ayush/.oci/config"

        # The maximum number of attempts (including the initial call) Steampipe will
        # make for failing API calls. Defaults to 9 and must be greater than or equal to 1.
        #max_error_retry_attempts = 9

        # The minimum retry delay in milliseconds after which retries will be performed.
        # This delay is also used as a base value when calculating the exponential backoff retry times.
        # Defaults to 25ms and must be greater than or equal to 1ms.
        #min_error_retry_delay = 25
        }
    ```

3. For `cloudsploit`
    - Clone `cloudsploit` in `cloudsploit/` folder
    - Create another folder named `configs` inside `cloudsploit/<cloned-cloudsploit>/`
    - Then copy `config_example.js` to `configs/config.js`
    - Then create `cloudsploit_config_oracle.json` for `oracle` and just give path in `config.js`
    - cmd to run `node index.js --config ./configs/config.js --json results.json`
    ```shell
        {
            "tenancyId": "ocid1.tenancy.oc1..",
            "compartmentId": "ocid1.compartment.oc1..",
            "userId": "ocid1.user.oc1..",
            "keyFingerprint": "88:2c:",
            "region": "us-ashburn-1",
            "keyValue": "-----BEGIN PRIVATE KEY----------END PRIVATE KEY-----"
        }

    ```
**Oracle Cloud**

