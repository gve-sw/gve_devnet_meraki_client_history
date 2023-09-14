import json
import logging
import os
from datetime import datetime
import meraki
import pandas as pd
import rich.logging
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class EnvironmentManager:
    """
    The EnvironmentManager class is responsible for loading and validating the necessary environment variables
    that the Meraki program relies on.

    Attributes:
        MERAKI_API_KEY (str): API key for accessing Meraki.
        MERAKI_ORG_NAME (str): Organization NAME for the Meraki API.
        REPORT_ORG_WIDE (bool): Flag to output client history by organization.
        REPORT_BY_NETWORK (bool): Flag to output client history by network.
        EXCEL (bool): Flag to create Excel report output.
        TIMESPAN_IN_SECONDS (int): Used for filtering client data over a day.

    Methods:
        validate_env_variables() - Validates that all required environment variables are set.
    """

    MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
    MERAKI_ORG_NAME = os.getenv('MERAKI_ORG_NAME')
    REPORT_ORG_WIDE = os.getenv('REPORT_ORG_WIDE', "False").lower() == "true"  # Default to false if left blank
    REPORT_BY_NETWORK = os.getenv('REPORT_BY_NETWORK', "False").lower() == "true"  # Default to false if left blank
    EXCEL = os.getenv('EXCEL', "False").lower() == "true"  # Default to false if left blank
    try:
        TIMESPAN_IN_SECONDS = int(os.getenv('TIMESPAN_IN_SECONDS', '86400'))
    except ValueError:
        TIMESPAN_IN_SECONDS = 86400  # Default to 86400 seconds (1 day) if left blank or if value is invalid

    @classmethod
    def validate_env_variables(cls):
        missing_vars = []
        console = Console()  # Instantiate a console object for rich

        table = Table(title="Environment Variables")
        table.add_column("Variable", justify="left", style="bright_white", width=30)
        table.add_column("Value", style="bright_white", width=50)

        for var_name, var_value in cls.__dict__.items():
            if "os" in var_name or "__" in var_name or isinstance(var_value, classmethod):  # ignore class documentation & methods
                continue
            table.add_row(var_name, str(var_value) if var_value is not None else "Not Set")
            if var_value in ("", None) and var_name != "TIMESPAN_IN_SECONDS":  # Exclude TIMESPAN_IN_SECONDS from this check
                missing_vars.append(var_name)

        # Display the table
        console.print(table)

        if missing_vars:
            raise EnvironmentError(f"The following environment variables have not been set: {', '.join(missing_vars)}")

        # Check TIMESPAN_IN_SECONDS separately since we always have a default
        if not (1 <= cls.TIMESPAN_IN_SECONDS <= 2678400):  # 2678400 = 31 days in seconds
            raise ValueError(f"TIMESPAN_IN_SECONDS value ({cls.TIMESPAN_IN_SECONDS}) out of range. Please correct timespan in .env file.")


class LoggerManager:
    def __init__(self):
        self.logger = self.setup()
        self.original_log_level = self.logger.level
        self.console = Console()

    def setup(self):
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
        return logging.getLogger(__name__)

    def suppress_logging(self):
        self.logger.setLevel(logging.CRITICAL + 1)

    def restore_logging(self):
        self.logger.setLevel(self.original_log_level)

    def log_org_wide_report_data(self, response):
        """Logs the provided data as a table using Rich and logs raw data to app.log"""
        # For cleaner logs
        self.suppress_logging()

        table = Table(show_header=True, header_style="bold magenta")
        columns = ["name", "lat", "lng", "address", "notes", "tags", "networkId",
                   "serial", "model", "mac", "lanIp", "firmware", "productType"]

        for col in columns:
            table.add_column(col.capitalize())

        # Data extraction with `get()` to handle missing keys gracefully
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

        self.console.print(table)
        self.logger.info(json.dumps(response))
        self.restore_logging()

    def log_network_report_data(self, response):
        """Logs the provided device clients data as a table using Rich and logs raw data to app.log"""
        self.suppress_logging()

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

        self.console.print(table)
        self.logger.info(json.dumps(response))
        self.restore_logging()


