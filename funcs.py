import json
import logging
import os
from datetime import datetime
import meraki
import pandas as pd
import rich.logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
from meraki.exceptions import APIError
import sys
from rich.prompt import Prompt
from rich.progress import track
import argparse

# Load environment variables from .env file
load_dotenv()


class EnvironmentManager:
    MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
    EXCEL = os.getenv('EXCEL', "False").lower() == "true"  # Default to false if left blank
    LOGGER_LEVEL = os.getenv('LOGGER_LEVEL', "CRITICAL").upper()
    try:
        TIMESPAN_IN_SECONDS = int(os.getenv('TIMESPAN_IN_SECONDS', '86400'))
    except ValueError:
        TIMESPAN_IN_SECONDS = 86400  # Default to 86400 seconds (1 day) if left blank or if value is invalid

    @classmethod
    def validate_env_variables(cls):
        missing_vars = []
        console = Console()  # Instantiate a console object for rich

        table = Table()
        table.add_column("Variable", justify="left", style="bright_white", width=30)
        table.add_column("Value", style="bright_white", width=50)

        for var_name, var_value in cls.__dict__.items():
            if "os" in var_name or "__" in var_name or isinstance(var_value, classmethod):  # ignore class documentation & methods
                continue
            if var_name == 'MERAKI_API_KEY' and var_value is not None:
                table.add_row(var_name, "OK")
            else:
                table.add_row(var_name, str(var_value) if var_value is not None else "Not Set")
            if var_value in ("", None) and var_name not in ["TIMESPAN_IN_SECONDS"]:
                missing_vars.append(var_name)

        # Display the table
        console.print(Panel.fit(table, title="Step 1: Retrieve and Validate Environment Variables"))

        if missing_vars:
            raise EnvironmentError(f"The following environment variables have not been set: {', '.join(missing_vars)}")

        # Check TIMESPAN_IN_SECONDS separately since we always have a default
        if not (1 <= cls.TIMESPAN_IN_SECONDS <= 2678400):  # 2678400 = 31 days in seconds
            raise ValueError(f"TIMESPAN_IN_SECONDS value ({cls.TIMESPAN_IN_SECONDS}) out of range. Please correct timespan in .env file.")


class LoggerManager:
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

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

        # Get logging level from environment variable
        log_level_str = EnvironmentManager.LOGGER_LEVEL  # Ensuring to get the level from the EnvironmentManager
        log_level = self.LOG_LEVELS.get(log_level_str, logging.CRITICAL)  # Default to WARNING if invalid level
        # Configure the logger based on the module's name for better granularity
        logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])

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


class InvalidArgumentsError(Exception):
    """
    For defining custom exceptions
    """
    pass


class ArgumentParserManager:

    @staticmethod
    def parse_arguments(logger_manager):
        parser = argparse.ArgumentParser(description="Generate reports for specific product types.")
        parser.add_argument('-o', '--option',
                            type=str,
                            choices=['all', 'wired', 'wireless'],
                            default='all',
                            help='Specify the product type (default: %(default)s).')
        parser.add_argument('--raw',
                            action='store_true',
                            help='If present, export all raw data.')

        args = parser.parse_args()
        product_type = args.option.lower()
        raw_data = args.raw

        valid_options = ["wired", "wireless", "all"]
        if product_type not in valid_options:
            error_message = f"Invalid product type: {product_type}. Valid options are: {', '.join(valid_options)}"
            logger_manager.console.print(error_message)
            raise InvalidArgumentsError(error_message)

        return product_type, raw_data

def get_oui_from_mac(mac_address):
    """
    Get the Organizationally Unique Identifier (OUI) from a MAC address.
    """
    return mac_address[:8]  # Slice to get the first 8 characters (OUI)


