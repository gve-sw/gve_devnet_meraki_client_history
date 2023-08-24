# gve_devnet_meraki_client_history
This program is designed to interact with the Meraki Dashboard API to fetch, log, and export data about client history devices and networks within an organization.


## Contacts
* Mark Orszycki

## Solution Components
* Meraki Dashboard API

## Prerequisites
#### Meraki API Keys
In order to use the Meraki API, you need to enable the API for your organization first. After enabling API access, you can generate an API key. Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access`
3. Click on `Enable access to the Cisco Meraki Dashboard API`
4. Go to `My Profile > API access`
5. Under API access, click on `Generate API key`
6. Save the API key in a safe place. The API key will only be shown once for security purposes, so it is very important to take note of the key then. In case you lose the key, then you have to revoke the key and a generate a new key. Moreover, there is a limit of only two API keys per profile.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization). 

> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

#### Meraki Organization Name
To utilize the program, you need to acquire your Meraki Org name:
1. Login to the Meraki dashboard.
2. Navigate to Organization > Settings.
3. Copy and save the Organization Name.


## Installation/Configuration
1. Clone this repository with `git clone gve_devnet_meraki_client_history`
2. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
3. Add Meraki API key & Organizaiton Name to environment variables:
```bash
export MERAKI_API_KEY='YOUR_MERAKI_API_KEY'
export MERAKI_ORG_NAME='YOUR_MERAKI_ORG_NAME'
```
4. Install the requirements with `pip3 install -r requirements.txt`

### Flags
In the helper_functions.py, configure which Excel reports to generate. If both flags are set to false, output will only be seen in app.log:

* To generate a Excel report with client history for all devices in the organization in a singluar worksheet:
    * Set EXCEL_REPORT_1 = True
* To generate an Excel report with client history where each network is a worksheet:
    * Set EXCEL_REPORT_2 = True


## Usage
To run the program, use the command:
```
$ python3 app.py
```


### Rate Limiting
The program includes a rate-limiting mechanism to prevent excessive API calls in a short span, ensuring adherence to Meraki's API rate limits. Rate limiting prevents potential bans or timeouts from the API. Adjust the RATE_LIMIT_PAUSE and MAX_RETRIES parameters as per your requirements and Meraki's guidelines.


# Screenshots

![/IMAGES/0image.png](/IMAGES/0image.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.