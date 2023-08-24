import logging
import rich.logging
import json
import pandas as pd
import time
import os
from rich import print as rprint
from rich.table import Table
from datetime import datetime
import meraki

# Constants for controlling behavior of the script
BURST_REQUESTS = 10  # Initial burst of 10 requests allowed in the first second
RATE_LIMIT_PAUSE = 1  # One request per second after the initial burst
MAX_RETRIES = 3  # Maximum number of retries in case of failures
TIMESPAN_IN_SECONDS = 86400  # Used for filtering client data over a day
EXCEL_REPORT_1 = False  # Flag
EXCEL_REPORT_2 = True


def get_env_variables():
    API_KEY = os.getenv('MERAKI_API_KEY')
    ORGANIZATION_NAME = os.getenv('MERAKI_ORG_NAME')

    if not API_KEY or not ORGANIZATION_NAME:
        return None, None

    return API_KEY, ORGANIZATION_NAME


def setup():
    # Configure logging format for the rich handler
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Set up the rich logging handler for console output
    console_handler = rich.logging.RichHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    # Set up the standard logging handler for file output
    file_handler = logging.FileHandler("app.log", mode='a')
    file_handler.setFormatter(logging.Formatter(log_format))

    # Configure the logger based on the module's name for better granularity
    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler])
    logger = logging.getLogger(__name__)

    return logger


def close_logger(logger):
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def rate_limit_request(current_request_count):
    """Pauses execution to maintain request rate limits."""
    if current_request_count > BURST_REQUESTS:
        # We've exhausted the burst allowance, so we'll pause between subsequent requests
        time.sleep(RATE_LIMIT_PAUSE)


def handle_api_error(error, serial, logger, RATE_LIMIT_PAUSE, retries):
    if error.status == 429:  # Rate Limit error
        logger.warning(f"Rate limit hit. Retrying in {RATE_LIMIT_PAUSE} seconds.")
        time.sleep(RATE_LIMIT_PAUSE)
        retries += 1
    else:
        logger.error(f"Failed to get clients for device with serial {serial}. Error: {error}")
    return retries


def get_org_id_by_name(dashboard, organization_name, logger):
    """
    Fetch the organization ID based on its name. Exit the script if not found.
    """
    try:
        orgs = dashboard.organizations.getOrganizations()
        for org in orgs:
            if org['name'] == organization_name:
                return org['id']
    except Exception as e:
        logger.error(f"Failed to fetch organizations. Error: {e}")
        close_logger(logger)
        exit(1)

    logger.error(f"Organization with name '{organization_name}' not found.")
    close_logger(logger)
    exit(1)


def get_networks_in_org(dashboard, org_id, net_name, logger):
    net_response = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')
    for net in net_response:
        if net['name'] == net_name:
            return net['id']
    return None


def log_org_data(logger, response):
    """Logs the provided data as a table using Rich and logs raw data to app.log"""

    table = Table(show_header=True, header_style="bold magenta")
    columns = ["name", "lat", "lng", "address", "notes", "tags", "networkId",
               "serial", "model", "mac", "lanIp", "firmware", "productType"]

    for col in columns:
        table.add_column(col.capitalize())

    # Improved data extraction with `get()` to handle missing keys gracefully
    for item in response:
        table.add_row(
            item.get("name", ""),
            str(item.get("lat", "")),
            str(item.get("lng", "")),
            item.get("address", ""),
            item.get("notes", ""),
            ", ".join(item.get("tags", [])),
            item.get("networkId", ""),
            item.get("serial", ""),
            item.get("model", ""),
            item.get("mac", ""),
            item.get("lanIp", ""),
            item.get("firmware", ""),
            item.get("productType", "")
        )

    rprint(table)
    logger.info(json.dumps(response))


def log_clients_data(logger, response):
    """Logs the provided device clients data as a table using Rich and logs raw data to app.log"""

    table = Table(show_header=True, header_style="bold magenta")
    columns = ["id", "description", "mac", "ip", "user", "vlan", "switchport"]

    for col in columns:
        table.add_column(col.capitalize())

    # Improved data extraction with `get()` to handle missing keys gracefully
    for item in response:
        table.add_row(
            str(item.get("id", "")),
            str(item.get("description", "")),
            str(item.get("mac", "")),
            str(item.get("ip", "")),
            str(item.get("user", "")),
            str(item.get("vlan", "")),
            str(item.get("switchport", "None"))
        )

    rprint(table)
    logger.info(json.dumps(response))


