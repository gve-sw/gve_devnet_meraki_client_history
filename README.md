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
4. Alternatively go to: https://api.meraki.com/api/v0/organizations after logging in.

#### Environment Variables Setup
For ease of configuration and better security, this application uses a `.env` file.
```env
MERAKI_API_KEY=your_meraki_api_key
MERAKI_ORG_NAME=your_meraki_org_name
REPORT_ORG_WIDE=True
REPORT_BY_NETWORK=True
EXCEL=True
TIMESPAN_IN_SECONDS=desired_timespan_for_reports

```
 1. Update MERAKI_API_KEY with your Meraki API key
      * Note that if your org name contains spaces, use single quotes. i.e. MERAKI_ORG_NAME='My Org'
   2. Update MERAKI_ORG_NAME with your meraki Organization name
   3. Set the flags in `.env` based on desired program output:
      * Set `REPORT_ORG_WIDE` to True in the `.env` file to generate an Excel report with all devices in organization in one sheet.
      * Set `REPORT_BY_NETWORK` to True in the `.env` file to generate an Excel report where each Worksheet is a network in the organization. 
      * If you'd like to export the report to Excel, set the `EXCEL` flag in the `.env` file, otherwise the program will only output to console.
      * Set the desired timespan for the report in seconds. If not timespan is set, it will default to 86400 (1 day). Max is 31 days.

## Installation/Configuration

1. Clone this repository with `git clone https://wwwin-github.cisco.com/gve/gve_devnet_meraki_client_history.git`
2. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
3. Set up your `.env` file (see Environment Variables Setup above).
4. Install the requirements with `pip3 install -r requirements.txt`

## Usage
To run the program, use the command:
```
$ python3 app.py
```

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