def get_org_id(dashboard, logger_manager):
    """
    Fetch the org ID based on org name, or prompt the user to select
    an organization if the name is left blank or is invalid. If there is only one
    organization, it selects that organization automatically. Exits the script if
    the organization is not found or if there's an error fetching the organizations.
    """
    console = Console()

    with console.status("[bold green]Fetching Meraki Organizations....", spinner="dots"):
        try:
            orgs = dashboard.organizations.getOrganizations()
        except APIError as e:
            logger_manager.logger.error(f"Failed to fetch organizations. Error: {e.message['errors'][0]}")
            sys.exit(1)

    console.print("[bold bright_green]Connected to Meraki dashboard!")
    print(f"Found {len(orgs)} organization(s).")

    # If one org, return early
    if len(orgs) == 1:
        print(f"Working with Org: {orgs[0]['name']}\n")
        return orgs[0]["id"]
    org_names = [org["name"] for org in orgs]
    print("Available organizations:")
    for org in orgs:
        console.print(f"- {org['name']}")
    console.print("[bold red]\nNote: Meraki organization names are case sensitive")
    selection = Prompt.ask(
        "Which organization should we use?", choices=org_names, show_choices=False
    )
    organization_name = selection  # Update organization_name with the user's selection

    for org in orgs:
        if org["name"] == organization_name:
            return org["id"]

    logger_manager.logger.error(f"Organization with name '{organization_name}' not found.")
    exit(1)


def get_networks_in_org(dashboard, org_id, product_type=None):
    console = Console()
    """
    Collect existing Meraki network names / IDs
    """
    console.print(Panel.fit("[bold bright_green]Retrieving Network(s) Information[/bold bright_green]", title="Step 3"))
    # Fetching the networks before applying any filter.
    try:
        response = dashboard.organizations.getOrganizationNetworks(organizationId=org_id)
    except Exception as e:  # Handle exception for API call
        console.print(f"[bold red]Failed to retrieve networks: {str(e)}[/bold red]")
        sys.exit(1)

    if product_type:
        # Filter networks by product type
        response = [network for network in response if product_type in network['productTypes']]

    print(f"Found {len(response)} networks.")
    return response


def get_clients_for_network(dashboard, network, product_type, logger_manager, timespan, raw_data=False):
    network_data = {
        "network_info": network,
        "clients": []
    }
    try:
        clients = dashboard.networks.getNetworkClients(network['id'], total_pages='all', timespan=timespan)

        if raw_data:  # if all_data is True, include all the data without filtering
            network_data["clients"].extend(clients)
            return network_data

        if product_type == "wireless":
            clients = [client for client in clients if 'ssid' in client and client['ssid'] is not None]
        elif product_type == "wired":
            clients = [client for client in clients if 'ssid' not in client or client['ssid'] is None]

        if clients:
            network_data["clients"].extend(clients)
            return network_data
        else:
            return None
    except meraki.APIError as e:
        logger_manager.logger.error(f"Failed to get clients for network with network id: {network['id']}. Error: {e}")
        return None


def get_network_client_data(dashboard, org_id, product_type, logger_manager, timespan, raw_data=False):
    console = Console()
    all_network_data = []
    networks = get_networks_in_org(dashboard, org_id)

    for network in track(networks, description="Fetching Network Client History..."):
        network_data = get_clients_for_network(dashboard, network, product_type, logger_manager, timespan)
        if network_data:
            all_network_data.append(network_data)

    console.print("[bold bright_green]Network retrieval done!\r\n")
    return all_network_data


