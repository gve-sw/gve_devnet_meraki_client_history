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

from helper_functions import (
    LoggerManager,
    get_org_id_by_name,
    run_report_1,
    run_report_2,
    EnvironmentManager
)

if __name__ == "__main__":
    # Set up logging
    logger_manager = LoggerManager()

    # Fetch required environment variables
    EnvironmentManager.validate_env_variables()  # Validate environment variables at startup

    # Initialize Meraki Dashboard API
    dashboard = meraki.DashboardAPI(EnvironmentManager.MERAKI_API_KEY)

    # Fetch organization ID based on its name
    org_id = get_org_id_by_name(dashboard, EnvironmentManager.MERAKI_ORG_NAME, logger_manager)

    # Run Reports based on flags set in .env

    run_report_1(dashboard, org_id, logger_manager, EnvironmentManager.TIMESPAN_IN_SECONDS, EnvironmentManager.REPORT_ORG_WIDE, EnvironmentManager.EXCEL)
    run_report_2(dashboard, org_id, logger_manager, EnvironmentManager.TIMESPAN_IN_SECONDS, EnvironmentManager.REPORT_BY_NETWORK, EnvironmentManager.EXCEL)
