# accuknox-pocs
poc of security tools

1. Create `keys` folder

2. Create a `configs` folder
    - For `cloudsploit` 
        - Add `cloudsploit_config_oracle.json`
        - Add `config.js` from `config-example.js`
        - In `config.js` just replace the `credential_file` path
    
    - For `steampipe`

3. For `steampipe` 
    - Install steampipe and oci Plugin
    - In `.oci` folder create `config` file
    ```shell
        [DEFAULT]
        user=ocid1.user.
        fingerprint=88:2c
        key_file=/key-path/steampipe_key.pem
        tenancy=ocid1.tenancy.
        region=us-ashburn-1
    ```
    - In `.steampipe/config` folder create `oci.spc`
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

4. For `cloudsploit`
    - Clone `cloudsploit` in `cloudsploit/` folder
    - Create another folder named `configs` inside `cloudsploit/<cloned-cloudsploit>/`    
    - cmd to run `node index.js --config /home/ayush/accuknox/accuknox-pocs/configs/cloudsploit/config.js  --json cs-results.json`
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
    