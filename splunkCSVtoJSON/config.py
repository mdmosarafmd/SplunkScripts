"""
Configuration settings for CSV to Splunk converter
"""

import os

# Splunk configuration
SPLUNK_HOST = os.getenv('SPLUNK_HOST', 'localhost')
SPLUNK_PORT = int(os.getenv('SPLUNK_PORT', '8088'))
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', 'b69e8871-8135-4ca4-a631-8a44ee7b1af9')
SPLUNK_INDEX = os.getenv('SPLUNK_INDEX', 'testdata')
SPLUNK_PROTOCOL = os.getenv('SPLUNK_PROTOCOL', 'http').lower()  # 'http' or 'https'

# Directory configuration
DATA_DIR = os.getenv('DATA_DIR', 'data')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'json_output')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')