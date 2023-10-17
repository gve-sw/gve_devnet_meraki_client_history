# gve_devnet_meraki_client_history
This program is designed to interact with the Meraki Dashboard API to obtain, analyze, and manage data associated with client history, devices, and networks within an organization’s infrastructure.


## Contacts
* Mark Orszycki


## Solution Components
* Meraki Dashboard API


## Prerequisites
### Meraki API Keys
Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access`
3. Click on `Enable access to the Cisco Meraki Dashboard API`
4. Go to `My Profile > API access`
5. Under API access, click on `Generate API key`
6. Save the API key in a safe place.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization). 

> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

### Environment Variables Setup
For ease of configuration and better security, this application uses a `.env` file. Create a `.env` file in the root directory of your project and add the following entries:
```env
MERAKI_API_KEY=your_meraki_api_key
EXCEL=True
TIMESPAN_IN_SECONDS=desired_timespan_for_reports
LOGGER_LEVEL=CRITICAL
```
* Note, if no value is set for timespan in .env, it will default to 1 day. 
* Optionally, set LOGGER_LEVEL: Warning, Info, Critical, Debug, etc.

## Installation/Configuration
### With Docker
1. Clone this repository with `git clone https://wwwin-github.cisco.com/gve/gve_devnet_meraki_client_history.git`.
2. Set up your `.env` file as per the instructions above.

**Note:** If you haven't installed Docker or Docker Compose, you will need to do so. Follow the instructions on the [Docker website](https://docs.docker.com/get-docker/) to get started.

### Optional: Running Locally Without Docker
1. Clone this repository with `git clone https://wwwin-github.cisco.com/gve/gve_devnet_meraki_client_history.git`.
2. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](URL_to_download_Python). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](URL_to_virtual_environment_instructions).
3. Set up your `.env` file as per the instructions above.
4. Install the requirements with `pip3 install -r requirements.txt`.

### Flags

- `-o, --option` (Required): Specify the product type. Available options:
    - `all`: For all products.
    - `wired`: For wired products.
    - `wireless`: For wireless products.

- `--raw`: (Optional) If present, export all raw data.

## Usage
### Running with Docker (Containerized)
Once installation and configuration is complete, run the application using Docker Compose as follows:
```shell
docker-compose run meraki_client_history [flags]
```
Replace `[flags]` with any of the flags described below.

#### Examples of running the containerized app with different flags:
1. To generate a filtered report for wired clients:
```shell
docker-compose run meraki_client_history -o wired
```
2. To generate a filtered report for wireless clients:
```shell
docker-compose run meraki_client_history -o wireless
``` 
3. To generate a filtered report for wired and wireless clients:
```shell
docker-compose run meraki_client_history -o all 
```
4. To generate a filtered report for wired and wireless clients with unfiltered API response data:
```shell
docker-compose run meraki_client_history -o all --raw
```


### Running Locally
Once installation and configuration is complete, if you chose to use your local installation of python (instead of container), run the application using:

```shell
python app.py -o [flags]
```

1. To generate a filtered report for wired and wireless clients:
```shell
python app.py -o all
```
2. To generate a report specifically for wireless clients with filtered data:
```shell
python app.py -o wireless
```
3. To generate a report specifically for wired clients with filtered data:
```shell
python app.py -o wired
```
4. To generate a report with raw data from API call, use the "--raw" flag.
```shell
python app.py -o wireless --raw
```

Note: If the user has access to multiple Meraki organizations, a list of available orgs will be displayed, and the user prompted enter

# Screenshots
**High-level design:**
![process_flowchart](/IMAGES/process_flowchart.png)<br>

**Console Output:**
![console](/IMAGES/console.png)<br>

**Console Report Filtered:**
![console_report_filtered](/IMAGES/console_report_filtered.png)<br>

**Console Report Unfiltered:**
![console_report_unfiltered](/IMAGES/console_report_unfiltered.png)<br>

**Excel Report Filtered:**
![filtered_excel_report](/IMAGES/excel_report_filtered.png)<br>

**Excel Report Unfiltered:**
![unfiltered_excel_report](/IMAGES/excel_report_unfiltered.png)<br><br>

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