def export_data_to_excel(data, output_dir="/app/reports", raw_data=False):
    console = Console()
    console.print(Panel.fit("[bold bright_green]Export Data to Excel[/bold bright_green]", title="Step 4"))

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Client_History_Report_{current_time}.xlsx"

    # Ensure output directory exists or create it
    os.makedirs(output_dir, exist_ok=True)

    # Combine the desired directory with the filename
    full_filepath = os.path.join(output_dir, filename)
    has_data = any(network_data["clients"] for network_data in data)

    if not has_data:
        console.print("No data available to export to Excel. Exiting...")
        return

    with pd.ExcelWriter(full_filepath) as writer:
        summary_data = []

        # Write data to Excel, network by network
        for network_data in track(data, description="[cyan]Creating Excel File..."):
            network_info = network_data["network_info"]
            clients = network_data["clients"]

            if not clients:
                continue

            relevant_client_data = []
            for client in clients:
                if raw_data:
                    client_info = {
                        "Network Name": network_info.get("name", "Unknown"),
                        **client  # Include all original client data
                    }
                else:
                    client_info = {
                        "Network Name": network_info.get("name", "Unknown"),
                        "IP Address": client.get("ip"),
                        "MAC Address": client.get("mac"),
                        "OUI": get_oui_from_mac(client.get("mac", "")),
                        "Manufacturer": client.get("manufacturer"),
                        "Description": client.get("description"),
                        "SSID": client.get("ssid"),
                        "OS": client.get("os"),
                        "First Seen": datetime.strptime(client.get("firstSeen"), "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d %H:%M:%S') if client.get("firstSeen") else None,
                        "Last Seen": datetime.strptime(client.get("lastSeen"), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S') if client.get("lastSeen") else None,
                        "Status": client.get("status"),
                        "Sent Data": client.get("usage", {}).get("sent"),
                        "Received Data": client.get("usage", {}).get("recv"),
                        "User": client.get("user"),
                        "Meraki Device Serial (Connected to)": client.get("recentDeviceSerial", "Unknown")
                    }

                relevant_client_data.append(client_info)
                summary_data.append(client_info)

            sheet_name = network_info.get("name", "Unknown")
            if len(sheet_name) > 30:
                sheet_name = sheet_name[:30]

            df = pd.DataFrame(relevant_client_data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Write summary data
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        console.print(f"Data exported successfully to {filename}.")
        console.print("\n")


def print_final_table(all_network_data, raw_data=False):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    if raw_data:
        columns = ["id", "mac", "ip", "ip6", "description", "firstSeen", "lastSeen", "manufacturer",
                   "os", "user", "vlan", "ssid", "switchport", "wirelessCapabilities", "smInstalled",
                   "recentDeviceMac", "status", "usage", "namedVlan", "adaptivePolicyGroup",
                   "deviceTypePrediction", "recentDeviceSerial", "recentDeviceName", "recentDeviceConnection",
                   "notes", "ip6Local", "groupPolicy8021x", "pskGroup"]
    else:
        columns = ["IP", "MAC", "OUI", "Manufacturer", "Description", "SSID", "OS", "First Seen", "Last Seen",
                   "Status", "Sent Data", "Received Data", "User", "Meraki Device Serial (Connected to)"]

    # Add columns to the table
    for col in columns:
        table.add_column(col)

    # Add data to the table
    for network_data in all_network_data:
        for client in network_data["clients"]:
            if raw_data:
                row_data = [str(client.get(col, "")) for col in columns]
            else:
                row_data = [
                        client.get("ip", ""),
                        client.get("mac", ""),
                        get_oui_from_mac(client.get("mac", "")),
                        client.get("manufacturer", ""),
                        client.get("description", ""),
                        client.get("ssid", ""),
                        client.get("os", ""),
                        client.get("firstSeen", ""),
                        client.get("lastSeen", ""),
                        client.get("status", ""),
                        str(client.get("usage", {}).get("sent", "")),
                        str(client.get("usage", {}).get("recv", "")),
                        client.get("user", ""),
                        client.get("recentDeviceSerial", "Unknown")
                ]
            table.add_row(*row_data)

    console.print(Panel.fit(table, title="Final Report"))


def run_report(dashboard, org_id, product_type, logger_manager, timespan, excel, raw_data=False):
    all_network_data = get_network_client_data(dashboard, org_id, product_type, logger_manager, timespan, raw_data)
    if excel:
        export_data_to_excel(all_network_data, "/app/reports", raw_data)
        logger_manager.logger.info("Excel report generated!")
    print_final_table(all_network_data, raw_data)
    return True


if __name__ == "__main__":
    # Insert Testing/debugging code here
    pass