def fetch_and_log_client_data(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan):
    all_clients_data = []
    request_count = 0

    # Allowed product types
    allowed_product_types = ["appliance", "switch", "wireless", "cellularGateway"]

    # Get all devices in organization
    org_devices_response = dashboard.organizations.getOrganizationDevices(org_id, total_pages='all')
    log_org_data(logger, org_devices_response)

    # Loop through devices to get client information
    for device in org_devices_response:
        serial = device['serial']
        device_product_type = device["productType"]

        # Check if the device has the allowed product types
        if device_product_type not in allowed_product_types:
            logger.info(f"Skipping device {serial} due to its product type not being in the allowed list.")
            continue
        device_data = {
            "device_info": device,
            "clients": []
        }

        retries = 0
        success = False
        while not success and retries < max_retries:
            try:
                response = dashboard.devices.getDeviceClients(serial, timespan=timespan)
                for client in response:
                    client["device_name"] = device.get("name", device.get("serial"))  # Adding device name to each client
                log_clients_data(logger, response)
                device_data["clients"].extend(response)
                success = True
                request_count += 1
                rate_limit_request(request_count)
            except meraki.APIError as e:
                retries = handle_api_error(e, serial, logger, rate_limit_pause, retries)
                if not success:
                    break
        all_clients_data.append(device_data)
    return all_clients_data


def fetch_and_log_network_data(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan):
    all_network_data = []
    request_count = 0

    # Allowed product types
    allowed_product_types = ["appliance", "switch", "wireless", "cellularGateway"]

    # Get all networks in the organization
    org_networks_response = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')

    for network in org_networks_response:
        network_id = network['id']
        network_product_types = network["productTypes"]

        # Check if the network has none of the allowed product types
        if not any(product in network_product_types for product in allowed_product_types):
            logger.info(f"Skipping network {network_id} due to not having any of the allowed product types.")
            continue

        network_data = {
            "network_info": network,
            "clients": []
        }

        retries = 0
        success = False
        while not success and retries < max_retries:
            try:
                response = dashboard.networks.getNetworkClients(network_id, total_pages='all', timespan=timespan)
                log_clients_data(logger, response)
                network_data["clients"].extend(response)
                success = True
                request_count += 1
                rate_limit_request(request_count)
            except meraki.APIError as e:
                retries = handle_api_error(e, network_id, logger, rate_limit_pause, retries)  # Fixing the TypeError by adding 'retries' argument
                if retries >= max_retries:
                    # if we hit the maximum number of retries, log the error and move to the next network
                    logger.error(f"Max retries reached for network_id {network_id}. Moving to the next network.")
                    break

        all_network_data.append(network_data)
    return all_network_data


def export_org_to_excel(data):
    """Exports the given data to an Excel file using pandas."""
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"MAC Report 1 - All Devices in Organization_{current_time}.xlsx"

    # Flatten client data and concatenate together
    all_client_data = []
    for device_data in data:
        all_client_data.extend(device_data["clients"])
    all_clients_df = pd.DataFrame(all_client_data)

    # Reorder columns to make sure "device_name" is the first column
    cols = list(all_clients_df.columns)
    cols.insert(0, cols.pop(cols.index('device_name')))
    all_clients_df = all_clients_df[cols]

    with pd.ExcelWriter(filename) as writer:
        all_clients_df.to_excel(writer, sheet_name="All Clients", index=False)

    print(f"Data exported to {filename} successfully!")


def export_networks_to_excel(data):
    """Exports network-based data to an Excel file using pandas."""
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"MAC Report 2 - Devices by Network_{current_time}.xlsx"

    # Check if there's any network with client data
    has_data = any(network_data["clients"] for network_data in data)

    if not has_data:
        print("No data available to export to Excel. Exiting...")
        return

    # Create an Excel writer
    with pd.ExcelWriter(filename) as writer:
        for network_data in data:
            network_info = network_data["network_info"]
            clients = network_data["clients"]

            # Check if there are clients for this network, if not, skip creating a sheet for it.
            if not clients:
                continue

            # Create sheet name based on the network name
            sheet_name = network_info.get("name", "Unknown")
            if len(sheet_name) > 30:  # Excel sheet names have a max length of 31 characters
                sheet_name = sheet_name[:30]

            clients_df = pd.DataFrame(clients)
            clients_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Data exported to {filename} successfully!")


def run_report_1(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan, report):
    if report:
        rprint("[green]Generating Report 1...[/green]")
        all_clients_data = fetch_and_log_client_data(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan)
        export_org_to_excel(all_clients_data)
        logger.info("Excel report (Report 1) generated!")
        return True
    return False


def run_report_2(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan, report):
    if report:
        rprint("[green]Generating Report 2...[/green]")
        all_network_data = fetch_and_log_network_data(dashboard, org_id, logger, rate_limit_pause, max_retries, timespan)
        export_networks_to_excel(all_network_data)
        logger.info("Excel report (Report 2) generated!")
        return True
    return False