def get_org_id_by_name(dashboard, organization_name, logger_manager):
    """
    Fetch the organization ID based on its name. Exit the script if not found.
    """

    try:
        orgs = dashboard.organizations.getOrganizations()
        for org in orgs:
            if org['name'] == organization_name:
                return org['id']
    except Exception as e:
        logger_manager.logger.error(f"Failed to fetch organizations. Error: {e}")
        exit(1)

    logger_manager.logger.error(f"Organization with name '{organization_name}' not found.")
    exit(1)


def get_networks_in_org(dashboard, org_id, net_name):
    net_response = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')
    for net in net_response:
        if net['name'] == net_name:
            return net['id']
    return None


def fetch_meraki_client_data(dashboard, org_id, logger_manager, timespan):
    all_clients_data = []

    # Allowed product types. API call will fail on MV & MT
    allowed_product_types = ["appliance", "switch", "wireless", "cellularGateway"]

    # Get all devices in organization
    org_devices_response = dashboard.organizations.getOrganizationDevices(org_id, total_pages='all')
    logger_manager.log_org_wide_report_data(org_devices_response)

    # Loop through devices to get client information
    for device in org_devices_response:
        serial = device['serial']
        device_product_type = device["productType"]

        # Check if the device has the allowed product types
        if device_product_type not in allowed_product_types:
            logger_manager.logger.info(f"Skipping device {serial} due to its product type not being in the allowed list.")
            continue
        device_data = {
            "device_info": device,
            "clients": []
        }

        try:
            response = dashboard.devices.getDeviceClients(serial, timespan=timespan)
            for client in response:
                client["device_name"] = device.get("name", device.get("serial"))  # Adding device name to each client
            logger_manager.log_network_report_data(response)
            device_data["clients"].extend(response)
        except meraki.APIError as e:
            logger_manager.logger.error(f"Failed to get clients for device with serial {serial}. Error: {e}")

        all_clients_data.append(device_data)
    return all_clients_data


def fetch_meraki_network_data(dashboard, org_id, logger_manager, timespan):
    all_network_data = []

    # Allowed product types
    allowed_product_types = ["appliance", "switch", "wireless", "cellularGateway"]

    # Get all networks in the organization
    org_networks_response = dashboard.organizations.getOrganizationNetworks(org_id, total_pages='all')

    for network in org_networks_response:
        network_id = network['id']
        network_product_types = network["productTypes"]

        # Check if the network has none of the allowed product types
        if not any(product in network_product_types for product in allowed_product_types):
            logger_manager.logger.info(f"Skipping network {network_id} due to not having any of the allowed product types.")
            continue

        network_data = {
            "network_info": network,
            "clients": []
        }
        try:
            response = dashboard.networks.getNetworkClients(network_id, total_pages='all', timespan=timespan)
            logger_manager.log_network_report_data(response)
            network_data["clients"].extend(response)
        except meraki.APIError as e:
            logger_manager.logger.error(f"Failed to get clients for network with network id: {network_id}. Error: {e}")

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


def run_report_1(dashboard, org_id, logger_manager, timespan, report_org_wide, excel):
    if report_org_wide:
        rprint("[green]Generating Report 1...[/green]")
        all_clients_data = fetch_meraki_client_data(dashboard, org_id, logger_manager, timespan)
        if excel:
            export_org_to_excel(all_clients_data)
            logger_manager.logger.info("Excel report (Report 1) generated!")
        return True
    return False


def run_report_2(dashboard, org_id, logger_manger, timespan, report, excel):
    if report:
        rprint("[green]Generating Report 2...[/green]")
        all_network_data = fetch_meraki_network_data(dashboard, org_id, logger_manger, timespan)
        if excel:
            export_networks_to_excel(all_network_data)
            logger_manger.logger.info("Excel report (Report 2) generated!")
        return True
    return False
