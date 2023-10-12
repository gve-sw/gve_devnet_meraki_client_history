"""
Copyright (c) 2023 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
import meraki
from rich.panel import Panel

from funcs import (
    EnvironmentManager,
    LoggerManager,
    ArgumentParserManager,
    InvalidArgumentsError,
    get_org_id,
    run_report,
)

# Instantiate custom logger
logger_manager = LoggerManager()


def main():

    # Title Panel
    logger_manager.console.print(Panel.fit("[bold bright_green]MERAKI WIRELESS CLIENT REPORT[/bold bright_green]"))

    # Argument Parsing
    try:
        product_type, raw_data = ArgumentParserManager.parse_arguments(logger_manager)
    except InvalidArgumentsError as e:
        logger_manager.logger.error(str(e))
        return

    #  Step 1: Retrieve and Validate Environment Variables
    EnvironmentManager.validate_env_variables()

    # Initialize Meraki Dashboard API
    logger_manager.console.print(Panel.fit("[bold bright_green]Connect to Meraki Dashboard[/bold bright_green]", title="Step 2"))
    dashboard = meraki.DashboardAPI(api_key=EnvironmentManager.MERAKI_API_KEY, suppress_logging=True)

    # Fetch organization ID
    org_id = get_org_id(dashboard, logger_manager)

    # Run Report
    run_report(dashboard, org_id, product_type, logger_manager, EnvironmentManager.TIMESPAN_IN_SECONDS, EnvironmentManager.EXCEL, raw_data)

    logger_manager.console.print(Panel.fit("[bold bright_green]Script Complete.[/bold bright_green]"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        logger_manager.console.print(Panel.fit("Shutting down...", title="[bright_red]Script Exited[/bright_red]"))

