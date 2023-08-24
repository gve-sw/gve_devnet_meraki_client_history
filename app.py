"""
Copyright (c) 2022 Cisco and/or its affiliates.

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
    setup,
    get_env_variables,
    get_org_id_by_name,
    run_report_1,
    run_report_2,
    close_logger,
    RATE_LIMIT_PAUSE,
    MAX_RETRIES,
    TIMESPAN_IN_SECONDS,
    EXCEL_REPORT_1,
    EXCEL_REPORT_2
)

if __name__ == "__main__":
    # Set up logging
    logger = setup()

    # Fetch required environment variables
    API_KEY, ORGANIZATION_NAME = get_env_variables()

    # Initialize Meraki Dashboard API
    dashboard = meraki.DashboardAPI(API_KEY)

    # Fetch organization ID based on its name
    org_id = get_org_id_by_name(dashboard, ORGANIZATION_NAME, logger)

    # Run Reports
    run_report_1(dashboard, org_id, logger, RATE_LIMIT_PAUSE, MAX_RETRIES, TIMESPAN_IN_SECONDS, EXCEL_REPORT_1)
    run_report_2(dashboard, org_id, logger, RATE_LIMIT_PAUSE, MAX_RETRIES, TIMESPAN_IN_SECONDS, EXCEL_REPORT_2)

    # Logging script completion message
    logger.info("Script completed successfully!")

    # Close logger handlers
    close_logger(logger)
