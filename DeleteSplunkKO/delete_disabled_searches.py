#!/usr/bin/env python3

import sys
import os
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import argparse
import logging
import yaml
from pathlib import Path
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logger will be initialized in main() after loading config
logger = None

class SplunkSearchManager:
    def __init__(self, config):
        self.splunk_host = config['splunk']['host']
        self.port = config['splunk']['port']
        self.username = config['splunk']['username']
        self.password = config['splunk']['password']
        self.protocol = config['splunk']['protocol']
        self.verify_ssl = config['splunk']['verify_ssl']
        self.base_url = f"{self.protocol}://{self.splunk_host}:{self.port}/servicesNS/-/-"
        self.user_base_url = f"{self.protocol}://{self.splunk_host}:{self.port}/servicesNS/{self.username}/-"
        self.auth = HTTPBasicAuth(self.username, self.password)
        
    def get_saved_search(self, search_name):
        """Get details of a specific saved search"""
        encoded_name = quote(search_name, safe='')
        # Try different namespace combinations
        apps_to_try = ['search', 'system', '-']  # Common apps where searches might be stored
        
        for app in apps_to_try:
            for user in [self.username, 'nobody', '-']:
                url = f"{self.protocol}://{self.splunk_host}:{self.port}/servicesNS/{user}/{app}/saved/searches/{encoded_name}"
                try:
                    response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
                    if response.status_code == 200:
                        logger.debug(f"Found search '{search_name}' in namespace user='{user}', app='{app}'")
                        return response.text, url, user, app
                    elif response.status_code != 404:
                        logger.debug(f"Non-404 error for {url}: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Request error for {url}: {e}")
                    continue
        
        logger.warning(f"Saved search '{search_name}' not found in any namespace")
        return None, None, None, None
    
    def is_search_disabled(self, search_details):
        """Check if a saved search is disabled based on its details"""
        if search_details:
            # Parse the response to check if disabled=1
            return 'disabled">1<' in search_details or 'disabled">true<' in search_details
        return False
    
    def delete_saved_search(self, search_name, user, app):
        """Delete a saved search using specific user and app context"""
        encoded_name = quote(search_name, safe='')

        # For private searches or global namespace, try multiple combinations
        if user == '-' or app == '-':
            deletion_attempts = [
                (self.username, 'search'),   # Try current user with search app
                ('nobody', 'search'),        # Try nobody user with search app
                (self.username, 'system'),   # Try current user with system app
                ('nobody', 'system'),        # Try nobody user with system app
                (self.username, app if app != '-' else 'search'),  # Try current user with actual app
                ('nobody', app if app != '-' else 'search')        # Try nobody user with actual app
            ]
        else:
            deletion_attempts = [(user, app)]
        
        for del_user, del_app in deletion_attempts:
            url = f"{self.protocol}://{self.splunk_host}:{self.port}/servicesNS/{del_user}/{del_app}/saved/searches/{encoded_name}"
            logger.debug(f"Attempting deletion with user={del_user}, app={del_app}")
            
            try:
                response = requests.delete(url, auth=self.auth, verify=self.verify_ssl)
                if response.status_code == 200:
                    logger.info(f"Successfully deleted saved search: {search_name} (user={del_user}, app={del_app})")
                    return True
                else:
                    logger.debug(f"Delete attempt failed for user={del_user}, app={del_app}: HTTP {response.status_code}")
                    logger.debug(f"Response: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"Delete attempt error for user={del_user}, app={del_app}: {e}")
                continue
        
        logger.error(f"Failed to delete saved search '{search_name}' from any namespace")
        return False
    
    def test_connection(self):
        """Test connection to Splunk server"""
        url = f"{self.base_url}/apps/local"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl, timeout=10)
            if response.status_code == 200:
                logger.info("Successfully connected to Splunk server")
                return True
            else:
                logger.error(f"Failed to connect to Splunk: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def process_searches_from_file(self, file_path, dry_run=False):
        """Process saved searches from a text file"""
        # Test connection first
        if not self.test_connection():
            logger.error("Unable to connect to Splunk server. Please check your configuration.")
            return
        
        try:
            with open(file_path, 'r') as f:
                search_names = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return
        
        if not search_names:
            logger.warning("No saved search names found in the file")
            return
        
        logger.info(f"Found {len(search_names)} saved searches to process")
        
        deleted_count = 0
        skipped_count = 0
        not_found_count = 0
        error_count = 0
        
        for search_name in search_names:
            logger.info(f"Processing: {search_name}")
            
            # Check if search exists and is disabled
            search_details, search_url, user, app = self.get_saved_search(search_name)
            if search_details is None:
                not_found_count += 1
                continue
            
            if self.is_search_disabled(search_details):
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete disabled saved search: {search_name} (user={user}, app={app})")
                    deleted_count += 1
                else:
                    if self.delete_saved_search(search_name, user, app):
                        deleted_count += 1
                    else:
                        logger.error(f"Failed to delete: {search_name}")
                        error_count += 1
            else:
                logger.info(f"Skipping enabled saved search: {search_name} (user={user}, app={app})")
                skipped_count += 1
        
        logger.info(f"Summary: {deleted_count} deleted, {skipped_count} skipped (enabled), {not_found_count} not found, {error_count} errors")

def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        sys.exit(1)

def validate_config(config):
    """Validate configuration parameters"""
    required_keys = {
        'splunk': ['host', 'port', 'username', 'password', 'protocol'],
        'settings': ['log_level']
    }
    
    for section, keys in required_keys.items():
        if section not in config:
            logger.error(f"Missing section '{section}' in config file")
            return False
        for key in keys:
            if key not in config[section]:
                logger.error(f"Missing key '{key}' in section '{section}'")
                return False
    
    # Validate protocol
    if config['splunk']['protocol'].lower() not in ['http', 'https']:
        logger.error("Protocol must be 'http' or 'https'")
        return False
    
    # Validate log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    if config['settings']['log_level'].upper() not in valid_log_levels:
        logger.error(f"Invalid log level. Must be one of: {', '.join(valid_log_levels)}")
        return False
    
    return True

def setup_logging(log_level):
    """Setup logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Delete disabled Splunk saved searches from a text file')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path (default: config.yaml)')
    parser.add_argument('--file', required=True, help='Text file containing saved search names (one per line)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--host', help='Override Splunk host from config')
    parser.add_argument('--username', help='Override username from config')
    parser.add_argument('--password', help='Override password from config')
    parser.add_argument('--port', type=int, help='Override port from config')
    parser.add_argument('--protocol', choices=['http', 'https'], help='Override protocol from config')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Validate configuration
    if not validate_config(config):
        sys.exit(1)
    
    # Setup logging
    global logger
    logger = setup_logging(config['settings']['log_level'])
    
    # Override config with command line arguments if provided
    if args.host:
        config['splunk']['host'] = args.host
    if args.username:
        config['splunk']['username'] = args.username
    if args.password:
        config['splunk']['password'] = args.password
    if args.port:
        config['splunk']['port'] = args.port
    if args.protocol:
        config['splunk']['protocol'] = args.protocol
    
    # Override dry_run from config if command line argument is provided
    dry_run = args.dry_run or config['settings'].get('dry_run', False)
    
    logger.info(f"Connecting to {config['splunk']['protocol']}://{config['splunk']['host']}:{config['splunk']['port']}")
    logger.info(f"SSL verification: {'enabled' if config['splunk'].get('verify_ssl', False) else 'disabled'}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    manager = SplunkSearchManager(config)
    manager.process_searches_from_file(args.file, dry_run)

if __name__ == "__main__":
    main()
